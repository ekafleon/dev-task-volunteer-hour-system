# -*- coding: utf-8 -*-

import sys
from src.db import init_db
from src.cli import main_menu


def main():
    init_db()  # 启动时确保表已建好
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