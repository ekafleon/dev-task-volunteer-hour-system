# -*- coding: utf-8 -*-

import sys

from src.db import init_db
from src.cli import main_menu
from src.logger import logger



def main():
    init_db()
    main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已退出")
    except Exception as e:
        logger.exception("未处理异常")
        print(f"出错了: {e}")
