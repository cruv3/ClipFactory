import os
from dotenv import load_dotenv

load_dotenv()

TEST_RUN = os.getenv("TEST_RUN", "False").lower() == "true"
# Base Paths
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_DIR = os.path.join(BASE_PATH, "secrets")
DATA_DIR = os.path.join(BASE_PATH, "data")
VIDEO_CHUNKS_DIR = os.path.join(DATA_DIR, "video_chunks")

for directory in [SECRETS_DIR, DATA_DIR, VIDEO_CHUNKS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

# Persistent Logs (The "Memory" of your factory)
USED_POSTS_LOG = os.path.join(DATA_DIR, "used_posts.txt")
VIDEO_HISTORY_JSON = os.path.join(DATA_DIR, "video_history.json")
STRATEGY_LOG = os.path.join(DATA_DIR, "ai_strategy.txt")

# Telegram & Ollama & Kokoro
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LLM_MODEL = os.getenv("LLM_MODEL")
AI_SERVICE_IP = os.getenv("AI_SERVICE_IP", "192.168.2.124:8800")
AI_BASE_URL = f"http://{AI_SERVICE_IP}"
API_GENERATE_SCRIPT = f"{AI_BASE_URL}/generate_script"
API_GENERATE_VOICE  = f"{AI_BASE_URL}/generate_voice"
API_GENERATE_VIDEO  = f"{AI_BASE_URL}/generate_video"
API_VRAM_CLEANUP    = f"{AI_BASE_URL}/cleanup"
API_HEALTH_CHECK    = f"{AI_BASE_URL}/health"

WORD_MIN = int(os.getenv("WORD_MIN", 150))
WORD_MAX = int(os.getenv("WORD_MAX", 250))

KOKORO_URL = os.getenv("KOKORO_URL", "http://192.168.2.124:8880/v1/audio/speech")
KOKORO_URL_WEB = KOKORO_URL.replace("/v1/audio/speech", "/web/")

# Intervals
VIDEO_INTERVAL_HOURS = int(os.getenv("VIDEO_INTERVAL", 6))
CLEAN_INTERVAL_HOURS = int(os.getenv("CLEANUP_INTERVAL", 48))
REPORT_INTERVAL_HOURS = int(os.getenv("REPORT_INTERVAL_HOURS", 168))

# Instagram
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_SETTINGS_FILE = os.path.join(SECRETS_DIR, "ig_settings.json")

# TikTok
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME")
TIKTOK_COOKIES = os.path.join(SECRETS_DIR, "cookies-tiktok-com.txt")
TIKTOK_SESSION_ID = os.getenv("TIKTOK_SESSION_ID")

# YouTube
YOUTUBE_CLIENT_SECRETS = os.path.join(SECRETS_DIR, "client_secrets.json")
YOUTUBE_TOKEN_PICKLE = os.path.join(SECRETS_DIR, "youtube_token.pickle")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Fonts
FONT_PATH = os.path.join(BASE_PATH, "fonts", "SourGummy_SemiExpanded-ExtraBoldItalic.ttf").replace("\\", "/")

# --- Video AI / RTX XX90 Configuration ---
USE_RTX_XX90 = os.getenv("USE_RTX_XX90", "False").lower() == "true"
AI_GENERATED_DIR = os.path.join(DATA_DIR, "ai_generated")
for directory in [SECRETS_DIR, DATA_DIR, VIDEO_CHUNKS_DIR, AI_GENERATED_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)