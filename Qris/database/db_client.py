
import aiosqlite
import aioshutil
import pytz

from pathlib import Path
from datetime import datetime

from Qris.config import DB_NAME
from Qris.logger import logger


JAKARTA_TIMEZONE = pytz.timezone("Asia/Jakarta")

DATA_DIR = Path("./data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / f"{DB_NAME}.db"
ENV_PATH = Path("./.env")
TEMP_DIR = DB_PATH.parent / "output"


class DatabaseClient:
    def __init__(self) -> None:
        self.db_path = DB_PATH
        self.env_path = ENV_PATH
        self.db_backup_format = "zip"
        self.temp_dir = TEMP_DIR
        self.conn = None

        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        await self.connect()
        await self._initialize_database()

    async def connect(self):
        if self.conn is not None:
            return

        self.conn = await aiosqlite.connect(
            self.db_path,
            timeout=30,
            check_same_thread=False
        )

        self.conn.row_factory = aiosqlite.Row

        await self.conn.execute("PRAGMA journal_mode=WAL;")
        await self.conn.execute("PRAGMA synchronous=NORMAL;")
        await self.conn.execute("PRAGMA busy_timeout=30000;")
        await self.conn.execute("PRAGMA foreign_keys=ON;")
        await self.conn.execute("PRAGMA temp_store=MEMORY;")
        await self.conn.execute("PRAGMA cache_size=-32000;")

        await self.conn.commit()

        logger.info(f"Database connected to -> {self.db_path}")
        logger.info("SQLite WAL mode enabled")

    async def _initialize_database(self):
        query = """
        CREATE TABLE IF NOT EXISTS akses (
            user_id INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS broadcast (
            user_id INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS saldo_user (
            user_id INTEGER PRIMARY KEY,
            saldo INTEGER NOT NULL DEFAULT 0,
            fee INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_transaksi_user_id
        ON transaksi(user_id);

        CREATE INDEX IF NOT EXISTS idx_transaksi_status
        ON transaksi(status);
        """

        await self.conn.executescript(query)
        await self.conn.commit()

        logger.info("Database schema initialized")

    async def ensure_connection(self):
        if self.conn is None:
            await self.connect()

    # AKSES MANAGEMENT
    async def add_akses(self, user_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR REPLACE INTO akses (user_id)
                VALUES (?)
                """,
                (user_id,)
            )

        await self.conn.commit()

    async def get_akses(self, user_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM akses WHERE user_id = ?",
                (user_id,)
            )

            return await cursor.fetchone()

    async def all_akses(self):
        await self.ensure_connection()

        akses = []

        async with self.conn.execute(
            "SELECT * FROM akses"
        ) as cursor:
            async for row in cursor:
                akses.append({
                    "user_id": row["user_id"]
                })

        return akses

    async def remove_akses(self, user_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM akses WHERE user_id = ?",
                (user_id,)
            )

        await self.conn.commit()

    # BROADCAST USERS MANAGEMENT
    async def add_broadcast(self, user_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT OR IGNORE INTO broadcast (user_id)
                VALUES (?)
                """,
                (user_id,)
            )

        await self.conn.commit()

    async def get_broadcast(self, user_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM broadcast WHERE user_id = ?
                """,
                (user_id,)
            )

            return await cursor.fetchone()

    async def all_broadcast(self):
        await self.ensure_connection()

        users = []

        async with self.conn.execute(
            "SELECT * FROM broadcast"
        ) as cursor:
            async for row in cursor:
                users.append({
                    "user_id": row["user_id"]
                })

        return users

    async def remove_broadcast_user(self, user_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM broadcast WHERE user_id = ?",
                (user_id,)
            )

        await self.conn.commit()

    # TRANSAKSI MANAGEMENT
    async def add_transaksi(self, transaction_id, user_id, amount):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO transaksi (transaction_id, user_id, amount, status)
                VALUES (?, ?, ?, 'pending')
                """,
                (transaction_id, user_id, amount)
            )

        await self.conn.commit()

    async def get_transaksi(self, transaction_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                SELECT * FROM transaksi WHERE transaction_id = ?
                """,
                (transaction_id,)
            )

            return await cursor.fetchone()

    async def get_transaksi_user_id(self, user_id):
        await self.ensure_connection()
        transaksi = []

        async with self.conn.execute(
            "SELECT * FROM transaksi WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        ) as cursor:
            async for row in cursor:
                transaksi.append({
                    "id": row["id"],
                    "transaction_id": row["transaction_id"],
                    "user_id": row["user_id"],
                    "amount": row["amount"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                })

        return transaksi

    async def all_transaksi(self):
        await self.ensure_connection()
        transaksi = []

        async with self.conn.execute(
            "SELECT * FROM transaksi ORDER BY id DESC"
        ) as cursor:
            async for row in cursor:
                transaksi.append({
                    "id": row["id"],
                    "transaction_id": row["transaction_id"],
                    "user_id": row["user_id"],
                    "amount": row["amount"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                })

        return transaksi

    async def update_status_transaksi(self, transaction_id, status):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                UPDATE transaksi
                SET status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE transaction_id = ?
                """,
                (status, transaction_id)
            )

        await self.conn.commit()

    async def remove_transaksi_user_id(self, user_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM transaksi WHERE user_id = ?
                """,
                (user_id,)
            )

        await self.conn.commit()

    async def remove_transaksi(self, transaction_id):
        await self.ensure_connection()

        async with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                DELETE FROM transaksi WHERE transaction_id = ?
                """,
                (transaction_id,)
            )

        await self.conn.commit()

    # SALDO MANAGEMENT
    async def add_saldo_user(self, user_id, amount=0):
        await self.ensure_connection()

        async with self.conn.execute(
            """
            INSERT INTO saldo_user (user_id, saldo)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                saldo = saldo + excluded.saldo,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, amount)
        ):
            pass

        await self.conn.commit()

    async def get_saldo_user(self, user_id):
        await self.ensure_connection()

        async with self.conn.execute(
            """
            SELECT saldo FROM saldo_user WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

        return row["saldo"] if row else 0

    async def get_all_saldo_user(self):
        await self.ensure_connection()

        users = []

        async with self.conn.execute(
            """
            SELECT * FROM saldo_user
            ORDER BY user_id ASC
            """
        ) as cursor:
            async for row in cursor:
                users.append({
                    "user_id": row["user_id"],
                    "saldo": row["saldo"],
                    "fee": row["fee"]
                })
        return users

    async def reset_saldo_user(self, user_id):
        await self.ensure_connection()

        async with self.conn.execute(
            """
            INSERT INTO saldo_user (user_id, saldo)
            VALUES (?, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                saldo = 0,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id,)
        ):
            pass

        await self.conn.commit()

    # FEE USER MANAGEMENT
    async def set_fee_user(self, user_id, fee):
        await self.ensure_connection()

        if fee < 0:
            raise ValueError("Fee tidak boleh negatif")

        async with self.conn.execute(
            """
            INSERT INTO saldo_user (user_id, saldo, fee)
            VALUES (?, 0, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                fee = excluded.fee,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, fee)
        ):
            pass

        await self.conn.commit()

    async def get_fee_user(self, user_id):
        await self.ensure_connection()

        async with self.conn.execute(
            """
            SELECT fee FROM saldo_user WHERE user_id = ?
            """,
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

        return row["fee"] if row else 0

    # BACKUP DATABASE
    async def backup_database(self):
        await self.ensure_connection()

        db_file = Path(self.db_path)
        env_file = Path(self.env_path)

        if not db_file.exists():
            logger.warning(f"File {self.db_path} tidak ditemukan!")
            return None

        backup_time = datetime.now(JAKARTA_TIMEZONE).strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"./{DB_NAME}_backup_{backup_time}")

        self.temp_dir.mkdir(parents=True, exist_ok=True)

        temp_db_file = self.temp_dir / db_file.name

        async with aiosqlite.connect(temp_db_file) as backup_conn:
            await self.conn.backup(backup_conn)
            await backup_conn.commit()

        logger.info(
            f"Database backup sementara dibuat: {temp_db_file}"
        )

        if env_file.exists():
            temp_env_file = self.temp_dir / env_file.name

            await aioshutil.copy(env_file, temp_env_file)

            logger.info(f"File .env ikut dibackup: {temp_env_file}")

        archive_full_path = await aioshutil.make_archive(
            str(backup_path),
            self.db_backup_format,
            self.temp_dir
        )

        await aioshutil.rmtree(self.temp_dir, ignore_errors=True)

        logger.info(f"Arsip berhasil dibuat: {archive_full_path}")

        return archive_full_path

    # SQLITE WAL CHECKPOINT
    async def checkpoint(self):
        await self.ensure_connection()

        try:
            await self.conn.execute(
                "PRAGMA wal_checkpoint(TRUNCATE);"
            )

            await self.conn.commit()

            logger.info("SQLite WAL checkpoint selesai")

        except Exception as e:
            logger.error(
                f"SQLite WAL checkpoint gagal: {e}"
            )

    # CLOSE DATABASE
    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

        logger.info("Database connection closed")

dB = DatabaseClient()