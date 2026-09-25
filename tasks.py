from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def tasks_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 الاشتراك في القناة", url="https://t.me/")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
    ])

async def show_tasks(update, context):
    text = (
        "🎯 قسم المهام\n\n"
        "نفّذ المهام التي يضيفها المشرف.\n"
        "ملاحظة: التحقق من إعلانات خارجية وزيارات TikTok/Instagram "
        "يحتاج مزود تحقق خارجي."
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=tasks_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=tasks_keyboard())
