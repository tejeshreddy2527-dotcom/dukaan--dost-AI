import os
from pathlib import Path
from uuid import uuid4
from flask import Flask, render_template, jsonify, request, send_from_directory
from dotenv import load_dotenv

from config import Config
from database.db import init_db, get_dashboard_data, get_analytics_data
from modules.inventory import list_products, create_product, update_product, delete_product
from modules.sales import list_sales, today_summary
from modules.data_ingestion import (
    extract_from_csv, extract_from_excel, extract_from_pdf,
    extract_from_image, save_confirmed_items
)
from inputs.voice_input import InvalidVoiceUpload, transcribe_voice_upload
from agent.orchestrator import process_command
from gnani.timbre import synthesize_speech
from werkzeug.datastructures import FileStorage

load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25MB max upload

Path("uploads").mkdir(exist_ok=True)
Path("instance").mkdir(exist_ok=True)
init_db()

GREETINGS = {
    "te-IN": "నమస్కారం! నేను మీ దుకాన్ దోస్త్ AI. మీ షాప్ అమ్మకాలు, స్టాక్, ఆదాయం గురించి అడగండి. మీకు ఎలా సహాయం చేయాలి?",
    "en-IN": "Hello! I'm Dukaan Dost AI. Ask me about today's sales, revenue, inventory, or anything about your shop.",
    "hi-IN": "नमस्ते! मैं हूँ दुकान दोस्त AI। आज की बिक्री, स्टॉक और कमाई के बारे में मुझसे पूछें। मैं आपकी क्या मदद करूँ?"
}

# -------------------------------------------------------------
# PAGE ROUTES
# -------------------------------------------------------------

@app.get("/")
def home():
    """Page 1: Premium 3D Cinematic Landing Page & Voice Assistant"""
    return render_template("landing.html")

@app.get("/dashboard")
def dashboard_page():
    """Page 2: Business Command Center Dashboard"""
    return render_template("dashboard.html")

@app.get("/inventory")
def inventory_page():
    """Page 3: Product Catalogue & Stock Management"""
    return render_template("inventory.html")

@app.get("/sales")
def sales_page():
    """Page 4: Sales History & Detailed Transactions"""
    return render_template("sales.html")

@app.get("/assistant")
def assistant_page():
    """Page 5: Full-screen Interactive AI Voice Assistant"""
    return render_template("assistant.html")

@app.get("/upload")
def upload_page():
    """Page 6: Multi-format Document & Data Ingestion"""
    return render_template("upload.html")

# -------------------------------------------------------------
# CORE API ENDPOINTS
# -------------------------------------------------------------

@app.get("/health")
def health():
    gnani_ok = bool(Config.GNANI_API_KEY or Config.GNANI_STT_API_KEY)
    return jsonify(
        status="success",
        application="Dukaan Dost AI",
        message="Server is running",
        gnani_configured=gnani_ok,
        database="SQLite (Initialized)",
        models={"prisma": Config.PRISMA_MODEL, "timbre": Config.TIMBRE_MODEL}
    )

@app.get("/api/dashboard")
def dashboard_api():
    return jsonify(get_dashboard_data())

@app.get("/api/analytics")
def analytics_api():
    return jsonify(get_analytics_data())

@app.get("/api/products")
def products_api():
    return jsonify(products=list_products())

@app.post("/api/products")
def add_product_api():
    data = request.get_json(silent=True) or {}
    try:
        product = create_product(
            name=data.get("name", ""),
            quantity=data.get("quantity", 0),
            unit=data.get("unit", "pcs"),
            price=data.get("price", 0),
            low_stock_threshold=data.get("low_stock_threshold", 5),
            category=data.get("category", "General"),
            cost_price=data.get("cost_price", 0)
        )
        return jsonify(success=True, product=product, message=f"{product['name']} added to your catalogue.")
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400

@app.put("/api/products/<int:pid>")
def update_product_api(pid):
    data = request.get_json(silent=True) or {}
    try:
        updated = update_product(
            product_id=pid,
            name=data.get("name"),
            category=data.get("category", "General"),
            quantity=data.get("quantity", 0),
            unit=data.get("unit", "pcs"),
            price=data.get("price", 0),
            cost_price=data.get("cost_price", 0),
            low_stock_threshold=data.get("low_stock_threshold", 5)
        )
        if not updated:
            return jsonify(success=False, error="Product not found"), 404
        return jsonify(success=True, product=updated, message=f"{updated['name']} updated successfully.")
    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 400

@app.delete("/api/products/<int:pid>")
def delete_product_api(pid):
    try:
        delete_product(pid)
        return jsonify(success=True, message="Product deleted successfully.")
    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 400

@app.get("/api/sales")
def sales_api():
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    product_name = request.args.get("product")
    res = list_sales(limit=limit, offset=offset, start_date=start_date, end_date=end_date, product_name=product_name)
    today = today_summary()
    return jsonify(success=True, **res, today_summary=today)

@app.post("/api/command")
def command_api():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    confirmed = bool(data.get("confirmed"))
    lang = data.get("language")
    result = process_command(text, confirmed=confirmed, preferred_lang=lang)

    # Optional auto-speech generation if requested
    auto_speak = bool(data.get("speak"))
    if auto_speak and result.get("success") and result.get("reply"):
        speech_lang = result.get("language") or lang or "te-IN"
        if Config.GNANI_TTS_API_KEY or Config.GNANI_API_KEY:
            try:
                audio_bytes = synthesize_speech(result["reply"], language=speech_lang)
                filename = f"{uuid4().hex}.wav"
                (Path("uploads") / filename).write_bytes(audio_bytes)
                result["audio_url"] = f"/audio/{filename}"
            except Exception as e:
                app.logger.warning(f"Voice synthesis for command skipped: {e}")
                result["audio_url"] = None

    return jsonify(result), (200 if result.get("success") else 400)

@app.get("/api/greeting")
def greeting_api():
    lang = request.args.get("language", "te-IN")
    if lang not in GREETINGS:
        lang = "te-IN"
    text = GREETINGS[lang]
    audio_url = None

    # Synthesize with Gnani Timbre if configured
    if Config.GNANI_TTS_API_KEY or Config.GNANI_API_KEY:
        try:
            audio_bytes = synthesize_speech(text, language=lang)
            filename = f"greeting_{lang.replace('-', '_')}_{uuid4().hex[:8]}.wav"
            (Path("uploads") / filename).write_bytes(audio_bytes)
            audio_url = f"/audio/{filename}"
        except Exception as exc:
            app.logger.warning(f"Greeting synthesis through Timbre skipped: {exc}")

    return jsonify(
        success=True,
        language=lang,
        greeting_text=text,
        audio_url=audio_url,
        gnani_speech=bool(audio_url)
    )

@app.post("/api/voice")
def voice_api():
    api_key = Config.GNANI_STT_API_KEY or Config.GNANI_API_KEY
    if not api_key:
        return jsonify(
            success=False,
            error="Add GNANI_API_KEY or GNANI_STT_API_KEY to your .env file to enable Gnani Prisma STT."
        ), 503

    audio = request.files.get("audio")
    if not audio or not audio.filename:
        return jsonify(success=False, error="Please select or record an audio file first."), 400

    try:
        lang_hint = request.form.get("language", "indic-auto")
        transcript, detected = transcribe_voice_upload(audio, language_code=lang_hint)
        if not transcript.strip():
            return jsonify(
                success=False,
                error="No clear words detected in audio. Please speak closer to the mic.",
                transcript=""
            )

        # Run intent processor automatically on transcribed command!
        cmd_result = process_command(transcript, confirmed=False, preferred_lang=detected)

        # Synthesize reply via Gnani Timbre
        speech_url = None
        if cmd_result.get("success") and cmd_result.get("reply"):
            try:
                audio_bytes = synthesize_speech(cmd_result["reply"], language=detected)
                speech_filename = f"{uuid4().hex}.wav"
                (Path("uploads") / speech_filename).write_bytes(audio_bytes)
                speech_url = f"/audio/{speech_filename}"
            except Exception as e:
                app.logger.warning(f"Timbre synthesis failed for voice command: {e}")

        return jsonify(
            success=True,
            transcript=transcript,
            detected_language=detected,
            command_result=cmd_result,
            audio_url=speech_url
        )
    except InvalidVoiceUpload as exc:
        return jsonify(success=False, error=str(exc)), 400
    except Exception as exc:
        app.logger.exception("Prisma transcription failed")
        return jsonify(success=False, error=str(exc)), 502

@app.post("/api/speak")
def speak_api():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    language = str(data.get("language", "te-IN"))
    if not text:
        return jsonify(success=False, error="No text to speak."), 400

    api_key = Config.GNANI_TTS_API_KEY or Config.GNANI_API_KEY
    if not api_key:
        return jsonify(
            success=False,
            error="Add GNANI_API_KEY or GNANI_TTS_API_KEY to your .env file to enable Gnani Timbre TTS."
        ), 503

    try:
        audio_bytes = synthesize_speech(text, language=language)
        filename = f"{uuid4().hex}.wav"
        (Path("uploads") / filename).write_bytes(audio_bytes)
        return jsonify(success=True, audio_url=f"/audio/{filename}")
    except Exception as exc:
        app.logger.exception("Timbre synthesis failed")
        return jsonify(success=False, error=str(exc)), 502

@app.post("/api/upload")
def upload_document_api():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify(success=False, error="Please select a file to upload."), 400

    filename = uploaded.filename
    ext = Path(filename).suffix.lower()
    audio_extensions = {
        ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus",
        ".webm", ".wma", ".aiff", ".aif", ".3gp", ".amr", ".mp4",
    }
    allowed = {".csv", ".xlsx", ".xls", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
    if ext not in allowed and ext not in audio_extensions:
        return jsonify(
            success=False,
            error=f"Unsupported format {ext}. Upload CSV, Excel, PDF, Image, or an audio file supported by FFmpeg."
        ), 400

    temp_name = f"upload_{uuid4().hex[:8]}_{filename}"
    temp_path = Path("uploads") / temp_name
    uploaded.save(temp_path)

    try:
        extracted_items = []
        raw_text = ""
        category_detected = "General"

        if ext == ".csv":
            extracted_items = extract_from_csv(temp_path.read_bytes())
        elif ext in {".xlsx", ".xls"}:
            extracted_items = extract_from_excel(temp_path)
        elif ext == ".pdf":
            extracted_items, raw_text = extract_from_pdf(temp_path)
        elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
            extracted_items, raw_text = extract_from_image(temp_path)
        elif ext in audio_extensions:
            with temp_path.open("rb") as audio_stream:
                transcript, detected = transcribe_voice_upload(
                    FileStorage(stream=audio_stream, filename=filename)
                )
            raw_text = f"Voice Recording Transcription ({detected}):\n{transcript}"
            # Run intent or extract lines
            extracted_items = []
            parsed = process_command(transcript)
            if parsed.get("pending"):
                p = parsed["pending"]
                extracted_items.append({
                    "name": p["product"],
                    "category": "General",
                    "quantity": p["quantity"],
                    "unit": "pcs",
                    "price": 50.0,
                    "cost_price": 40.0,
                    "low_stock_threshold": 5.0
                })

        return jsonify(
            success=True,
            filename=filename,
            file_type=ext.lstrip(".").upper(),
            item_count=len(extracted_items),
            items=extracted_items,
            raw_text=raw_text[:2000] if raw_text else None,
            message=f"Extracted {len(extracted_items)} items. Please review and confirm before saving."
        )
    except InvalidVoiceUpload as exc:
        return jsonify(success=False, error=str(exc)), 400
    except Exception as exc:
        app.logger.exception(f"Upload processing failed for {filename}")
        return jsonify(success=False, error=str(exc)), 500
    finally:
        temp_path.unlink(missing_ok=True)

@app.post("/api/upload/confirm")
def confirm_upload_api():
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    if not items or not isinstance(items, list):
        return jsonify(success=False, error="No valid items provided to confirm."), 400

    try:
        saved_count = save_confirmed_items(items)
        return jsonify(
            success=True,
            saved_count=saved_count,
            message=f"Successfully imported and updated {saved_count} products in your inventory."
        )
    except Exception as exc:
        app.logger.exception("Failed to save confirmed items")
        return jsonify(success=False, error=str(exc)), 500

@app.get("/audio/<path:filename>")
def audio_file(filename):
    return send_from_directory("uploads", filename, mimetype="audio/wav", as_attachment=False)

@app.errorhandler(413)
def too_large(_error):
    return jsonify(success=False, error="File is too large. Maximum upload size is 25 MB."), 413

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
