import qrcode
from io import BytesIO
from hydrogram import filters
from hydrogram.enums import ParseMode
from Qris import bot, logger
from Qris.utils import post
from Qris.config import (
    GENERATE_URL,
    ID_QRIS,
    LICENSE_KEY_CASAKU,
)
from Qris.database import *

@bot.on_message(filters.command("qris") & filters.private)
async def cmd_qris(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses untuk menggunakan perintah ini.</b>",
        )

    if len(m.command) < 2:
        return await m.reply(
            "<b>⚠️ Format salah, gunakan format:</b>\n\n<code>/qris nominal</code>"
        )

    try:
        nominal = int(m.command[1])
    except ValueError:
        return await m.reply(
            "<b>❌ Nominal harus berupa angka.</b>",
        )

    if nominal < 1000:
        return await m.reply(
            "<b>⚠️ Minimal nominal QRIS adalah <code>1000</code>.</b>"
        )

    fee = await dB.get_fee_user(user_id)
    if nominal <= fee:
        fee_str = f"{fee:,}".replace(",", ".")
        return await c.send_message(
            user_id,
            f"<b>⚠️ Nominal QRIS terlalu kecil!</b>\n\nNominal harus lebih besar dari fee kamu yaitu <b>Rp{fee_str}</b>."
        )

    temp_msg = await m.reply(
        "<b>⏳ Sedang membuat QRIS dinamis...</b>",
        parse_mode=ParseMode.HTML,
    )

    headers = {
        "x-license-key": LICENSE_KEY_CASAKU,
        "Content-Type": "application/json",
    }

    payload = {
        "qr_id": ID_QRIS,
        "amount": nominal,
        "useUniqueCode": True,
        "packageIds": ["id.dana"],
        "expiredInMinutes": 60,
        "qrType": "dynamic",
        "paymentMethod": "qris",
        "useQris": True,
        "prefix": "CSK",
    }

    try:
        data = await post(GENERATE_URL, json=payload, headers=headers)
        if data.get("status") != 200:
            return await temp_msg.edit_text(
                "<b>❌ Gagal membuat pembayaran Qris.</b>",
            )

        logger.info(f"[QRIS] Response API: {data}")

        result = data["data"]
        qr_string = result["qr_string"]
        transaction_id = result["transactionId"]
        total_amount = result["totalAmount"]

        qr = qrcode.make(qr_string)

        buffer = BytesIO()
        buffer.name = "qris.png"

        qr.save(buffer, "PNG")
        buffer.seek(0)

        msg = f"""
<b>💳 Pembayaran QRIS Berhasil Dibuat</b>

<b>Detail Pembayaran:</b>
• Nominal : Rp{nominal:,}
• Total Bayar : Rp{total_amount:,}
• Expired : 60 menit

<b>Silakan scan QRIS di atas untuk melakukan pembayaran.</b>
""".replace(",", ".")

        await temp_msg.delete()

        payment_msg = await c.send_photo(
            chat_id=user_id,
            photo=buffer,
            caption=msg,
        )

        await dB.add_transaksi(
            transaction_id,
            user_id,
            nominal,
            fee=fee,
            total_amount=total_amount,
            message_id=payment_msg.id,
        )

    except Exception as e:
        logger.info(f"[QRIS] Error Generate: {e}")
        try:
            await temp_msg.edit_text(
                "<b>❌ Terjadi kesalahan saat membuat pembayaran QRIS.</b>",
            )
        except Exception:
            pass