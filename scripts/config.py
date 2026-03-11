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

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_PULL_URL = f"{OLLAMA_BASE_URL}/api/pull"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE_URL}/api/tags"

KOKORO_URL = os.getenv("KOKORO_URL", "http://192.168.2.124:8880/v1/audio/speech")
KOKORO_URL_WEB = KOKORO_URL.replace("/v1/audio/speech", "/web/")

# Intervals
VIDEO_INTERVAL_HOURS = int(os.getenv("VIDEO_INTERVAL", 6))
CLEAN_INTERVAL_HOURS = int(os.getenv("CLEANUP_INTERVAL", 48))

# Instagram
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

# TikTok
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME")
TIKTOK_COOKIES = os.path.join(SECRETS_DIR, "cookies-tiktok-com.txt")

# YouTube
YOUTUBE_CLIENT_SECRETS = os.path.join(SECRETS_DIR, "client_secrets.json")
YOUTUBE_TOKEN_PICKLE = os.path.join(SECRETS_DIR, "youtube_token.pickle")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]