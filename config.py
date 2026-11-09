import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "local-development-key-change-before-deploy")
    GNANI_API_KEY = os.getenv("GNANI_API_KEY", "").strip()
    GNANI_STT_API_KEY = os.getenv("GNANI_STT_API_KEY", "").strip() or os.getenv("GNANI_API_KEY", "").strip()
    GNANI_TTS_API_KEY = os.getenv("GNANI_TTS_API_KEY", "").strip() or os.getenv("GNANI_API_KEY", "").strip()
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "te-IN")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "instance/dukaan_dost.db")
    PRISMA_MODEL = os.getenv("PRISMA_MODEL", "prisma-v3.0")
    TIMBRE_MODEL = os.getenv("TIMBRE_MODEL", "timbre-v2.5")
    TIMBRE_VOICE = os.getenv("TIMBRE_VOICE", "Kaveri")
