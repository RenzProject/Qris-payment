import asyncio
import qrcode
from io import BytesIO
from hydrogram import filters
from hydrogram.enums import ParseMode
from Qris import bot, logger
from Qris.utils import post
from Qris.config import LICENSE_KEY_CASAKU, ID_QRIS
from Qris.database import *

GENERATE_URL = "https://api.casaku.id/api/generate/v2/qris"
CHECK_STATUS_URL = "https://api.casaku.id/api/generate/check-status"

@bot.on_message(filters.command("qris") & filters.private)
async def cmd_qris(c, m):
    user_id = m.from_user.id

    if not await check_akses(user_id):
        return await m.reply(
            "<b>⚠️ Kamu tidak memiliki akses premium, Silahkan hubungi Owner.</b>",
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
        "expiredInMinutes": 10,
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

        await dB.add_transaksi(transaction_id, user_id, nominal)

        qr = qrcode.make(qr_string)

        buffer = BytesIO()
        buffer.name = "qris.png"

        qr.save(buffer, "PNG")
        buffer.seek(0)

        msg = f"""
<b>💳 Pembayaran QRIS Berhasil Dibuat</b>

<b>Detail Pembayaran:</b>
• ID : <code>{transaction_id}</code>
• Nominal : Rp{nominal:,}
• Total Bayar : Rp{total_amount:,}
• Status : ⏳ pending
• Expired : 10 menit

<b>Silakan scan QRIS di atas untuk melakukan pembayaran.</b>
""".replace(",", ".")

        await temp_msg.delete()

        payment_msg = await c.send_photo(
            chat_id=user_id,
            photo=buffer,
            caption=msg,
        )

        for _ in range(120):
            await asyncio.sleep(5)

            try:
                check_payload = {
                    "transactionId": transaction_id,
                }

                check = await post(CHECK_STATUS_URL, json=check_payload, headers=headers)

                logger.info(f"[QRIS] Check Status: {check}")

                if check.get("status") == 200:
                    status = check["data"]["status"]

                    if status == "paid":
                        transaksi = await dB.get_transaksi(transaction_id)

                        if transaksi["status"] != "paid":
                            fee = await dB.get_fee_user(user_id)
                            saldo_ditambahkan = nominal - fee

                            if saldo_ditambahkan < 0:
                                logger.warning("[QRIS] Fee melebihi nominal top up")
    
                            await dB.update_status_transaksi(transaction_id, "paid")

                        await payment_msg.delete()

                        msg_paid = f"""
<b>🔔 Pembayaran Berhasil!</b>

<b>Detail Transaksi:</b>
• ID : <code>{transaction_id}</code>
• Total Bayar : Rp{total_amount:,}
• Saldo Ditambahkan : Rp{nominal:,}
• Status : ✅ {status}

<blockquote>Terima kasih telah melakukan pembayaran. Saldo kamu berhasil ditambahkan.</blockquote>
""".replace(",", ".")

                        await c.send_message(user_id, msg_paid)
                        break

                    elif status in ("cancel", "expired"):
                        await dB.update_status_transaksi(transaction_id, status,)

                        await payment_msg.delete()

                        if status == "cancel":
                            title = "❌ Pembayaran QRIS Dibatalkan"
                        else:
                            title = "⌛ Pembayaran QRIS Kedaluwarsa"

                        msg_status = f"""
<b>{title}</b>

<b>Detail Transaksi:</b>
• ID : <code>{transaction_id}</code>
• Nominal : Rp{nominal:,}
• Status : <code>{status}</code>

Saldo kamu tidak ditambahkan.
""".replace(",", ".")

                        await c.send_message(user_id, msg_status)
                        break

            except Exception as e:
                logger.info(f"[QRIS] Error Check Status: {e}")

    except Exception as e:
        logger.info(f"[QRIS] Error Generate: {e}")
        await temp_msg.edit_text(
            "<b>❌ Terjadi kesalahan saat membuat pembayaran QRIS.</b>",
        )