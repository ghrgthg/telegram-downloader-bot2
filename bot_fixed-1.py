import os
from pathlib import Path
from fastapi import FastAPI
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, PreCheckoutQueryHandler, ContextTypes, filters
from database import init_db, save_user, get_user, can_download, increase_free_used, set_vip
from downloader import download_media
from tasks import show_tasks
from payments import send_vip_invoice
from admin import admin_command, block_command, unblock_command, vip_command

TOKEN = os.environ["BOT_TOKEN"]
api = FastAPI()

@api.get("/")
async def home():
    return {"status": "online", "bot": "telegram-downloader"}

def main_keyboard(user_id: int):
    buttons = [["🎬 تحميل فيديو", "🎵 تحميل صوت"], ["💰 رصيدي", "🎯 المهام"]]
    if user_id == int(os.getenv("ADMIN_ID", "0")):
        buttons.append(["⚙️ لوحة التحكم"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, is_persistent=True)

def inline_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ VIP", callback_data="vip"), InlineKeyboardButton("🎯 المهام", callback_data="tasks")],
        [InlineKeyboardButton("🎵 صوت فقط", callback_data="audio")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    context.user_data["audio_only"] = False
    await update.message.reply_text("مرحبًا بك في بوت تحميل الفيديوهات 🤖\nاختر الخدمة من الأزرار التالية:", reply_markup=main_keyboard(update.effective_user.id))

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

async def show_balance(update: Update):
    row = get_user(update.effective_user.id)
    if not row:
        await update.message.reply_text("لم يتم العثور على حسابك. اضغط /start.")
        return
    if row["vip"]:
        text = "💎 حالتك: VIP\n✅ التحميلات المجانية غير محدودة حسب حدود الخدمة."
    else:
        text = f"💰 رصيدك\n\nالتحميلات المجانية المتبقية: {max(0, 3 - row['free_used'])}\n⭐ للترقية استخدم /vip"
    await update.message.reply_text(text, reply_markup=main_keyboard(update.effective_user.id))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if text == "🎬 تحميل فيديو":
        context.user_data["audio_only"] = False
        await update.message.reply_text("أرسل رابط الفيديو الآن.")
        return
    if text == "🎵 تحميل صوت":
        context.user_data["audio_only"] = True
        await update.message.reply_text("أرسل رابط الفيديو لتحويله إلى صوت MP3.")
        return
    if text == "💰 رصيدي":
        await show_balance(update)
        return
    if text == "🎯 المهام":
        await show_tasks(update, context)
        return
    if text == "⚙️ لوحة التحكم":
        await admin_command(update, context)
        return
    await handle_link(update, context)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(update.effective_user)
    if not can_download(user_id):
        await update.message.reply_text("انتهت تحميلاتك المجانية. استخدم /vip أو 🎯 المهام.", reply_markup=main_keyboard(user_id))
        return
    url = update.message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("أرسل رابطًا صحيحًا يبدأ بـ http أو https.")
        return
    audio_only = bool(context.user_data.pop("audio_only", False))
    await update.message.reply_text("⏳ جاري التحميل...")
    path = None
    try:
        path = await download_media(url, audio_only)
        if not path or not Path(path).exists():
            raise RuntimeError("لم يتم العثور على الملف")
        with open(path, "rb") as media:
            if Path(path).suffix.lower() == ".mp3":
                await update.message.reply_audio(media)
            else:
                await update.message.reply_video(media)
        row = get_user(user_id)
        if row and not row["vip"]:
            increase_free_used(user_id)
    except Exception:
        await update.message.reply_text("تعذر التحميل. جرّب رابطًا آخر أو ملفًا أصغر.")
    finally:
        if path:
            file_path = Path(path)
            try:
                file_path.unlink(missing_ok=True)
                file_path.parent.rmdir()
            except OSError:
                pass

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if payment and payment.invoice_payload == "vip_subscription":
        set_vip(update.effective_user.id, 1)
        await update.message.reply_text("تم تفعيل VIP بنجاح ⭐", reply_markup=main_keyboard(update.effective_user.id))

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("vip", send_vip_invoice))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("block", block_command))
    application.add_handler(CommandHandler("unblock", unblock_command))
    application.add_handler(CommandHandler("vipuser", vip_command))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(PreCheckoutQueryHandler(precheckout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
