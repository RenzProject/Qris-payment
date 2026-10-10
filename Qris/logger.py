import logging
from os import execvp
from sys import executable
from Qris.config import BOT_NAME

class ConnectionHandler(logging.Handler):
    def emit(self, record):
        for X in ["OSError"]:
            if X in record.getMessage():
                execvp(executable, [executable, "-m", "Qris"])

logger = logging.getLogger(BOT_NAME)
logger.setLevel(logging.INFO)
logger.propagate = False

if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter("[%(levelname)s] - %(name)s - %(message)s", "%d-%b %H:%M")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

connection_handler = ConnectionHandler()

logger.addHandler(stream_handler)
logger.addHandler(connection_handler)

logging.getLogger("hydrogram").setLevel(logging.WARNING)
logging.getLogger("hydrogram.client").setLevel(logging.WARNING)
logging.getLogger("hydrogram.session.auth").setLevel(logging.CRITICAL)
logging.getLogger("hydrogram.session.session").setLevel(logging.CRITICAL)

LOGS = logging.getLogger(__name__)

def LOGGER(name: str) -> logging.Logger:
    child = logging.getLogger(f"{BOT_NAME} - {name}")
    child.propagate = False
    return child