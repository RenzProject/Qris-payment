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
        f"<b>✅ Berhasil menambahkan saldo user!</b>\n\n- User ID: <code>{user_id}</code>\n- Saldo Sekarang: <code>Rp{saldo_str}</code>"
    )

@bot.on_message(filters.command("saldo") & filters.private)
async def cmd_saldo(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses untuk menggunakan perintah ini.</b>"
        )

    saldo = await get_saldo_user(user_id)

    await m.reply(
        f"<b>💰 Saldo kamu saat ini:</b> <code>Rp{saldo:,}</code>"
    )

@bot.on_message(filters.command("delsaldo") & filters.private)
async def cmd_del_saldo(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses untuk menggunakan perintah ini.</b>"
        )

    args = m.text.split()
    if len(args) < 3:
        return await m.reply(
            "<b>⚠️ Format salah, gunakan format:</b>\n\n<code>/delsaldo user_id nominal</code>"
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
            "<b>⚠️ Nominal pengurangan saldo harus lebih besar dari 0.</b>"
        )

    saldo_saat_ini = await get_saldo_user(user_id)
    if saldo_saat_ini < nominal:
        return await m.reply(
            f"<b>❌ Saldo user tidak mencukupi!</b>\n\Saldo saat ini: <code>Rp{saldo_saat_ini:,}</code>".replace(",", ".")
        )
    
    await add_saldo_user(user_id, -nominal)
    saldo_terkini = await get_saldo_user(user_id)
    saldo_str = f"{saldo_terkini:,}".replace(",", ".")

    await m.reply(
        f"<b>✅ Berhasil Mengurangi saldo user!</b>\n\n- User ID: <code>{user_id}</code>\n- Saldo sekarang: <code>Rp{saldo_str}</code>"
    )

@bot.on_message(filters.command("listsaldo") & filters.private)
async def cmd_list_saldo(c, m):
    user_id_pengirim = m.from_user.id

    if not await check_akses(user_id_pengirim):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses untuk menggunakan perintah ini.</b>"
        )

    users = await get_all_saldo_user()

    if not users:
        return await m.reply(
            "<b>📂 Belum ada data saldo user di database.</b>"
        )

    text_list = []
    for idx, u in enumerate(users, start=1):
        saldo_str = f"{u['saldo']:,}".replace(",", ".")
        text_list.append(f"{idx}. User ID: <code>{u['user_id']}</code>\n💰 Saldo: <code>Rp{saldo_str}</code>")

    daftar_user = "\n".join(text_list)
    pesan = f"<b>📋 Daftar Saldo Semua User:</b>\n\n{daftar_user}"

    if len(pesan) > 4096:
        for x in range(0, len(pesan), 4096):
            await m.reply(pesan[x:x+4096])
    else:
        await m.reply(pesan)

@bot.on_message(filters.command("resetsaldo") & filters.private)
async def cmd_resetsaldo(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses untuk menggunakan perintah ini.</b>",
        )

    await reset_saldo_user(user_id)

    await m.reply(
        "<b>✅ Saldo kamu berhasil direset menjadi Rp0.</b>",
    )