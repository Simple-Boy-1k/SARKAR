import os
import html
import logging
import random
import re
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
    safe_name = html.escape(bot_name or "Deep Emotions")
    return (
        f"✨ Hii everyone, I'm <b>{safe_name}</b> 💖🌸\n\n"
        "Aapki pyari AI companion! Mujhse chat karo, games khelo ya baatein karo. ✨\n\n"
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
    user = update.effective_user
    is_owner = bool(user and OWNER_ID != 0 and user.id == OWNER_ID)
    await update.message.reply_photo(
        photo=START_IMAGE_URL,
        caption=_welcome_caption(me.first_name),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(me.username, is_owner=is_owner),
    )


# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text("💗 **Help Menu:**\n\n• Group mein mujhe tag karke ya reply karke baat karo ✨\n• Owner ya group ke baare mein poochho! 🌸", parse_mode="Markdown")


# Command: /clear
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    context.user_data.clear()
    await update.message.reply_text("🧹 Sab saaf kar diya! Chalo ab naye sire se baatein karte hain ✨")


# Button Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return
    data = query.data
    await query.answer()

    if data == "home":
        me = await context.bot.get_me()
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=START_IMAGE_URL,
            caption=_welcome_caption(me.first_name),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(me.username, is_owner=(query.from_user.id == OWNER_ID)),
        )


# Safe Long Message Sender
async def send_long_message(update: Update, text: str):
    if not text:
        return
    if len(text) <= 4000:
        await update.message.reply_text(text)
    else:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000])


# New Member Welcome Handler (Group mein naye member ke aane par pyara welcome)
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        
        name = member.first_name or "Friend"
        welcome_messages = [
            f"✨ Arey dekho kon aaya! Welcome to the group, {name} ji! 🌸💖 Aaram se baitho aur maza lo!",
            f"Hii {name} ji! 👋 Welcome to our family. Yahan sab mast hain, aap bhi enjoy karo! ✨🌸",
            f"Welcome {name} ji! 💖 Group ki raunak badhane ke liye shukriya. Chalo ab baatein shuru karo! ✨"
        ]
        await update.message.reply_text(random.choice(welcome_messages))


# Smart Sticker Reply Handler
async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.sticker:
        return
    user = update.effective_user
    responses = [
        f"Awww {user.first_name}, kitna cute sticker hai! 🥺💖",
        f"Uff {user.first_name}! Aise stickers kahan se laate ho? 🤭✨",
        f"Haha {user.first_name}, mast sticker tha yeh toh! 🤌🔥",
        f"Aha! {user.first_name} ji, ekdum sahi sticker hai! 🚀💯"
    ]
    await update.message.reply_text(random.choice(responses))


# Smart Group & Private Message Handler (Screenshot Jaisi Playful & Teasing Vibe)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return

    me = await context.bot.get_me()
    bot_username = (me.username or "").lower()

    is_private = chat.type == "private"
    mentioned = f"@{bot_username}" in text.lower() if bot_username else False
    replied_to_bot = (
        update.message.reply_to_message is not None
        and update.message.reply_to_message.from_user is not None
        and update.message.reply_to_message.from_user.id == me.id
    )

    # Group mein bina tag/reply ke chup rahegi
    if not is_private and not mentioned and not replied_to_bot:
        return

    if mentioned and bot_username:
        text = re.sub(rf"@{re.escape(bot_username)}", "", text, flags=re.IGNORECASE).strip()

    await update.message.chat.send_action(ChatAction.TYPING)

    owner_handle = f"@{OWNER_USERNAME}" if OWNER_USERNAME else "Not Set"
    user_full_name = user.full_name or user.first_name

    try:
        # Screenshot jaisi playful, teasing aur sweet ladki wali tone
        system_prompt = (
            f"You are a cute, witty, and playful Indian girl AI companion named {me.first_name} on Telegram[span_1](start_span)[span_1](end_span). "
            f"Talk like a natural human girl in Hinglish or English with cute emojis like ✨, 🌸, 🥺, 🤭, 💖, 😘, 🪄. "
            f"Always address or refer to the user by their full profile name or handle ({user_full_name})[span_2](start_span)[span_2](end_span). "
            f"BEHAVIOR STYLE: Be slightly teasing, witty, and affectionate (just like a close female friend who loves to pull your leg)[span_3](start_span)[span_3](end_span). For example, if they say 'hello' repeatedly, tease them like 'Kitni baar hello bologe, {user_full_name}? Kuch naya shuru karein ya bas hello hi chalega? ✨[span_4](start_span)'[span_4](end_span). "
            f"BAD WORDS RULE: If the user uses abusive or vulgar words, don't get angry, gently and cutely scold them (e.g., '{user_full_name}, aisi gandi baatein nahi bolte na! Achhe bacche bano 🥺🌸'). "
            f"GROUP OWNER INFO: The group owner username is {owner_handle}. If anyone asks who owns this group, tell them politely that {owner_handle} is the owner[span_5](start_span)[span_5](end_span)."
        )

        full_prompt = f"{system_prompt}\n\nUser ({user_full_name}) says: {text}"

        response = ai_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=full_prompt,
        )
        
        reply_text = response.text if response.text else f"Arre {user.first_name}, samajh nahi aaya kya bol rahe ho! 🙈✨"
        await send_long_message(update, reply_text)

    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        await update.message.reply_text(f"Arre yaar {user.first_name}, thoda network issue ho gaya hai, baad mein baat karte hain na! 🥺💔")


def main():
    if not BOT_TOKEN or not GEMINI_API_KEY:
        print("❌ Error: Token or API Key missing!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # New Member Welcome Handler
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    
    # Sticker & Text Handlers
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🤖 Smart Girl AI Bot successfully start ho gaya hai! ✨🌸")
    app.run_polling()


if __name__ == "__main__":
    main()
