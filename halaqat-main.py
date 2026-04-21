import os
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not TOKEN:
    raise ValueError("BOT_TOKEN غير موجود")

chat_data_store = {}

ARABIC_DAYS = {
    0: "الاثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}


def get_chat_data(chat_id: int) -> dict:
    if chat_id not in chat_data_store:
        chat_data_store[chat_id] = {
            "users": {},
            "message_id": None,
            "message_type": None,
        }
    return chat_data_store[chat_id]


def get_today_text():
    now = datetime.now(ZoneInfo("Asia/Riyadh"))
    return f"{ARABIC_DAYS[now.weekday()]} - {now.strftime('%Y/%m/%d')}"


def build_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ قرأت", callback_data="read"),
            InlineKeyboardButton("📝 سجل اسمي", callback_data="register"),
        ],
        [
            InlineKeyboardButton("🗑️ احذف اسمي", callback_data="delete"),
            InlineKeyboardButton("🌸 مستمعة", callback_data="listener"),
        ],
    ])


def format_users(users):
    if not users:
        return "لا توجد أسماء بعد"

    rtl = "\u200F"
    result = []

    for i, (name, status) in enumerate(users.items(), start=1):
        name = escape(name)

        if status == "read":
            result.append(f"{rtl}{i}. {name}   ✅")
        elif status == "listener":
            result.append(f"{rtl}{i}. {name} (مستمعة)")
        else:
            result.append(f"{rtl}{i}. {name}")

    return "\n".join(result)

def build_caption(users):
    return (
        f"📅 <b>{escape(get_today_text())}</b>\n\n"
        "🌸💙🌸💙🌸💙🌸💙🌸\n\n"
        "<b>قائمة المسجلات</b>\n"
        "ــــــــــــــــــــــ\n\n"
        f"{format_users(users)}\n\n"
        "🌸💙🌸💙🌸💙🌸💙🌸\n\n"
        "\n"
        "كل طريق تسلكه قد يكون فيه نجاح وفشل إلا طريق القرآن فإنه محفوفٌ بالأُجور\n"
        "حتى التأتأةُ فيه تؤجر عليها 💙🌸"
    )


async def send_message(chat_id, context):
    data = get_chat_data(chat_id)

    caption = build_caption(data["users"])
    buttons = build_buttons()

    try:
        with open("form.png", "rb") as photo:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
            )
        data["message_id"] = msg.message_id
        data["message_type"] = "photo"

    except:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
        )
        data["message_id"] = msg.message_id
        data["message_type"] = "text"


async def update_message(chat_id, context):
    data = get_chat_data(chat_id)

    caption = build_caption(data["users"])
    buttons = build_buttons()

    try:
        if data["message_type"] == "photo":
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=data["message_id"],
                caption=caption,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
            )
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=data["message_id"],
                text=caption,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
            )
    except:
        await send_message(chat_id, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    data = get_chat_data(chat_id)
    data["users"] = {}

    await send_message(chat_id, context)


async def publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    data = get_chat_data(int(CHANNEL_ID))
    data["users"] = {}

    await send_message(int(CHANNEL_ID), context)
    await update.message.reply_text("تم النشر في القناة ✅")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    name = user.full_name or user.first_name

    chat_id = query.message.chat_id
    data = get_chat_data(chat_id)
    users = data["users"]

    # ✅ سجل اسمي
    if query.data == "register":
        if name in users:
            await query.answer("تم تسجيل اسمك مسبقًا", show_alert=True)
            return

        users[name] = "normal"
        await query.answer()

    # ✅ قرأت
    elif query.data == "read":
        if name not in users:
            await query.answer("سجلي اسمك أولًا", show_alert=True)
            return

        users[name] = "read"
        await query.answer()

    # ✅ مستمعة
    elif query.data == "listener":
        if name not in users:
            await query.answer("سجلي اسمك أولًا", show_alert=True)
            return

        users[name] = "listener"
        await query.answer()

    # ✅ حذف
    elif query.data == "delete":
        if name not in users:
            await query.answer("اسمك غير موجود", show_alert=True)
            return

        users.pop(name)
        await query.answer("تم حذف اسمك")

    await update_message(chat_id, context)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("publish", publish))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
