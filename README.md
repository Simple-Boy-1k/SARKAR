# 𝐃ᴇᴇᴘ 𝐄ᴍᴏᴛɪᴏɴs

Telegram + Gemini AI chatbot with long-term memory,
group conversation context, AI tools, voice support,
privacy controls and basic moderation.

## ✨ Features

- 🤖 Gemini AI conversations
- 🧠 Long-term personal memory
- 💬 Group conversation context
- 👋 Welcome and goodbye messages
- 🛡️ Basic anti-spam moderation
- 🛠️ AI tools
  - Rewrite
  - Summarize
  - Translate
  - Explain
  - Study Help
- 🎙️ Voice message transcription
- 🔒 Privacy and memory controls
- 📊 User statistics
- ⚡ Rate limiting
- 🌐 Render health server support

## 📁 Project Structure

```text
TelegramAIBot/
├── .env
├── .env.example
├── .gitignore
├── config.py
├── main.py
├── requirements.txt
├── README.md
├── data/
│   └── deep_emotions.db
├── bot/
│   ├── __init__.py
│   ├── ai.py
│   ├── database.py
│   └── handlers.py
└── .venv/

## 🚀 Deploy to Heroku

This repository includes a `Procfile` and `app.json` for Heroku.

1. Push the project to a GitHub repository.
2. In Heroku, create a new app and deploy the repository from the **Deploy** tab, or use the Heroku Deploy button if you add one to your repository README.
3. In **Settings → Config Vars**, set:
   - `BOT_TOKEN` — token from Telegram `@BotFather`
   - `GEMINI_API_KEY` — key from Google AI Studio
   - `OWNER_ID` — your numeric Telegram user ID (optional; defaults to `0`)
   - `GEMINI_MODEL` — defaults to `gemini-2.5-flash`
4. In **Resources**, enable one `web` dyno, then check **More → View logs**.

The bot uses SQLite at `data/deep_emotions.db`. Heroku's local filesystem is ephemeral, so the database and saved memories can be lost when the dyno restarts or is redeployed. Use a persistent external database or a suitable persistent storage service if you need memories to survive restarts.

## Optional environment variables (Heroku Config Vars / hosting Variables)

- `OWNER_ID` — numeric Telegram user ID allowed to see/use the Owner Panel.
- `SUPPORT_CHAT_URL` — support chat/bot link; its button appears when set.
- `SUPPORT_CHANNEL_URL` — support channel link; its button appears when set.
- `UPDATES_CHANNEL_URL` — updates channel link.
- `START_IMAGE_URL` — direct image URL used for `/start`; the repository welcome image is the default.
- `OUR_BOTS_URL` — optional link to your other bots.
- `OWNER_USERNAME` — optional username without `@`; leave blank to hide the owner line.

Set the variable values in your hosting dashboard, then restart/redeploy the bot. Empty optional links hide their respective buttons.

