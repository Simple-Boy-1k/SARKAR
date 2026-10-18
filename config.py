import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "").strip()
SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL", "").strip()
SUPPORT_CHANNEL_URL = os.getenv("SUPPORT_CHANNEL_URL", "").strip()
UPDATES_CHANNEL_URL = os.getenv("UPDATES_CHANNEL_URL", "").strip()
START_IMAGE_URL = os.getenv("START_IMAGE_URL", "https://raw.githubusercontent.com/AashishTechs/Deep-Emotion/main/Welcome.jpg?v=2").strip()
OUR_BOTS_URL = os.getenv("OUR_BOTS_URL", "").strip()
