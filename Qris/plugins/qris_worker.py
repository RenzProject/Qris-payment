import asyncio
from Qris.logger import logger
from Qris.database import dB
from Qris.utils import post
from Qris.config import (
    CHECK_STATUS_URL,
    LICENSE_KEY_CASAKU,
)

QRIS_WORKERS = 10
CHECK_INTERVAL = 5

queue: asyncio.Queue = asyncio.Queue()
in_flight: set = set()

def rp(angka: int) -> str:
    return f"{angka:,}".replace(",", ".")

async def proses_transaksi(c, trx, headers):
    transaction_id = trx["transaction_id"]
    user_id = trx["user_id"]
    nominal = trx["amount"]
    fee = trx["fee"]
    total_amount = trx["total_amount"]

    try:
        check = await post(
            CHECK_STATUS_URL,
            json={"transactionId": transaction_id},
            headers=headers,
        )
        if check.get("status") != 200:
            return
        status = check["data"]["status"]
    except Exception:
        return

    if status == "pending":
        return

    if status == "paid":
        saldo_ditambahkan = nominal - fee
        ok = await dB.settle_paid_transaksi(transaction_id, user_id, saldo_ditambahkan)
        if not ok:
            return
    elif status in ("cancel", "expired"):
        ok = await dB.update_status_transaksi(transaction_id, status, only_if="pending")
        if not ok:
            return
    else:
        return

    if trx.get("message_id"):
        try:
            await c.delete_messages(user_id, trx["message_id"])
        except Exception:
            pass

    if status == "paid":
        msg = f"""
<b>🔔 Pembayaran Berhasil!</b>

<b>Detail Transaksi:</b>
• ID: <code>{transaction_id}</code>
• Total Bayar: Rp{rp(total_amount)}
• Saldo Ditambahkan: Rp{rp(saldo_ditambahkan)}
• Status: ✅ paid

<blockquote>Terima kasih telah melakukan pembayaran. Saldo kamu berhasil ditambahkan.</blockquote>
"""
    else:
        title = (
            "❌ Pembayaran QRIS Dibatalkan"
            if status == "cancel"
            else "⌛ Pembayaran QRIS Kedaluwarsa"
        )
        msg = f"""
<b>{title}</b>

<b>Detail Transaksi:</b>
• ID: <code>{transaction_id}</code>
• Nominal: Rp{rp(nominal)}
• Status: <code>{status}</code>

Saldo kamu tidak ditambahkan.
"""

    try:
        await c.send_message(user_id, msg)
    except Exception as e:
        logger.info(f"[QRIS] Gagal kirim notif {transaction_id}: {e}")

async def qris_scheduler():
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            await dB.expire_transaksi_lama()

            pending = await dB.get_pending_transaksi()
            for trx in pending:
                tid = trx["transaction_id"]
                if tid in in_flight:
                    continue
                in_flight.add(tid)
                await queue.put(trx)
        except Exception as e:
            logger.info(f"[QRIS] Scheduler error: {e}")

async def qris_worker(c, headers):
    while True:
        trx = await queue.get()
        try:
            await proses_transaksi(c, trx, headers)
        except Exception as e:
            logger.info(f"[QRIS] Worker error: {e}")
        finally:
            in_flight.discard(trx["transaction_id"])
            queue.task_done()

async def start_qris(c):
    headers = {
        "x-license-key": LICENSE_KEY_CASAKU,
        "Content-Type": "application/json",
    }
    asyncio.create_task(qris_scheduler())
    for _ in range(QRIS_WORKERS):
        asyncio.create_task(qris_worker(c, headers))