import asyncio
import qrcode
from io import BytesIO
from hydrogram import filters
from Qris import logger
from Qris.utils import Rz, BUTTON, TEXT
from Qris.config import LICENSE_KEY_CASAKU, ID_QRIS
from Qris.utils import post
from Qris.database import *

GENERATE_URL = "https://api.casaku.id/api/generate/v2/qris"
CHECK_STATUS_URL = "https://api.casaku.id/api/generate/check-status"

@Rz.callback(r"^gen_qris")
async def cb_gen_qris(c, q):
    user_id = q.from_user.id

    if not await check_akses(user_id):
        return await q.answer(
            "⚠️ Kamu tidak memiliki akses untuk menggunakan perintah ini.",
            show_alert=True,
        )

    try:
        response = await c.ask(
            user_id,
            text="Silahkan masukkan nominal QRIS yang ingin kamu dibuat. Contoh: 1500\n\n<i>Kirim /cancel untuk membatalkan proses</i>",
            filters=filters.private,
        )
    except asyncio.TimeoutError:
        return

    try:
        nominal = int(response.text)
    except (ValueError, AttributeError):
        return await c.send_message(
            user_id,
            "<b>❌ Nominal harus berupa angka.</b>",
        )

    if nominal < 1000:
        return await c.send_message(
            user_id,
            "<b>⚠️ Minimal nominal QRIS adalah Rp1.000.</b>",   
        )

    fee = await dB.get_fee_user(user_id)
    if nominal <= fee:
        fee_str = f"{fee:,}".replace(",", ".")
        return await c.send_message(
            user_id,
            f"<b>⚠️ Nominal QRIS terlalu kecil!</b>\n\nNominal harus lebih besar dari fee kamu yaitu <b>Rp{fee_str}</b>."
        )

    temp_msg = await c.send_message(
        user_id,
        "<b>⏳ Sedang membuat QRIS dinamis...</b>",
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
        data = await post(
            GENERATE_URL,
            json=payload,
            headers=headers,
        )

        if data.get("status") != 200:
            return await temp_msg.edit_text(
                "<b>❌ Gagal membuat pembayaran QRIS.</b>",
                
            )

        logger.info(f"[QRIS] Response API: {data}")

        result = data["data"]
        qr_string = result["qr_string"]
        transaction_id = result["transactionId"]
        total_amount = result["totalAmount"]

        await dB.add_transaksi(
            transaction_id,
            user_id,
            nominal,
        )

        qr = qrcode.make(qr_string)

        buffer = BytesIO()
        buffer.name = "qris.png"
        qr.save(buffer, "PNG")
        buffer.seek(0)

        msg = f"""
<b>💳 Pembayaran QRIS Berhasil Dibuat</b>

<b>Detail Pembayaran:</b>
• ID: <code>{transaction_id}</code>
• Nominal: Rp{nominal:,}
• Total Bayar: Rp{total_amount:,}
• Status: ⏳ pending
• Kedaluwarsa: 60 menit

<b>Silakan scan QRIS di atas untuk melakukan pembayaran.</b>
""".replace(",", ".")

        await temp_msg.delete()

        payment_msg = await c.send_photo(
            chat_id=user_id,
            photo=buffer,
            caption=msg,
        )

        for _ in range(720):
            await asyncio.sleep(5)

            try:
                check = await post(
                    CHECK_STATUS_URL,
                    json={"transactionId": transaction_id},
                    headers=headers,
                )

                logger.info(f"[QRIS] Check Status: {check}")

                if check.get("status") != 200:
                    continue

                status = check["data"]["status"]

                if status == "paid":
                    transaksi = await dB.get_transaksi(transaction_id)

                    if transaksi and transaksi["status"] != "paid":
                        saldo_ditambahkan = nominal - fee
                        await dB.add_saldo_user(user_id, saldo_ditambahkan)
                        await dB.update_status_transaksi(transaction_id, "paid")

                    await payment_msg.delete()

                    msg_paid = f"""
<b>🔔 Pembayaran Berhasil!</b>

<b>Detail Transaksi:</b>
• ID: <code>{transaction_id}</code>
• Total Bayar: Rp{total_amount:,}
• Saldo Ditambahkan: Rp{nominal:,}
• Status: ✅ paid

<blockquote>Terima kasih telah melakukan pembayaran. Saldo kamu berhasil ditambahkan.</blockquote>
""".replace(",", ".")

                    await c.send_message(user_id, msg_paid)
                    break

                elif status in ("cancel", "expired"):
                    await dB.update_status_transaksi(transaction_id,status)

                    await payment_msg.delete()

                    if status == "cancel":
                        title = "❌ Pembayaran QRIS Dibatalkan"
                    else:
                        title = "⌛ Pembayaran QRIS Kedaluwarsa"

                    msg_status = f"""
<b>{title}</b>

<b>Detail Transaksi:</b>
• ID: <code>{transaction_id}</code>
• Nominal: Rp{nominal:,}
• Status: <code>{status}</code>

Saldo kamu tidak ditambahkan.
""".replace(",", ".")

                    await c.send_message(user_id, msg_status)
                    break

            except Exception as e:
                logger.info(f"[QRIS] Error Check Status: {e}")

        else:
            await payment_msg.delete()

    except Exception as e:
        logger.info(f"[QRIS] Error Generate: {e}")

        try:
            await temp_msg.edit_text(
                "<b>❌ Terjadi kesalahan saat membuat pembayaran QRIS.</b>",
            )
        except Exception:
            pass

@Rz.callback(r"^history")
async def cb_history(c, q):
    user_id = q.from_user.id
    
    transactions = await get_transaksi_user_id(user_id)

    if not transactions:
        text = """
<b>📜 RIWAYAT TRANSAKSI</b>

Kamu belum memiliki riwayat transaksi.
"""
        return await q.edit_message_text(
            text=text,
            reply_markup=BUTTON.back_to_start(),
        )

    msg = "<b>📜 RIWAYAT TRANSAKSI</b>\n\n"

    for idx, trx in enumerate(transactions, start=1):
        status = trx["status"].upper()

        msg += f"""<blockquote><b>🧾 Transaksi #{idx} • {status}</b>

🆔 ID: <code>{trx['transaction_id']}</code>
💰 Nominal: <b>Rp{trx['amount']:,}</b>
📅 Tanggal: <code>{trx['updated_at']}</code>
</blockquote>\n
"""

    await q.edit_message_text(
        text=msg,
        reply_markup=BUTTON.back_to_start(),
    )

@Rz.callback(r"^total_pendapatan")
async def cb_total_pendapatan(c, q):
    user_id = q.from_user.id

    transaksi = await all_transaksi()
    transaksi = [trx for trx in transaksi if trx["user_id"] == user_id]

    total_success = sum(trx["status"] == "paid" for trx in transaksi)
    total_cancel = sum(trx["status"] == "cancel" for trx in transaksi)
    total_saldo = await get_saldo_user(user_id)

    text = f"""
<b>📊 STATISTIK PENDAPATAN</b>

<blockquote>🧾 Total Transaksi: <b>{len(transaksi)}</b>
✅ Total Success: <b>{total_success}</b>
❌ Total Cancel: <b>{total_cancel}</b>
💰 Total Saldo: <b>Rp{total_saldo:,}</b>
</blockquote>
"""

    await q.edit_message_text(
        text=text,
        reply_markup=BUTTON.back_to_start(),
    )

@Rz.callback(r"^back_start")
async def cb_back_start(c, q):
    username = q.from_user.mention
    bot_name = c.me.mention

    keyboard = BUTTON.start()
    welcome_msg = TEXT.start_msg(username, bot_name)

    await q.edit_message_text(
        text=welcome_msg,
        reply_markup=keyboard
    )