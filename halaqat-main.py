import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

group_data = {}

def get_chat_data(chat_id):
    if chat_id not in group_data:
        group_data[chat_id] = {
            "users": {},
            "list_message_id": None,
            "photo_message_id": None,
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

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=text
    )
    data["list_message_id"] = msg.message_id

async def update_current_list(chat_id, context):
    data = get_chat_data(chat_id)
    text = format_list(data["users"])

    if data["list_message_id"] is None:
        await send_new_list(chat_id, context)
        return

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=data["list_message_id"],
            text=text
        )
    except Exception:
        await send_new_list(chat_id, context)

async def send_new_photo(chat_id, context):
    data = get_chat_data(chat_id)
    buttons = build_buttons()

    try:
        with open("halaqat.png", "rb") as photo:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption="🌿 أهلًا بك في بوت منظم أدوار الحلقة",
                reply_markup=buttons
            )
            data["photo_message_id"] = msg.message_id
    except FileNotFoundError:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text="🌿 أهلًا بك في بوت منظم أدوار الحلقة",
            reply_markup=buttons
        )
        data["photo_message_id"] = msg.message_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    chat_id = chat.id

    # السماح فقط للمشرفين أو مالك المجموعة
    if chat.type in ["group", "supergroup"]:
        member = await context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ["administrator", "creator"]:
            try:
                await update.message.delete()
            except Exception:
                pass
            return

    data = get_chat_data(chat_id)

    # تصفير القائمة وإنشاء قائمة جديدة نظيفة
    data["users"] = {}

    # إرسال صورة جديدة وأزرار جديدة
    await send_new_photo(chat_id, context)

    # إرسال قائمة جديدة نظيفة
    await send_new_list(chat_id, context)

    # حذف أمر /start
    try:
        await update.message.delete()
    except Exception:
        pass

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user = query.from_user
    user_name = user.full_name.strip() if user.full_name else user.first_name

    data = get_chat_data(chat_id)
    users = data["users"]

    if query.data == "register":
        if user_name not in users:
            users[user_name] = "normal"

    elif query.data == "read":
        users[user_name] = "read"

    elif query.data == "listener":
        users[user_name] = "listener"

    elif query.data == "delete":
        if user_name in users:
            del users[user_name]

    await update_current_list(chat_id, context)

def main():
    if not TOKEN:
        print("❌ BOT_TOKEN غير موجود داخل ملف .env")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
