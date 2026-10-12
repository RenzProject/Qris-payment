from hydrogram import filters
from Qris import bot
from Qris.database import *

@bot.on_message(filters.command("addsaldo") & filters.private)
async def cmd_add_saldo(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses untuk menggunakan perintah ini.</b>"
        )

    args = m.text.split()
    if len(args) < 3:
        return await m.reply(
            "<b>⚠️ Format salah, gunakan format:</b>\n\n<code>/addsaldo user_id nominal</code>"
        )

    try:
        user_id = int(args[1])
        nominal = int(args[2])
    except ValueError:
        return await m.reply(
            "<b>❌ User ID dan Nominal harus berupa angka!</b>"
        )

    if nominal <= 0:
        return await m.reply(
            "<b>⚠️ Nominal penambahan saldo harus lebih besar dari 0.</b>"
        )

    await add_saldo_user(user_id, nominal)
    saldo_terkini = await get_saldo_user(user_id)

    saldo_str = f"{saldo_terkini:,}".replace(",", ".")

    await m.reply(
        f"<b>✅ Berhasil Menambahkan Saldo!</b>\n\n- User ID: <code>{user_id}</code>\n- Saldo Sekarang: <code>Rp{saldo_str}</code>"
    )

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