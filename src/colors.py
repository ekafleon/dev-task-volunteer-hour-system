# src/colors.py
"""终端彩色输出。Windows 下自动启用 ANSI。"""

import os

# Windows 10+ 启用 ANSI
if os.name == "nt":
    os.system("")

RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"


def success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def error(text):
    print(f"{RED}✗ {text}{RESET}")


def warn(text):
    print(f"{YELLOW}! {text}{RESET}")


def info(text):
    print(f"{BLUE}ℹ {text}{RESET}")


def bold(text):
    return f"{BOLD}{text}{RESET}"