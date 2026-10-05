# src/colors.py
"""终端彩色输出。Windows 下自动启用 ANSI。"""

import os
import unicodedata

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

def display_width(text):
    """计算字符串在终端里的显示宽度。中文算 2，英文算 1。"""
    width = 0
    for ch in str(text):
        if unicodedata.east_asian_width(ch) in ("F", "W"):
            width += 2
        else:
            width += 1
    return width


def pad(text, width, align="left"):
    """按显示宽度补齐字符串。

    :param text: 要补齐的内容
    :param width: 目标显示宽度
    :param align: 'left' 左对齐，'right' 右对齐，'center' 居中
    """
    text = str(text)
    current = display_width(text)
    if current >= width:
        return text
    space = width - current
    if align == "right":
        return " " * space + text
    if align == "center":
        left = space // 2
        right = space - left
        return " " * left + text + " " * right
    return text + " " * space
