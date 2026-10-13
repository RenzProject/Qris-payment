import importlib
from sys import version as pyver
import asyncio
from datetime import datetime
from pathlib import Path
import traceback
from pytz import timezone
from croniter import croniter
from hydrogram import __version__ as hydrover
from hydrogram import idle
from Qris import LOOP, bot
from Qris.config import OWNER_ID
from Qris.logger import logger
from Qris.plugins import loadModule
from Qris.database import *

global_task = []

async def auto_backup():
    tz = timezone("Asia/Jakarta")
    cron = croniter("0 0 * * *", datetime.now(tz))
    while True:
        next_run = cron.get_next(datetime)
        wait_time = (next_run - datetime.now(tz)).total_seconds()
        logger.info(f"Scheduled backup in {wait_time} seconds.")
        await asyncio.sleep(wait_time)

        try:
            await dB.checkpoint()
            archive_full_path = await dB.backup_database()

            if archive_full_path:
                backup_path = Path(archive_full_path)

                await bot.send_document(OWNER_ID, str(backup_path))
                logger.info(f"✅ Backup database berhasil dan dikirim ke OWNER_ID: {backup_path}")

                try:
                    backup_path.unlink(missing_ok=True)
                    logger.info(f"🗑️ File backup lokal berhasil dibersihkan: {backup_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Gagal hapus file backup lokal {backup_path}: {e}")

            else:
                logger.warning("⚠️ Backup gagal dibuat, file tidak ditemukan!")

        except Exception as e:
            logger.error(f"❌ Gagal melakukan auto-backup database: {e}")
            continue

async def start_task():
    global global_task

    background_tasks = [auto_backup()]
    for task in background_tasks:
        t = asyncio.create_task(task)
        global_task.append(t)
    logger.info(f"Started {len(background_tasks)} background tasks")

async def start_bots():
    await dB.initialize()
    await bot.start()

    for mod in loadModule():
        importlib.import_module(f"Qris.plugins.{mod}")

    logger.info(f"[🤖 @{bot.me.username} 🤖] [🔥 BERHASIL DIAKTIFKAN! 🔥]")

    try:
        msg = """
**Berhasil Di Aktifkan**
**Python Version** `{}`
**hydrogram Version** `{}`
        """
        await bot.send_message(OWNER_ID, msg.format(pyver.split()[0], hydrover))
        logger.info(f"Pesan berhasil dikirim ke {OWNER_ID}")
    except Exception as e:
        logger.error(f"Error saat mengirim pesan ke OWNER: {e}")

async def stop_main():
    logger.info(f"📌 Total task yang akan dihentikan: {len(global_task)}")

    if global_task:
        for task in global_task:
            if not task.done():
                task.cancel()

        await asyncio.sleep(1)

        for task in global_task:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5)
            except asyncio.TimeoutError:
                logger.error(f"⏳ Timeout saat menghentikan task: {task.get_name() or task}")
            except asyncio.CancelledError:
                continue
            except Exception as e:
                logger.error(f"⚠️ Task {task.get_name() or task} mengalami error: {e}")

    logger.info("⚠️ Menutup koneksi database dan menghentikan bot...")
    try:
        await dB.close()
    except Exception as e:
        logger.error(f"Error saat menutup database: {e}")

    try:
        await bot.stop()
    except Exception as e:
        logger.error(f"Error saat menghentikan bot: {e}")

    logger.info("✅ Semua task berhasil dihentikan dan database telah ditutup.")

async def main():
    try:
        await start_bots()
        await start_task()
        await idle()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.warning("Stopped All.")
    except Exception:
        logger.error(f"⚠️ Terjadi kesalahan tak terduga:\n{traceback.format_exc()}")
    finally:
        await stop_main()

if __name__ == "__main__":
    LOOP.run_until_complete(main())