import os
from dotenv import load_dotenv

load_dotenv()

TEST_RUN = os.getenv("TEST_RUN", "False").lower() == "true"

# Base Paths
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_DIR = os.path.join(BASE_PATH, "secrets")
DATA_DIR = os.path.join(BASE_PATH, "data")
VIDEO_CHUNKS_DIR = os.path.join(DATA_DIR, "video_chunks")
AI_GENERATED_DIR = os.path.join(DATA_DIR, "ai_generated")

for directory in [SECRETS_DIR, DATA_DIR, VIDEO_CHUNKS_DIR, AI_GENERATED_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

# Persistent Logs (The "Memory" of your factory)
USED_POSTS_LOG = os.path.join(DATA_DIR, "used_posts.txt")
VIDEO_HISTORY_JSON = os.path.join(DATA_DIR, "video_history.json")
STRATEGY_LOG = os.path.join(DATA_DIR, "ai_strategy.txt")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Hardware & IP Config
USE_RTX_XX90 = True
AI_SERVICE_IP = os.getenv("AI_SERVICE_IP", "192.168.2.124")

# ==========================================
# 1. LLM Service (OLLAMA) -> Port 8801
# ==========================================
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:14b") # Oder 'qwen2.5:32b'
LLM_BASE_URL = f"http://{AI_SERVICE_IP}:8801"
API_GENERATE_SCRIPT = f"{LLM_BASE_URL}/api/generate" # Offizielle Ollama API
# Hinweis: Ollama hat keinen /cleanup Endpunkt. 
# VRAM-Release passiert durch den Parameter "keep_alive": 0 im Request!

# ==========================================
# 2. Voice Service (TTS - Kokoro FastAPI) -> Port 8802
# ==========================================
VOICE_BASE_URL = f"http://{AI_SERVICE_IP}:8802"
API_GENERATE_VOICE  = f"{VOICE_BASE_URL}/v1/audio/speech" 
API_VOICE_HEALTH    = f"{VOICE_BASE_URL}/v1/models"

# ==========================================
# 3. Video Service (LTX-2) -> Port 8803
# ==========================================
VIDEO_BASE_URL = f"http://{AI_SERVICE_IP}:8803"
API_GENERATE_VIDEO  = f"{VIDEO_BASE_URL}/generate_video"
API_VIDEO_HEALTH    = f"{VIDEO_BASE_URL}/health"
API_VIDEO_CLEANUP   = f"{VIDEO_BASE_URL}/cleanup"

# Text Limits
WORD_MIN = int(os.getenv("WORD_MIN", 150))
WORD_MAX = int(os.getenv("WORD_MAX", 250))

# Intervals
VIDEO_INTERVAL_HOURS = int(os.getenv("VIDEO_INTERVAL", 6))
CLEAN_INTERVAL_HOURS = int(os.getenv("CLEANUP_INTERVAL", 48))
REPORT_INTERVAL_HOURS = int(os.getenv("REPORT_INTERVAL_HOURS", 168))

# Social Media Credentials
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_SETTINGS_FILE = os.path.join(SECRETS_DIR, "ig_settings.json")

TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME")
TIKTOK_COOKIES = os.path.join(SECRETS_DIR, "cookies-tiktok-com.txt")
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID")

YOUTUBE_CLIENT_SECRETS = os.path.join(SECRETS_DIR, "client_secrets.json")
YOUTUBE_TOKEN_PICKLE = os.path.join(SECRETS_DIR, "youtube_token.pickle")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Assets
FONT_PATH = os.path.join(BASE_PATH, "fonts", "SourGummy_SemiExpanded-ExtraBoldItalic.ttf").replace("\\", "/")