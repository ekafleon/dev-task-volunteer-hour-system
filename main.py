# -*- coding: utf-8 -*-

import sys

from src.cli import main_menu
from src.db import init_db


def main():
    init_db()
    if "--gui" in sys.argv:
        try:
            from src.gui import launch
            launch()
        except ImportError as e:
            print(f"GUI 启动失败，回退 CLI：{e}")
            main_menu()
    else:
        main_menu()


if __name__ == "__main__":
    main()
