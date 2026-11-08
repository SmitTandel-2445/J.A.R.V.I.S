import logging
from config import LOGS_DIR, LOG_FILE

# Ensure logs folder exists relative to project root
try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handlers = [file_handler, logging.StreamHandler()]
except OSError:
    handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=handlers
)

logger = logging.getLogger("JARVIS")