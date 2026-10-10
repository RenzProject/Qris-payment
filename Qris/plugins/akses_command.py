from hydrogram import filters
from Qris.database import *
from Qris.config import OWNER_ID
from Qris import bot

@bot.on_message(filters.command("akses") & filters.user(OWNER_ID))
async def cmd_akses(c, m):
    owner_id = m.from_user.id

    if len(m.command) < 3:
        return await m.reply(
            "<b>⚠️ Format salah, gunakan format:\n\n<code>/akses user_id fee</code></b>"
        )

    try:
        user_id = int(m.command[1])
        fee = float(m.command[2])
    except ValueError:
        return await m.reply(
            "<b>❌ User ID dan fee harus berupa angka.</b>"
        )

    if fee < 0:
        return await m.reply(
            "<b>❌ Fee tidak boleh kurang dari 0.</b>"
        )

    if await check_akses(user_id):
        return await m.reply(
            f"<b>⚠️ User <code>{user_id}</code> sudah memiliki akses premium.</b>"
        )

    await add_akses(user_id)
    await set_fee_user(user_id, fee)

    await c.send_message(
        owner_id,
        f"<b>✅ Akses premium berhasil ditambahkan.\n\n👤 User ID: <code>{user_id}</code>\n💰 Fee: <code>{fee:g}</code></b>"
    )

@bot.on_message(filters.command("listakses") & filters.user(OWNER_ID))
async def cmd_listakses(c, m):
    members = await all_akses()

    if not members:
        return await m.reply(
            "<b>📋 Belum ada member premium.</b>"
        )

    text = "<b>📋 Daftar Member Premium:</b>\n\n"

    for idx, akses in enumerate(members, start=1):
        user_id = akses["user_id"]
        fee = await get_fee_user(user_id)

        if fee is None:
            fee = 0

        text += f"{idx}. 👤 User ID: <code>{user_id}</code>\n💰 Fee: <code>{fee:g}</code>\n\n"

    text += f"<b>👥 Total Member: <code>{len(members)}</code></b>"

    await m.reply(text)

@bot.on_message(filters.command("delakses") & filters.user(OWNER_ID))
async def cmd_delakses(c, m):
    if len(m.command) < 2:
        return await m.reply(
            "<b>⚠️ Format salah, gunakan format:\n\n<code>/delakses user_id</code></b>"
        )

    try:
        user_id = int(m.command[1])
    except ValueError:
        return await m.reply(
            "<b>❌ User ID harus berupa angka.</b>"
        )

    if not await check_akses(user_id):
        return await m.reply(
            f"<b>⚠️ User <code>{user_id}</code> tidak terdaftar sebagai member premium.</b>"
        )

    await remove_akses(user_id)

    await m.reply(
        f"<b>✅ Akses premium user <code>{user_id}</code> berhasil dihapus.</b>"
    )