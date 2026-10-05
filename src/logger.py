# src/logger.py
"""日志系统，写入 logs/app.log"""

import logging
from pathlib import Path

from src.config import BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(module)s] %(message)s",
    encoding="utf-8",
)

logger = logging.getLogger("task_system")
