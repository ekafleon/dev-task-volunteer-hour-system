# src/config.py
"""项目配置模块。

定义项目根目录、数据库文件路径，并确保数据目录存在。
支持通过环境变量 APP_DB_PATH 覆盖默认数据库路径。
"""

import os
from pathlib import Path

# 项目根目录（src 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库文件路径，优先使用环境变量 APP_DB_PATH
DB_PATH = Path(os.environ.get("APP_DB_PATH", BASE_DIR / "data" / "app.db"))

# 确保数据库所在目录存在
DB_PATH.parent.mkdir(parents=True, exist_ok=True)