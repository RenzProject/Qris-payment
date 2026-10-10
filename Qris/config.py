import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ID = int(BOT_TOKEN.split(":")[0])
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
DB_NAME = os.environ.get("DB_NAME", "Autopaymentrenz")
BOT_NAME = os.environ.get("BOT_NAME", "PAYMENT-RENZ")
OWNER_ID = int(os.getenv("OWNER_ID", "6009049084"))
LOG_GRP = int(os.environ.get("LOG_GRP", "-100"))
ID_QRIS = os.environ.get("ID_QRIS")
LICENSE_KEY_CASAKU = os.environ.get("LICENSE_KEY_CASAKU")