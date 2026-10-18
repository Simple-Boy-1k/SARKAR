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
        f"✨ ʜɪ ʜᴇʟʟᴏ, ɪ'ᴍ <b>{safe_name}</b> 🤖💗\n\n"
        "Your friendly AI companion for chat, memory, games and everyday help. 🌸✨\n\n"
        "💬 Natural Chat • 🧠 Smart Responses • ⚡ Fast Replies 🚀\n\n"
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
        rows.append([_btn("👑 ᴏᴡɴᴇʀ ᴘᴀɴᴇﾙ", callback_data="owner_panel", style="danger")])
    
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
        "• `/start` - Open welcome panel ✨\n"
        "• `/clear` - Clear chat context 🧹\n"
        "• Bas kuch bhi message bhejo aur aaram se baat karo! 😊"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# Command: /clear
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    context.user_data.clear()
    await update.message.reply_text("🧹 Chat context bilkul clean kar diya gaya hai dost! ✨")


# Button Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return

    data = query.data
    if data == "owner_panel" and (OWNER_ID == 0 or query.from_user.id != OWNER_ID):
        await query.answer("⛔ Yeh panel sirf bot owner ke liye hai!", show_alert=True)
        return

    await query.answer()

    if data == "owner_panel":
        if query.message.photo:
            await query.edit_message_caption(
                caption=f"👑 **Owner Panel**\n\nOwner ID: `{OWNER_ID}`\nBot ekdum mast chal raha hai! 🚀",
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
                caption="💗 **Help Section**\n\nCommands use karo ya seedha chat mein baat karo! ✨",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
            )
        return

    if data == "chat":
        if query.message.photo:
            await query.edit_message_caption(
                caption="💬 **Chat With Me**\n\nAb aap mujhe koi bhi lamba ya chhota message bhej sakte hain! Main bilkul insano ki tarah jawab dungi. 🌸",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
            )
        return


# Helper function to send long messages safely (preventing Telegram 4096 char limit error)
async def send_long_message(update: Update, text: str):
    if not text:
        return
    if len(text) <= 4000:
        await update.message.reply_text(text)
    else:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000])


# Sticker Handler (Jab koi group ya private mein sticker dale)
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.sticker:
        return
    
    # Human-like cute sticker response with emojis
    responses = [
        "🔥 Arre kya mast sticker hai bhai! 😎✨",
        "uff yeh sticker! 🤭❤️",
        "Aha! Sahi sticker bheja hai 🤌🔥",
        "Mast sticker hai bro! 🚀💯",
        "Haha nice one! 🌸✨"
    ]
    import random
    await update.message.reply_text(random.choice(responses))


# Gemini AI Message Handler (Optimized, Human-like, Emoji-rich & Error Proof)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    await update.message.chat.send_action(ChatAction.TYPING)

    if not GEMINI_API_KEY:
        await update.message.reply_text("❌ **Error:** `GEMINI_API_KEY` set nahi hai Heroku config vars mein!")
        return

    try:
        # Human-like prompting context for Gemini
        system_instruction = (
            "You are a friendly, cool, and expressive human-like AI companion on Telegram. "
            "Talk naturally like a close friend, use Hinglish or English based on the user's style, "
            "and add cool emojis (like ✨, 🌸, 🚀, 🔥, 😊, ❤️) naturally in your sentences. "
            "Match the user's vibe and reply engagingly."
        )
        
        full_prompt = f"{system_instruction}\n\nUser Message: {user_text}"

        response = ai_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=full_prompt,
        )
        
        reply_text = response.text if response.text else "Arre arre, kuch samajh nahi aaya, thoda doosre tarike se bolo na! 😅✨"
        
        # Send long messages safely without crashing
        await send_long_message(update, reply_text)

    except Exception as e:
        err_msg = str(e)
        logging.error(f"Gemini API Error: {err_msg}")
        
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            await update.message.reply_text("⏳ Arre yaar, bohot saari requests aa gayi hain! Thoda sa slow ho jao na, 1 minute baad try karna! 😅🙏")
        else:
            await update.message.reply_text("💗 Oops! Thoda sa connection issue ho gaya hai, ek baar phir se message bhejo na please! ✨")


def main():
    if not BOT_TOKEN or not GEMINI_API_KEY:
        print("❌ Error: BOT_TOKEN ya GEMINI_API_KEY missing hai!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Sticker Handler
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    
    # Text Handler
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🤖 Gemini Telegram Bot successfully start ho gaya hai! ✨")
    app.run_polling()


if __name__ == "__main__":
    main()
