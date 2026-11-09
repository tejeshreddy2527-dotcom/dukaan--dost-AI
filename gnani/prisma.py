import requests
from config import Config

URL = "https://api.vachana.ai/stt/v3"

def transcribe_audio(path, language_code="indic-auto"):
    api_key = Config.GNANI_STT_API_KEY or Config.GNANI_API_KEY
    if not api_key:
        raise RuntimeError("Gnani STT API key is missing. Add GNANI_API_KEY or GNANI_STT_API_KEY to your .env file.")

    headers = {"X-API-Key-ID": api_key}
    data = {
        "model": Config.PRISMA_MODEL,
        "language_code": language_code if language_code != "indic-auto" else "te-IN,en-IN,hi-IN",
        "format": "codemix"
    }

    with open(path, "rb") as audio:
        # Gnani Prisma REST expects audio_file or audio
        response = requests.post(
            URL,
            headers=headers,
            data=data,
            files={"audio_file": (path.name, audio, "audio/wav")},
            timeout=60
        )

    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:300]
        raise RuntimeError(f"Prisma API error ({response.status_code}): {detail}")

    payload = response.json()
    transcript = payload.get("transcript", "")
    if isinstance(transcript, dict):
        transcript = transcript.get("text", "")

    detected_lang = payload.get("detected_language_code") or payload.get("language_code") or "te-IN"
    return str(transcript).strip(), detected_lang
