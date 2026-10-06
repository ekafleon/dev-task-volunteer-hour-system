# src/logger.py
"""日志系统模块。

配置日志输出到 logs/app.log，包含时间、级别、模块名和消息。
提供全局 logger 对象供其他模块使用。
"""

import logging
from pathlib import Path

from src.config import BASE_DIR

# 日志目录
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志基本配置
logging.basicConfig(
    filename=LOG_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(module)s] %(message)s",
    encoding="utf-8",
)

# 全局 logger 实例
logger = logging.getLogger("task_system")