from database import stats, set_blocked, set_vip

def is_admin(user_id: int) -> bool:
    import os
    return user_id == int(os.getenv("ADMIN_ID", "0"))

async def admin_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("ليس لديك صلاحية.")
        return
    row = stats()
    await update.message.reply_text(
        f"📊 الإحصائيات\nالمستخدمون: {row['total']}\n"
        f"VIP: {row['vip']}\nالمحظورون: {row['blocked']}"
    )

async def block_command(update, context):
    if not is_admin(update.effective_user.id) or not context.args:
        return
    set_blocked(int(context.args[0]), 1)
    await update.message.reply_text("تم الحظر.")

async def unblock_command(update, context):
    if not is_admin(update.effective_user.id) or not context.args:
        return
    set_blocked(int(context.args[0]), 0)
    await update.message.reply_text("تم فك الحظر.")

async def vip_command(update, context):
    if not is_admin(update.effective_user.id) or not context.args:
        return
    set_vip(int(context.args[0]), 1)
    await update.message.reply_text("تم تفعيل VIP.")
