import requests
from config import Config

URL = "https://api.vachana.ai/api/v1/tts/inference"

def synthesize_speech(text, language="te-IN"):
    api_key = Config.GNANI_TTS_API_KEY or Config.GNANI_API_KEY
    if not api_key:
        raise RuntimeError("Gnani TTS API key is missing. Add GNANI_API_KEY or GNANI_TTS_API_KEY to your .env file.")

    valid_langs = {"te-IN", "en-IN", "hi-IN"}
    selected_lang = language if language in valid_langs else "te-IN"

    payload = {
        "text": text,
        "voice": Config.TIMBRE_VOICE,
        "model": Config.TIMBRE_MODEL,
        "language": selected_lang,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 24000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav"
        }
    }

    headers = {
        "X-API-Key-ID": api_key,
        "Content-Type": "application/json"
    }

    response = requests.post(URL, headers=headers, json=payload, timeout=60)
    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text[:300]
        raise RuntimeError(f"Timbre API error ({response.status_code}): {detail}")

    if not response.content:
        raise RuntimeError("Timbre returned an empty audio response.")

    return response.content
