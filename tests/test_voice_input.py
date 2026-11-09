import io
import wave

import pytest
from werkzeug.datastructures import FileStorage

from inputs import voice_input


def make_wav() -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\x00\x00" * 1600)
    return output.getvalue()


def test_transcribe_voice_upload_converts_audio_to_wav(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen = {}

    def fake_transcribe(path, language_code):
        seen["path"] = path
        seen["language_code"] = language_code
        with wave.open(str(path), "rb") as converted:
            seen["format"] = (
                converted.getnchannels(),
                converted.getframerate(),
                converted.getsampwidth(),
            )
        return "hello", "en-IN"

    monkeypatch.setattr(voice_input, "transcribe_audio", fake_transcribe)
    upload = FileStorage(stream=io.BytesIO(make_wav()), filename="question.wav")

    transcript, language = voice_input.transcribe_voice_upload(upload, "en-IN")

    assert (transcript, language) == ("hello", "en-IN")
    assert seen["language_code"] == "en-IN"
    assert seen["format"] == (1, 16000, 2)
    assert not list((tmp_path / "uploads").iterdir())


def test_transcribe_voice_upload_rejects_non_audio(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    upload = FileStorage(stream=io.BytesIO(b"not audio"), filename="question.txt")

    with pytest.raises(voice_input.InvalidVoiceUpload, match="Could not read"):
        voice_input.transcribe_voice_upload(upload)

    assert not list((tmp_path / "uploads").iterdir())
