import os
from pathlib import Path
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    PreCheckoutQueryHandler, ContextTypes, filters
)

from database import init_db, save_user, get_user, can_download, increase_free_used, set_vip
from downloader import download_media
from tasks import show_tasks
from payments import send_vip_invoice
from admin import admin_command, block_command, unblock_command, vip_command

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
api = FastAPI()

@api.get("/")
async def home():
    return {"status": "online", "bot": "telegram-downloader"}

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ VIP", callback_data="vip"),
         InlineKeyboardButton("🎯 المهام", callback_data="tasks")],
        [InlineKeyboardButton("🎵 صوت فقط", callback_data="audio")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    await update.message.reply_text(
        "مرحبًا بك في بوت تحميل الفيديوهات 🤖\n"
        "أرسل رابط الفيديو لتحميله.\n"
        "لديك 3 تحميلات مجانية.", reply_markup=menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "vip":
        await query.message.reply_text("اضغط /vip لشراء الاشتراك.")
    elif query.data == "tasks":
        await show_tasks(update, context)
    elif query.data == "audio":
        context.user_data["audio_only"] = True
        await query.message.reply_text("أرسل رابطًا الآن لتحميل الصوت فقط.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(update.effective_user)
    if not can_download(user_id):
        await update.message.reply_text("انتهت تحميلاتك المجانية. استخدم /vip أو /tasks.")
        return
    url = update.message.text.strip()
    await update.message.reply_text("⏳ جاري التحميل...")
    try:
        path = await download_media(url, context.user_data.pop("audio_only", False))
        if not path or not Path(path).exists():
            raise RuntimeError("لم يتم العثور على الملف")
        with open(path, "rb") as media:
            if path.suffix.lower() == ".mp3":
                await update.message.reply_audio(media)
            else:
                await update.message.reply_video(media)
        row = get_user(user_id)
        if row and not row["vip"]:
            increase_free_used(user_id)
        Path(path).unlink(missing_ok=True)
        Path(path).parent.rmdir()
    except Exception as exc:
        await update.message.reply_text("تعذر التحميل. جرّب رابطًا آخر أو ملفًا أصغر.")

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.successful_payment.invoice_payload == "vip_subscription":
        set_vip(update.effective_user.id, 1)
        await update.message.reply_text("تم تفعيل VIP بنجاح ⭐")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", send_vip_invoice))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("block", block_command))
    app.add_handler(CommandHandler("unblock", unblock_command))
    app.add_handler(CommandHandler("vipuser", vip_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
