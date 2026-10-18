# ==========================================================
# DEEP EMOTIONS — COMPLETE ENTERPRISE TELEGRAM BOT CODE
# Full Features: Memory, Anti-Spam, Voice, AI Tools, Games,
# Human-like Girl Vibe, Sticker Tag & Reply, Bad Word Filter
# ==========================================================

import os
import html
import re
import time
import random
from pathlib import Path
from collections import defaultdict, deque

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
    MessageEntity,
)

from telegram.constants import ChatAction
from telegram.ext import ContextTypes, ApplicationHandlerStop

from google import genai

from config import (
    BOT_TOKEN, GEMINI_API_KEY, OWNER_ID, OWNER_USERNAME,
    SUPPORT_CHAT_URL, SUPPORT_CHANNEL_URL, UPDATES_CHANNEL_URL,
    START_IMAGE_URL, OUR_BOTS_URL
)

from bot.social_engine import (
    should_reply_group,
    mark_group_reply,
    social_game,
)

from bot.ai import (
    generate_reply,
    extract_memories,
    ai_tool,
    transcribe_voice,
)

from bot.database import (
    add_message,
    get_history,
    clear_history,
    count_messages,
    add_memory,
    get_memories,
    delete_memory,
    clear_memories,
    count_memories,
    add_group_message,
    get_group_context,
    clear_group_context,
    count_group_messages,
)

# ==========================================================
# LOGGING & GEMINI SETUP
# ==========================================================
import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if not GEMINI_API_KEY:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY is missing or empty!")

ai_client = genai.Client(api_key=GEMINI_API_KEY)


# ==========================================================
# RATE LIMITER
# ==========================================================
user_requests = defaultdict(deque)
WINDOW_SECONDS = 20
MAX_REQUESTS = 5
GROUP_REPLY_ALWAYS = True

def allowed(user_id):
    now = time.monotonic()
    q = user_requests[user_id]
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= MAX_REQUESTS:
        return False
    q.append(now)
    return True


# ==========================================================
# ANTI SPAM & MODERATION
# ==========================================================
spam_tracker = defaultdict(deque)
warnings = defaultdict(int)

SPAM_WINDOW_SECONDS = 10
SPAM_MESSAGE_LIMIT = 6
MAX_WARNINGS = 3
MUTE_SECONDS = 300

LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/)",
    re.IGNORECASE,
)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type not in ("group", "supergroup"):
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except Exception as exc:
        print("Admin check error:", repr(exc))
        return False

async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return False
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type not in ("group", "supergroup") or user.is_bot:
        return False

    if await is_admin(update, context):
        return False

    text = update.message.text or ""
    key = (chat.id, user.id)
    now = time.monotonic()

    q = spam_tracker[key]
    while q and now - q[0] > SPAM_WINDOW_SECONDS:
        q.popleft()
    q.append(now)

    flood_detected = len(q) > SPAM_MESSAGE_LIMIT
    link_detected = bool(LINK_PATTERN.search(text))

    if not flood_detected and not link_detected:
        return False

    try:
        await update.message.delete()
    except Exception as exc:
        print("Message delete error:", repr(exc))

    warnings[key] += 1
    current_warning = warnings[key]

    if current_warning < MAX_WARNINGS:
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"⚠️ **[DANGER WARNING]** {user.first_name or 'User'}, spam/link detected. Warning {current_warning}/{MAX_WARNINGS}.",
                parse_mode="Markdown",
            )
        except Exception as exc:
            print("Warning message error:", repr(exc))
        raise ApplicationHandlerStop

    try:
        permissions = ChatPermissions(
            can_send_messages=False, can_send_audios=False, can_send_documents=False,
            can_send_photos=False, can_send_videos=False, can_send_video_notes=False,
            can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False,
            can_add_web_page_previews=False,
        )
        until_date = int(time.time() + MUTE_SECONDS)
        await context.bot.restrict_chat_member(chat_id=chat.id, user_id=user.id, permissions=permissions, until_date=until_date)
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"🛑 **[MUTED]** {user.first_name or 'User'} ko 5 minutes ke liye mute kiya gaya spam/link activity ke karan.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        print("Mute error:", repr(exc))

    warnings[key] = 0
    spam_tracker[key].clear()
    raise ApplicationHandlerStop


# ==========================================================
# BUTTON STYLING & MENUS
# ==========================================================
WELCOME_IMAGE_URL = START_IMAGE_URL or "https://raw.githubusercontent.com/AashishTechs/Deep-Emotion/main/Welcome.jpg?v=2"

def _btn(text, *, callback_data=None, url=None, style=None):
    kwargs = {}
    if style:
        kwargs["style"] = style
    return InlineKeyboardButton(text=text, callback_data=callback_data, url=url, **kwargs)

def _welcome_caption(bot_name):
    safe_name = html.escape(bot_name or "Deep Emotions")
    return (
        f"✨ Hii everyone, I'm <b>{safe_name}</b> 💖🌸\n\n"
        "Your friendly AI companion for chat, memory, games and everyday help. 🌸\n\n"
        "🧠 Smart Memory • 💬 Natural Chat • 🎮 Games • 🛠️ AI Tools\n\n"
        "Choose an option below and let's get started. 👇"
    )

def main_menu_keyboard(bot_username="deepemotions01", is_owner=False):
    username = (bot_username or "deepemotions01").lstrip("@")
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
    
    owner_username = (OWNER_USERNAME or "").strip().lstrip("@")
    if owner_username:
        rows.append([_btn("👑 ᴏᴡɴᴇʀ", url=f"https://t.me/{owner_username}", style="primary")])
    
    rows.append([_btn("➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url=f"https://t.me/{username}?startgroup=true", style="primary")])
    
    if is_owner:
        rows.append([_btn("🔴 👑 ᴏᴡɴᴇʀ ᴘᴀɴᴇʟ", callback_data="owner_panel", style="danger")])
    return InlineKeyboardMarkup(rows)

def help_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                _btn("💬 ᴄʜᴀᴛ", callback_data="help_chat", style="danger"),
                _btn("🧠 ᴍᴇᴍᴏʀʏ", callback_data="help_memory", style="danger"),
                _btn("🛠️ ᴀɪ ᴛᴏᴏʟs", callback_data="help_ai_tools", style="danger"),
            ],
            [
                _btn("🎙️ ᴠᴏɪᴄᴇ", callback_data="help_voice", style="primary"),
                _btn("👥 ɢʀᴏᴜᴘ", callback_data="help_group", style="primary"),
                _btn("🔒 ᴘʀɪᴠᴀᴄʏ", callback_data="help_privacy", style="primary"),
            ],
            [
                _btn("🎮 ɢᴀᴍᴇs", callback_data="help_games", style="success"),
                _btn("📊 ꜱᴛᴀᴛs", callback_data="help_stats", style="success"),
                _btn("📖 ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_commands", style="success"),
            ],
            [_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")],
        ]
    )

HELP_SECTION_TEXT = {
    "help_chat": "💬 **Chat With Me**\n\nPrivate chat mein ya group mein tag/reply karke baat karo. Ekdum pyari girl vibe ke sath! ✨",
    "help_memory": "🧠 **Memory**\n\n/memory — saved memories\n/forget ID — delete memory\n/forget_all — delete all memories\n/clear — clear chat history",
    "help_ai_tools": "🛠️ **AI Tools**\n\nRewrite, Summarize, Translate, Explain & Study Help.",
    "help_voice": "🎙️ **Voice AI**\n\nVoice message bhejo aur main transcribe karke reply dungi.",
    "help_group": "👥 **Group Chats**\n\nTag ya reply karne par hi group mein reply karungi, faltu mein beech mein nahi bolungi!",
    "help_privacy": "🔒 **Privacy**\n\nPersonal memories group context mein share nahi hoti.",
    "help_games": "🎮 **Games**\n\n/game truth | /game dare | /game wyr | /game joke",
    "help_stats": "📊 **Stats**\n\n/stats se messages aur memories dekho.",
    "help_commands": "📖 **Commands**\n\n/start, /help, /ask, /game, /memory, /forget, /clear, /stats, /privacy",
}

def help_section_keyboard(section):
    rows = []
    if section == "help_ai_tools":
        rows.append([_btn("🛠️ ᴏᴘᴇɴ ᴀɪ ᴛᴏᴏʟs", callback_data="ai_tools", style="success")])
    rows.append([_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="primary")])
    return InlineKeyboardMarkup(rows)

def back_button():
    return InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]])

def ai_tools_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                _btn("✍️ Rewrite", callback_data="tool_rewrite", style="danger"),
                _btn("📝 Summarize", callback_data="tool_summarize", style="danger"),
            ],
            [
                _btn("🌐 Translate", callback_data="tool_translate", style="primary"),
                _btn("💡 Explain", callback_data="tool_explain", style="primary"),
            ],
            [_btn("📚 Study Help", callback_data="tool_study", style="success")],
            [_btn("🔙 ʙᴀᴄᴋ ᴛᴏ ʜᴇʟᴘ", callback_data="help_main", style="primary")],
        ]
    )


# ==========================================================
# COMMAND HANDLERS
# ==========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    me = await context.bot.get_me()
    user = update.effective_user
    is_owner = bool(user and OWNER_ID != 0 and user.id == OWNER_ID)
    await update.message.reply_photo(
        photo=WELCOME_IMAGE_URL,
        caption=_welcome_caption(me.first_name),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(me.username, is_owner=is_owner),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text("💗 **Deep Emotions — Help & Commands**\n\nChoose a category below. 👇", parse_mode="Markdown", reply_markup=help_menu_keyboard())

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text("🔒 **Privacy Info**\n\nPersonal memories are safe and secure.", parse_mode="Markdown", reply_markup=back_button())

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    game = (context.args[0] if context.args else "joke").lower()
    if game not in {"truth", "dare", "wyr", "would", "joke"}:
        await update.message.reply_text("🎮 Games: /game truth | /game dare | /game wyr | /game joke")
        return
    await update.message.reply_text(social_game(game))

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("💬 Example: `/ask Python kya hai?`", parse_mode="Markdown")
        return
    await process_ai(update, text, context)

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await clear_history(update.effective_chat.id, update.effective_user.id)
    if update.effective_chat.type in ("group", "supergroup"):
        await clear_group_context(update.effective_chat.id)
    await update.message.reply_text("🔴🧹 Conversation history clear kar di gayi hai!")

async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    memories = await get_memories(update.effective_user.id, limit=10)
    if not memories:
        await update.message.reply_text("🧠 Meri memory mein aapke baare mein kuch saved nahi hai.", reply_markup=back_button())
        return
    lines = ["🧠 **Tumhari Long-Term Memories**\n"]
    for mid, mem in memories:
        lines.append(f"**{mid}.** {mem}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=back_button())

async def forget_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not context.args:
        await update.message.reply_text("Usage: `/forget <ID>`", parse_mode="Markdown")
        return
    try:
        mid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Valid memory ID number do.")
        return
    deleted = await delete_memory(update.effective_user.id, mid)
    if deleted:
        await update.message.reply_text(f"🔴🗑️ Memory #{mid} delete kar di.")
    else:
        await update.message.reply_text("❌ Memory ID nahi mili.")

async def forget_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await clear_memories(update.effective_user.id)
    await update.message.reply_text("🔴🧹 Saari long-term memories delete kar di gayi hain.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.effective_user.id
    cid = update.effective_chat.id
    t_msg = await count_messages(cid, uid)
    t_mem = await count_memories(uid)
    g_msg = await count_group_messages(cid) if update.effective_chat.type != "private" else 0
    await update.message.reply_text(f"📊 **Stats**\n\n💬 Messages: {t_msg}\n🧠 Memories: {t_mem}\n👥 Group Msgs: {g_msg}", parse_mode="Markdown")


# ==========================================================
# SAFE LONG MESSAGE SENDER (Preventing 4000 char limits)
# ==========================================================
async def send_long_message(update: Update, text: str):
    if not text:
        return
    if len(text) <= 4000:
        await update.message.reply_text(text)
    else:
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i+4000])


# ==========================================================
# STICKER HANDLER (Tag & Reply with Cute Reactions)
# ==========================================================
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


# ==========================================================
# CHAT MESSAGE & AI PROCESSOR (Human Vibe, Owner & Filter)
# ==========================================================
pending_ai_tools = {}

async def save_group_context(update: Update):
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user or chat.type == "private" or not update.message.text:
        return
    await add_group_message(chat.id, user.id, f"@{user.username}" if user.username else None, user.full_name or "Unknown", update.message.text)

async def chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    if chat.type != "private":
        await save_group_context(update)

    me = await context.bot.get_me()
    bot_username = (me.username or "").lower()
    is_private = chat.type == "private"
    
    mentioned = f"@{bot_username}" in text.lower() if bot_username else False
    replied_to_bot = (
        update.message.reply_to_message is not None
        and update.message.reply_to_message.from_user is not None
        and update.message.reply_to_message.from_user.id == me.id
    )

    # Group mein bina tag/reply ke chup rahegi (Doosron ki baat mein beech mein nahi bolegi)
    if not is_private and not mentioned and not replied_to_bot:
        return

    if mentioned and bot_username:
        text = re.sub(rf"@{re.escape(bot_username)}", "", text, flags=re.IGNORECASE).strip()

    tool_key = (chat.id, user.id)
    selected_tool = pending_ai_tools.pop(tool_key, None)
    if selected_tool:
        await process_ai_tool(update, context, selected_tool, text)
        return

    await process_ai(update, text or "Hi", context)

async def process_ai_tool(update: Update, context: ContextTypes.DEFAULT_TYPE, tool: str, text: str):
    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        reply = await ai_tool(tool, text)
        await send_long_message(update, reply)
    except Exception as exc:
        print("AI tool error:", repr(exc))
        await update.message.reply_text("Sorry 💗 AI Tool use karte waqt problem aa gayi.")

async def process_ai(update, text, context: ContextTypes.DEFAULT_TYPE = None):
    user = update.effective_user
    chat = update.effective_chat
    if not user or not update.message:
        return

    if not allowed(user.id) and user.id != OWNER_ID:
        await update.message.reply_text("⏳ Thoda slow... bahut requests aa gayi 😅")
        return

    is_group = chat.type in ("group", "supergroup")
    history = await get_history(chat.id, user.id)
    memories = [] if is_group else await get_memories(user.id, limit=10)
    group_context = await get_group_context(chat.id, limit=15) if is_group else []

    owner_handle = f"@{OWNER_USERNAME}" if OWNER_USERNAME else "Not Set"

    try:
        await update.message.chat.send_action(ChatAction.TYPING)

        # Advanced Human Girl Vibe + Gentle Scolding for Bad Words + Owner Recognition
        system_instruction = (
            f"You are a sweet, smart, and expressive Indian girl AI companion named {update.effective_user.first_name or 'Bot'} on Telegram[span_0](start_span)[span_0](end_span). "
            f"Talk like a natural human girl in Hinglish or English using cute emojis like ✨, 🌸, 🥺, 🙈, 💖, ✌️. "
            f"Always address the user by their name ({user.first_name})[span_1](start_span)[span_1](end_span). "
            f"RULE FOR BAD WORDS: If the user ({user.first_name}) uses abusive language or vulgar words, do not get angry. Instead, gently scold and teach them like a sensible girl (e.g., '{user.first_name}, aisi gandi baatein nahi bolte na! Achhe bacche achhi bhasha use karte hain 🥺🌸'). "
            f"GROUP OWNER INFO: The group owner username is {owner_handle}. If anyone asks who the owner or admin is, tell them politely that {owner_handle} is the owner[span_2](start_span)[span_2](end_span)."
        )

        full_prompt = f"{system_instruction}\n\nUser ({user.first_name}) says: {text}"

        response = ai_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=full_prompt,
        )

        reply = response.text if response.text else f"Arre {user.first_name}, samajh nahi aaya kya bol rahe ho! 🙈✨"

        await add_message(chat.id, user.id, "user", text)
        await add_message(chat.id, user.id, "model", reply)

        if not is_group:
            new_memories = await extract_memories(text)
            for memory in new_memories:
                await add_memory(user.id, memory)

        await send_long_message(update, reply)

    except Exception as exc:
        print("AI error:", repr(exc))
        await update.message.reply_text(f"Arre yaar {user.first_name}, thoda network issue ho gaya hai, baad mein baat karte hain na! 🥺💔")


# ==========================================================
# BUTTON HANDLER
# ==========================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.message:
        return
    data = query.data

    if data == "owner_panel" and (OWNER_ID == 0 or query.from_user.id != OWNER_ID):
        await query.answer("⛔ Yeh panel sirf bot owner ke liye hai!", show_alert=True)
        return

    await query.answer()

    async def edit_panel(text, markup):
        if query.message.photo:
            await query.edit_message_caption(caption=text, parse_mode="Markdown", reply_markup=markup)
        else:
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=markup)

    if data == "owner_panel":
        await edit_panel(
            f"👑 **Owner Panel**\n\nOwner ID: `{OWNER_ID}`\nBot is running successfully with all features!",
            InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]),
        )
        return

    if data in {"home", "back"}:
        me = await context.bot.get_me()
        try:
            await query.message.delete()
        except Exception:
            pass
        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=WELCOME_IMAGE_URL,
            caption=_welcome_caption(me.first_name),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(me.username, is_owner=(OWNER_ID != 0 and query.from_user.id == OWNER_ID)),
        )
        return

    if data == "help_main":
        await edit_panel("💗 **Help & Commands**\n\nChoose a category below. 👇", help_menu_keyboard())
        return

    if data == "chat":
        await edit_panel("💬 **Chat With Me**\n\nBas apna message bhejo ya group mein tag karo!", InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="home", style="danger")]]))
        return

    if data == "ai_tools":
        await edit_panel("🛠️ **AI Tools**\n\nNeeche se tool choose karo.", ai_tools_keyboard())
        return

    tool_map = {
        "tool_rewrite": ("rewrite", "✍️ **Rewrite**\n\nApna text bhejo."),
        "tool_summarize": ("summarize", "📝 **Summarize**\n\nApna long text bhejo."),
        "tool_translate": ("translate", "🌐 **Translate**\n\nText bhejo."),
        "tool_explain": ("explain", "💡 **Explain**\n\nTopic bhejo."),
        "tool_study": ("study", "📚 **Study Help**\n\nQuestion bhejo."),
    }

    if data in tool_map:
        t_name, t_text = tool_map[data]
        pending_ai_tools[(query.message.chat.id, query.from_user.id)] = t_name
        await edit_panel(t_text + "\n\n🔙 Cancel karne ke liye Back dabao.", InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="ai_tools", style="primary")]]))
        return

    if data == "memory":
        memories = await get_memories(query.from_user.id, limit=10)
        lines = ["🧠 **Tumhari Long-Term Memories**\n"] if memories else ["🧠 **Memory**\n\nKuch saved nahi hai."]
        for mid, mem in memories:
            lines.append(f"**{mid}.** {mem}")
        await edit_panel("\n".join(lines), InlineKeyboardMarkup([[_btn("🔴🗑️ ғᴏʀɢᴇᴛ ᴀʟʟ", callback_data="forget_all_confirm", style="danger")], [_btn("🔙 ʙᴀᴄᴋ", callback_data="help_main", style="primary")]]))
        return

    if data == "forget_all_confirm":
        await clear_memories(query.from_user.id)
        await edit_panel("🔴🧹 **Memory cleared successfully!**", InlineKeyboardMarkup([[_btn("🔙 ʙᴀᴄᴋ", callback_data="help_main", style="primary")]]))
        return


# ==========================================================
# VOICE HANDLER
# ==========================================================
async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.voice:
        return
    user = update.effective_user
    chat = update.effective_chat
    status_message = await update.message.reply_text("🎙️ **Voice sun rahi hoon...**", parse_mode="Markdown")
    temp_dir = Path("data") / "voice_cache"
    temp_dir.mkdir(parents=True, exist_ok=True)
    voice_file_path = temp_dir / f"{chat.id}_{update.message.message_id}.ogg"

    try:
        telegram_file = await context.bot.get_file(update.message.voice.file_id)
        await telegram_file.download_to_drive(custom_path=str(voice_file_path))
        transcribed_text = await transcribe_voice(str(voice_file_path))
        if not transcribed_text:
            await status_message.edit_text("😕 Voice samajh nahi aayi, dubara bhejo.")
            return

        is_group = chat.type in ("group", "supergroup")
        history = await get_history(chat.id, user.id)
        memories = [] if is_group else await get_memories(user.id, limit=10)
        group_context = await get_group_context(chat.id, limit=15) if is_group else []

        reply = await generate_reply(history=history, user_message=transcribed_text, memories=memories, group_context=group_context, is_group=is_group, current_user_name=user.first_name)
        await status_message.edit_text(reply)
    except Exception as exc:
        print("Voice error:", repr(exc))
        await status_message.edit_text("Sorry 💗 voice process karne mein error aaya.")
    finally:
        if voice_file_path.exists():
            voice_file_path.unlink()
