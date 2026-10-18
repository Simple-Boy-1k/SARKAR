# ==========================================================
# DEEP EMOTIONS — CONFIGURATION
# ==========================================================

import os

from dotenv import load_dotenv


# ==========================================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================================

load_dotenv()


# ==========================================================
# TELEGRAM BOT
# ==========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "",
).strip()


# ==========================================================
# GEMINI AI
# ==========================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
).strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
).strip()


# ==========================================================
# OWNER
# ==========================================================

try:

    OWNER_ID = int(
        os.getenv(
            "OWNER_ID",
            "8885285219",
        )
        or 0
    )

except ValueError:

    OWNER_ID = 0



# ==========================================================
# OPTIONAL LINKS / START IMAGE (set these in hosting Variables)
# ==========================================================

SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL", "").strip()
SUPPORT_CHANNEL_URL = os.getenv("SUPPORT_CHANNEL_URL", "").strip()
UPDATES_CHANNEL_URL = os.getenv("UPDATES_CHANNEL_URL", "https://t.me/deep_emotions_01").strip()
START_IMAGE_URL = os.getenv("START_IMAGE_URL", "https://raw.githubusercontent.com/AashishTechs/Deep-Emotion/main/Welcome.jpg?v=2").strip()
OUR_BOTS_URL = os.getenv("OUR_BOTS_URL", "").strip()
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "").strip().lstrip("@")

# ==========================================================
# VALIDATION
# ==========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN missing. "
        "Put BOT_TOKEN in your .env file."
    )


if not GEMINI_API_KEY:

    raise RuntimeError(
        "GEMINI_API_KEY missing. "
        "Put GEMINI_API_KEY in your .env file."
    )


# ==========================================================
# CONFIG SUMMARY
# ==========================================================

print(
    f"Deep Emotions config loaded | "
    f"Model: {GEMINI_MODEL}"
)