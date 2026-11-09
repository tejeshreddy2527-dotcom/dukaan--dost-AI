"""Receive audio uploads and convert them to the WAV format used by Prisma."""

import subprocess
from pathlib import Path
from uuid import uuid4

import imageio_ffmpeg
from werkzeug.datastructures import FileStorage

from gnani.prisma import transcribe_audio


class InvalidVoiceUpload(ValueError):
    """Raised when an audio upload is missing or cannot be decoded."""


def transcribe_voice_upload(
    audio: FileStorage,
    language_code: str = "indic-auto",
) -> tuple[str, str]:
    if not audio or not audio.filename:
        raise InvalidVoiceUpload("Please select or record an audio file first.")

    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    upload_id = uuid4().hex
    extension = Path(audio.filename).suffix.lower() or ".webm"
    source_path = upload_dir / f"{upload_id}-source{extension}"
    wav_path = upload_dir / f"{upload_id}-normalized.wav"

    try:
        audio.save(source_path)
        if source_path.stat().st_size == 0:
            raise InvalidVoiceUpload("The audio file is empty. Please select another file.")

        try:
            result = subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-nostdin",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(source_path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(wav_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise InvalidVoiceUpload("Audio conversion timed out. Try a shorter recording.") from exc

        if result.returncode != 0 or not wav_path.is_file():
            # Fallback: if ffmpeg conversion failed on browser webm/ogg container, try sending source_path directly to Prisma API
            try:
                return transcribe_audio(source_path, language_code=language_code)
            except Exception:
                detail = result.stderr.strip().splitlines()
                message = detail[-1] if detail else "Unsupported or invalid audio format."
                raise InvalidVoiceUpload(f"Could not read this audio file: {message}")

        return transcribe_audio(wav_path, language_code=language_code)
    finally:
        source_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)
