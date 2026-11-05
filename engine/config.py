import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HOST = os.getenv("HOST", "127.0.0.1")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))
WS_PORT = int(os.getenv("WS_PORT", "8765"))

MODEL_NAME = os.getenv("MODEL_NAME", "Kaguya")
MODEL_PATH = os.getenv("MODEL_PATH", f"/assets/models/{MODEL_NAME}/{MODEL_NAME}.model3.json")
LIP_SYNC_SENSITIVITY = float(os.getenv("LIP_SYNC_SENSITIVITY", "1.2"))
PROACTIVE_IDLE_SECONDS = int(os.getenv("PROACTIVE_IDLE_SECONDS", "45"))

ASSETS_DIR = BASE_DIR / "assets"
CLIENT_UI_DIR = BASE_DIR / "client_ui"
FRONTEND_DIR = CLIENT_UI_DIR if CLIENT_UI_DIR.exists() else (BASE_DIR / "frontend")

