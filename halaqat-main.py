import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running"

# ---------- BOT ----------
group_data = {}

def get_chat_data(chat_id):
    if chat_id not in group_data:
        group_data[chat_id] = {
            "users": {},
            "list_message_id": None,
        }
    return group_data[chat_id]

def build_buttons():
    keyboard = [
        [
            InlineKeyboardButton("📝 سجل اسمي", callback_data="register"),
            InlineKeyboardButton("✅ قرأت", callback_data="read"),
        ],
        [
            InlineKeyboardButton("🌷 مستمعة", callback_data="listener"),
            InlineKeyboardButton("🗑️ احذف اسمي", callback_data="delete"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def format_list(users):
    if not users:
        return "📋 قائمة الحلقة:\n\nلا توجد أسماء بعد"

    text = "📋 قائمة الحلقة:\n\n"
    for i, (name, status) in enumerate(users.items(), start=1):
        if status == "read":
            text += f"{i}. {name} ✅\n"
        elif status == "listener":
            text += f"{i}. {name} (مستمعة)\n"
        else:
            text += f"{i}. {name}\n"
    return text

async def send_new_list(chat_id, context):
    data = get_chat_data(chat_id)
    text = format_list(data["users"])

    msg = await context.bot.send_message(chat_id=chat_id, text=text)
    data["list_message_id"] = msg.message_id

async def update_list(chat_id, context):
    data = get_chat_data(chat_id)
    text = format_list(data["users"])

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=data["list_message_id"],
            text=text
        )
    except:
        await send_new_list(chat_id, context)

async def send_photo(chat_id, context):
    buttons = build_buttons()

    try:
        with open("halaqat.png", "rb") as photo:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption="🌿 أهلًا بك في بوت منظم أدوار الحلقة",
                reply_markup=buttons
            )
    except:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🌿 أهلًا بك في بوت منظم أدوار الحلقة",
            reply_markup=buttons
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    data = get_chat_data(chat_id)
    data["users"] = {}

    await send_photo(chat_id, context)
    await send_new_list(chat_id, context)

    try:
        await update.message.delete()
    except:
        pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user_name = query.from_user.full_name

    data = get_chat_data(chat_id)

    if query.data == "register":
        data["users"][user_name] = "normal"
    elif query.data == "read":
        data["users"][user_name] = "read"
    elif query.data == "listener":
        data["users"][user_name] = "listener"
    elif query.data == "delete":
        data["users"].pop(user_name, None)

    await update_list(chat_id, context)

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    Thread(target=run_bot).start()
    app_web.run(host="0.0.0.0", port=10000)
