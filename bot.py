import os
import html
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from google import genai

from config import (
    BOT_TOKEN, GEMINI_API_KEY, OWNER_ID, OWNER_USERNAME,
    SUPPORT_CHAT_URL, SUPPORT_CHANNEL_URL, UPDATES_CHANNEL_URL,
    START_IMAGE_URL, OUR_BOTS_URL
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Gemini Client Initialization
if not GEMINI_API_KEY:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY is missing or empty!")

ai_client = genai.Client(api_key=GEMINI_API_KEY)


def _btn(text, *, callback_data=None, url=None, style=None):
    kwargs = {}
    if style:
        kwargs["style"] = style
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url, **kwargs)


def _welcome_caption(bot_name):
    safe_name = html.escape(bot_name or "Gemini AI")
    return (
        f"✨ ʜɪ ʜᴇʟʟᴏ, ɪ'ᴍ <b>{safe_name}</b> 🤖\n\n"
        "Your advanced AI assistant powered by Google Gemini. 🌸\n\n"
        "💬 Natural Chat • 🧠 Smart Responses • ⚡ Fast Replies\n\n"
        "Choose an option below and let's get started. 👇"
    )


def main_menu_keyboard(bot_username="bot", is_owner=False):
    username = (bot_username or "bot").lstrip("@")
    rows = [
        [_btn("💬 ᴄʜᴀᴛ ᴡɪᴛʜ ᴍᴇ", callback_data="chat", style="danger")],
        [_btn("💗 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_main", style="danger")],
    ]
    links = []
    if UPDATES_CHANNEL_URL:
        links.append(_btn("🔔 ᴜᴘᴅᴀᴛᴇs", url=UPDATES_CHANNEL_URL, style="success"))
    if SUPPORT_CHANNEL_URL:
        links.append(_btn("📢 ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=SUPPORT_CHANNEL_URL, style="success"))
    if links:
        rows.append(links)
    if SUPPORT_CHAT_URL:
        rows.append([_btn("🛠️ ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ", url=SUPPORT_CHAT_URL, style="success")])
    if OUR_BOTS_URL:
        rows.append([_btn("🤖 ᴏᴜʀ ʙᴏᴛs", url=OUR_BOTS_URL, style="primary")])
    
    owner_un = (OWNER_USERNAME or "").strip().lstrip("@")
    if owner_un:
        rows.append([_btn("👑 ᴏᴡɴᴇʀ", url=f"https://t.me/{owner_un}", style="primary")])
    
    rows.append([_btn("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url=f"https://t.me/{username}?startgroup=true", style="primary")])
    
    if is_owner:
        rows.append([_btn("👑 ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", callback_data="owner_panel", style="danger")])
    
    return InlineKeyboardMarkup(rows)


# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    me = await context.bot.get_me()
    bot_username = me.username or "bot"
    bot_name = me.first_name or "Gemini AI"
    user = update.effective_user
    is_owner = bool(user and OWNER_ID != 0 and user.id == OWNER_ID)

    await update.message.reply_photo(
        photo=START_IMAGE_URL,
        caption=_welcome_caption(bot_name),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(bot_username, is_owner=is_owner),
    )


# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = (
        "💗 **Gemini Bot — Help & Commands**\n\n"
        "• `/start` - Open welcome panel\n"
        "• `/clear` - Clear chat context\n"
        "• Just send any message to chat with Gemini AI!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# Command: /clear
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    context.user_data.clear()
    await update.message.reply_text("🧹 Chat context reset kar diya gaya hai!")


# Button Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return

    data = query.data
    if data == "owner_panel" and (OWNER_ID == 0 or query.from_user.id != OWNER_ID):
        await query.answer("⛔ This panel is only for the bot owner.", show_alert=True)
        return

    await query.answer()

    if data == "owner_panel":
        if query.message.photo:
            await query.edit_message_caption(
                caption=f"👑 **Owner Panel**\n\nOwner ID: `{OWNER_ID}`\nBot is running successfully!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
            )
        return

    if data in {"home", "back"}:
        me = await context.bot.get_me()
        text = _welcome_caption(me.first_name or "Gemini AI")
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=START_IMAGE_URL,
            caption=text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(
                me.username,
                is_owner=(OWNER_ID != 0 and query.from_user.id == OWNER_ID),
            ),
        )
        return

    if data == "help_main":
        if query.message.photo:
            await query.edit_message_caption(
                caption="💗 **Help Section**\n\nUse commands or chat directly with the AI bot.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
            )
        return

    if data == "chat":
        if query.message.photo:
            await query.edit_message_caption(
                caption="💬 **Chat With Me**\n\nAb aap mujhe koi bhi message bhej sakte hain!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
            )
        return


# Gemini AI Message Handler (Updated to gemini-3.8-flash)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    await update.message.chat.send_action(ChatAction.TYPING)

    if not GEMINI_API_KEY:
        await update.message.reply_text("❌ **Error:** `GEMINI_API_KEY` is empty or not set in Heroku Config Vars!")
        return

    try:
        response = ai_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_text,
        )
        reply_text = response.text if response.text else "Sorry, main iska jawab nahi de paaya."
        await update.message.reply_text(reply_text)

    except Exception as e:
        err_msg = str(e)
        logging.error(f"Gemini API Error: {err_msg}")
        await update.message.reply_text(f"⚠️ **Gemini Error:**\n<code>{html.escape(err_msg)}</code>", parse_mode="HTML")


def main():
    if not BOT_TOKEN or not GEMINI_API_KEY:
        print("❌ Error: BOT_TOKEN ya GEMINI_API_KEY environment variable missing hai!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🤖 Gemini Telegram Bot successfully start ho gaya hai!")
    app.run_polling()


if __name__ == "__main__":
    main()
