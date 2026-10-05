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
    """按显示宽度补齐字符串。"""
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
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg="\n按回车返回..."):
    input(msg)


def paginate(items, page_size=15, printer=print, headers=None):
    """分页打印列表。每页重复打印 headers。

    items: 可迭代对象
    page_size: 每页条数，传很大的值可禁用分页
    printer: 打印单条的回调
    headers: 表头行列表，每页开始前逐行打印
    """
    items = list(items)
    total = len(items)
    if total == 0:
        return

    for start in range(0, total, page_size):
        end = min(start + page_size, total)

        if headers:
            for line in headers:
                print(line)

        for item in items[start:end]:
            printer(item)

        if end < total:
            print()
            input(f"  -- 已显示 {end}/{total}，按回车继续 --")
            print()
        else:
            print(f"  -- 共 {total} 条 --")