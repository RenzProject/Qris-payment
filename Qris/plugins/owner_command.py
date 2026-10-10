import sys
import os
import asyncio
import subprocess
from time import time
from hydrogram import filters
from Qris import bot
from Qris.database import *
from Qris.config import OWNER_ID

def restart():
    os.execvp(sys.executable, [sys.executable, "-m", "Qris"])

jakarta_timezone = pytz.timezone("Asia/Jakarta")
START_TIME = datetime.now(jakarta_timezone)

async def _human_time_duration(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d > 0:
        parts.append(f"{d}d")
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}m")
    if s > 0:
        parts.append(f"{s}s")
    return ", ".join(parts)

async def cancel(callback_query, text):
    if text.startswith("/"):
        await bot.send_message(
            callback_query.from_user.id,
            "<b>Proses di batalkan, silahkan coba lagi</b>",
        )
        return True
    else:
        return False
    
async def canceled(bt, callback_query, text):
    if text.startswith("/"):
        await bt.send_message(
            callback_query.from_user.id,
            "<b>Proses di batalkan, silahkan coba lagi</b>",
        )
        return True
    return False

@bot.on_message(filters.command("help"))
async def cmd_help(c, m):
    text = """
<b>📚 BANTUAN PERINTAH</b>

<b>💳 AKSES PREMIUM (OWNER)</b>
<code>/akses user_id fee</code> - Tambah akses premium
<code>/delakses user_id</code> - Hapus akses premium
<code>/listakses</code> - Lihat daftar akses premium

<b>💰 MANAJEMEN SALDO (USER)</b>
<code>/saldo</code> - Cek saldo pengguna
<code>/resetsaldo</code> - Reset saldo pengguna

<b>⚙️ LAINNYA</b>
<code>/ping</code> - Cek ping dan uptime bot
<code>/help</code> - Menampilkan bantuan ini
"""
    await m.reply(text)

@bot.on_message(filters.command("ping"))
async def cmd_ping(c, m):
    user_id = m.from_user.id
    start = time()

    current_time = datetime.now(jakarta_timezone)
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime_str = await _human_time_duration(int(uptime_sec))

    temp_msg = await c.send_message(user_id, "<b>Pinging...</b>")
    delta_ping = (time() - start) * 1000

    msg = f"""
<b>PONG!! 🏓</b>
<b>• Ping</b> - <code>{delta_ping:.2f} ms</code>
<b>• Uptime</b> - <code>{uptime_str}</code>
"""
    await temp_msg.edit(msg)

@bot.on_message(filters.command("uptime"))
async def cmd_uptime(c, m):
    user_id = m.from_user.id
    current_time = datetime.now(jakarta_timezone)
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime_str = await _human_time_duration(int(uptime_sec))

    start_time_str = START_TIME.strftime("%Y-%m-%d %H:%M:%S")

    msg = f"""
<b>🤖 Bot Status:</b>
<b>• Uptime:</b> <code>{uptime_str}</code>
<b>• Start Time:</b> <code>{start_time_str}</code>
"""
    await c.send_message(user_id, msg)

@bot.on_message(filters.command("restore") & filters.user(OWNER_ID))
async def cmd_restore(c, m):
    user_id = m.from_user.id

    try:
        db_path = DB_PATH

        msg = await c.ask(
            user_id,
            "<b>Silahkan kirim document file .db!! Dan pastikan nama db_name sesuai dengan config.py</b>",
            filters=filters.document,
        )

        if os.path.exists(db_path):
            os.remove(db_path)

        await c.download_media(msg.document, file_name=db_path)

        await m.reply(
            "<b>✅ Sukses melakukan restore database, silahkan ketik /restart</b>"
        )

    except Exception as e:
        await m.reply(
            f"<b>⛔ Gagal melakukan restore database:</b>\n<code>{str(e)}</code>"
        )

@bot.on_message(filters.command("gitpull") & filters.user(OWNER_ID))
async def cmd_gitpull(c, m):
    try:
        update_message = await m.reply_text("<b>🔄 Sedang memproses...</b>")
        out = subprocess.check_output(["git", "pull"]).decode("UTF-8")
        if "Already up to date." in str(out):
            return await update_message.edit_text("<b>🤖 BOT SUDAH VERSI TERBARU!</b>")
        await update_message.edit_text(f"<b>✅ BERHASIL UPDATE BOT</b>\n\n<code>{out}</code>")
        await restart()
    except Exception as e:
        await m.reply_text(
            f"<b>❌ Terjadi kesalahan saat melakukan pembaruan:</b>\n<code>{e}</code>"
        )

@bot.on_message(filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot(c, m):
    try:
        update_message = await m.reply_text("<b>🔄 Sedang memulai ulang bot...</b>",)
        await asyncio.sleep(1)
        await update_message.delete()
        await m.reply_text("<b>✅ BOT BERHASIL DIMULAI ULANG.</b>",)
        return await restart()
    except Exception as e:
        await m.reply_text(
            f"<b>❌ Terjadi kesalahan saat memulai ulang bot:</b>\n<code>{e}</code>",
        )