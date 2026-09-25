from telegram import LabeledPrice

VIP_PRICE_STARS = 100

async def send_vip_invoice(update, context):
    await update.message.reply_invoice(
        title="اشتراك VIP",
        description="تحميلات غير محدودة حسب حدود Telegram والمنصات",
        payload="vip_subscription",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice("VIP", VIP_PRICE_STARS)],
    )
