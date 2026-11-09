import io
import os
import tempfile
import pytest

@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    import config
    config.Config.DATABASE_PATH = str(tmp_path / "test.db")
    import database.db as db
    db.init_db()
    from app import app as flask_app
    flask_app.config.update(TESTING=True)
    yield flask_app

@pytest.fixture()
def client(app):
    return app.test_client()

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["application"] == "Dukaan Dost AI"

def test_dashboard_loads(client):
    assert client.get("/").status_code == 200

def test_check_stock(client):
    response = client.post("/api/command", json={"text":"How much rice is available?"})
    assert response.status_code == 200
    assert "Rice" in response.json["reply"]

def test_stock_add_requires_confirmation_then_updates(client):
    preview = client.post("/api/command", json={"text":"Add 5 kg rice"})
    assert preview.json["requires_confirmation"] is True
    result = client.post("/api/command", json={"text":"Add 5 kg rice","confirmed":True})
    assert result.status_code == 200
    assert "30 kg" in result.json["reply"]

def test_sale_updates_stock_and_report(client):
    result = client.post("/api/command", json={"text":"Sell 2 soap","confirmed":True})
    assert result.status_code == 200
    assert "Sale recorded" in result.json["reply"]
    report = client.post("/api/command", json={"text":"Show today's sales"})
    assert report.status_code == 200
    assert "₹" in report.json["reply"]

def test_unknown_product_does_not_crash(client):
    response = client.post("/api/command", json={"text":"Add 2 kg almonds","confirmed":True})
    assert response.status_code == 400

def test_voice_endpoint_transcribes_uploaded_audio(client, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module.Config, "GNANI_STT_API_KEY", "test-key")
    monkeypatch.setattr(
        app_module,
        "transcribe_voice_upload",
        lambda audio, language_code: ("Show today's sales", "en-IN"),
    )
    monkeypatch.setattr(
        app_module,
        "process_command",
        lambda *args, **kwargs: {"success": False, "reply": "No sales yet."},
    )

    response = client.post(
        "/api/voice",
        data={"audio": (io.BytesIO(b"audio bytes"), "question.webm")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.json["transcript"] == "Show today's sales"

def test_upload_page_accepts_browser_recording_format(client, monkeypatch):
    import app as app_module

    monkeypatch.setattr(
        app_module,
        "transcribe_voice_upload",
        lambda audio, language_code="indic-auto": ("Add 3 kg rice", "en-IN"),
    )
    monkeypatch.setattr(
        app_module,
        "process_command",
        lambda *args, **kwargs: {},
    )

    response = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"browser recording"), "recording.webm")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert "Add 3 kg rice" in response.json["raw_text"]
