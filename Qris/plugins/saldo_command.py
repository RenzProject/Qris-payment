from hydrogram import filters
from Qris import bot
from Qris.database import *

@bot.on_message(filters.command("saldo") & filters.private)
async def cmd_saldo(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses premium, Silahkan hubungi Owner.</b>"
        )

    saldo = await get_saldo_user(user_id)

    await m.reply(
        f"<b>💰 Saldo kamu saat ini:</b> <code>Rp{saldo:,}</code>"
    )

@bot.on_message(filters.command("resetsaldo") & filters.private)
async def cmd_resetsaldo(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses premium, Silahkan hubungi Owner.</b>",
        )

    await reset_saldo_user(user_id)

    await m.reply(
        "<b>✅ Saldo kamu berhasil direset menjadi Rp0.</b>",
    )