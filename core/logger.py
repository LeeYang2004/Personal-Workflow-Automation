import os
import logging
from datetime import datetime, timedelta
from core.utils import get_log_path

_logger = None


def setup_logger():
    """
    Sets up a logger that writes to a daily log file and also outputs to the console.
    """
    LOG_DIR = get_log_path()
    global _logger

    if _logger:
        return _logger

    logger = logging.getLogger("workflow_logger")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        _logger = logger
        return logger

    file_path = _get_log_file_path(LOG_DIR)

    file_handler = logging.FileHandler(file_path, encoding="utf-8")

    # -------------------------
    # CONSOLE HANDLER (NEW)
    # -------------------------
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _cleanup_old_logs(LOG_DIR)

    _logger = logger
    return logger

def _get_log_file_path(LOG_DIR):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_DIR, f"{today}.log")

def _cleanup_old_logs(LOG_DIR):
    if not os.path.exists(LOG_DIR):
        return

    now = datetime.now()

    for file in os.listdir(LOG_DIR):
        file_path = os.path.join(LOG_DIR, file)

        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))

            if now - file_time > timedelta(days=30):
                os.remove(file_path)

logger = setup_logger()