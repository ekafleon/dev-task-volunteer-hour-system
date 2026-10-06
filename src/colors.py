# src/colors.py
"""终端彩色输出与显示工具。Windows 下自动启用 ANSI。"""

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
    """打印绿色成功信息，前缀 ✓。

    Args:
        text (str): 要显示的消息。
    """
    print(f"{GREEN}✓ {text}{RESET}")


def error(text):
    """打印红色错误信息，前缀 ✗。

    Args:
        text (str): 要显示的消息。
    """
    print(f"{RED}✗ {text}{RESET}")


def warn(text):
    """打印黄色警告信息，前缀 !。

    Args:
        text (str): 要显示的消息。
    """
    print(f"{YELLOW}! {text}{RESET}")


def info(text):
    """打印蓝色提示信息，前缀 ℹ。

    Args:
        text (str): 要显示的消息。
    """
    print(f"{BLUE}ℹ {text}{RESET}")


def bold(text):
    """返回加粗后的字符串（不直接打印）。

    Args:
        text (str): 原始文本。

    Returns:
        str: 带有 ANSI 加粗样式的字符串。
    """
    return f"{BOLD}{text}{RESET}"


def display_width(text):
    """计算字符串在终端中的显示宽度（中文算 2，英文算 1）。

    Args:
        text (str): 任意字符串。

    Returns:
        int: 显示宽度。
    """
    width = 0
    for ch in str(text):
        if unicodedata.east_asian_width(ch) in ("F", "W"):
            width += 2
        else:
            width += 1
    return width


def pad(text, width, align="left"):
    """按显示宽度补齐字符串。

    Args:
        text (str): 要补齐的内容。
        width (int): 目标显示宽度。
        align (str): 对齐方式，'left' 左对齐，'right' 右对齐，'center' 居中。

    Returns:
        str: 补齐后的字符串。
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


def clear():
    """清空终端屏幕。"""
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg="\n按回车返回..."):
    """暂停程序，等待用户按回车。

    Args:
        msg (str): 提示信息。
    """
    input(msg)