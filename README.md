# 🤖 Gemini Telegram AI Bot

A feature-rich, high-performance Telegram Bot powered by Google Gemini AI with custom-styled inline buttons and automated Heroku deployment setup.

---

## 🚀 Deploy to Heroku

Aap neeche diye gaye button par click karke is bot ko direct **Heroku** par deploy kar sakte hain. Deploy karte waqt aapko saare configuration boxes (`BOT_TOKEN`, `GEMINI_API_KEY`, etc.) fill karne ka option mil jayega:

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/yourusername/gemini-telegram-bot)

> ⚠️ **Note:** GitHub par upload karne ke baad, upar diye gaye link mein `yourusername/gemini-telegram-bot` ko apni GitHub username aur repository name se replace kar lena.

---

## ⚙️ Environment Variables (Config Boxes)

Jab aap Heroku par deploy karoge, toh yeh saare inputs aapko screen par dikhenge:

| Variable Name | Required | Description |
|---|---|---|
| `BOT_TOKEN` | Yes | Telegram Bot Token from [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | Yes | Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/) |
| `OWNER_ID` | No | Your Telegram User ID (Numeric format) |
| `OWNER_USERNAME` | No | Your Telegram handle (without `@`) |
| `SUPPORT_CHAT_URL` | No | Link to your support group |
| `SUPPORT_CHANNEL_URL` | No | Link to your support channel |
| `UPDATES_CHANNEL_URL` | No | Link to your updates channel |
| `START_IMAGE_URL` | No | Banner/Welcome Image URL |
| `OUR_BOTS_URL` | No | Link showcasing your other projects |

---

## 🛠️ Local Installation

Agar aap local machine par run karna chahte hain:

1. Repository clone karein:
   ```bash
   git clone [https://github.com/yourusername/gemini-telegram-bot.git](https://github.com/yourusername/gemini-telegram-bot.git)
   cd gemini-telegram-bot
