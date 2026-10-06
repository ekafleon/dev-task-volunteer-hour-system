# main.py
# -*- coding: utf-8 -*-
"""程序入口。

支持两种运行方式：
1. 默认启动命令行菜单。
2. 通过子命令直接执行特定操作（如 summary、add-member 等）。
"""

import argparse
import sys

from src.db import init_db
from src.logger import logger


def build_parser():
    """构建命令行参数解析器。

    Returns:
        argparse.ArgumentParser: 配置好的解析器。
    """
    parser = argparse.ArgumentParser(
        description="开发组任务登记及志愿时长分配系统"
    )
    parser.add_argument("--cli", action="store_true", help="启动菜单")

    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("summary", help="打印全体成员汇总")
    sub.add_parser("list-members", help="列出成员")
    sub.add_parser("list-tasks", help="列出任务")
    sub.add_parser("backup", help="备份数据库")
    sub.add_parser("export-summary", help="导出汇总 CSV")

    p = sub.add_parser("add-member", help="添加成员")
    p.add_argument("--name", required=True)
    p.add_argument("--note", default="")
    p.add_argument("--group", default="")

    return parser


def run_command(args):
    """根据解析后的参数执行对应的命令。

    Args:
        args (argparse.Namespace): 解析后的参数对象。

    Returns:
        bool: 如果执行了命令返回 True，否则 False。
    """
    from src import services

    if args.cmd == "summary":
        for r in services.summary_all():
            print(f"{r['id']}\t{r['name']}\t{r['task_count']}\t{r['total_hours']}")

    elif args.cmd == "add-member":
        try:
            services.add_member(args.name, args.note, args.group)
            print(f"已添加 {args.name}")
        except ValueError as e:
            print(f"错误：{e}")
            sys.exit(1)

    elif args.cmd == "list-members":
        for m in services.list_members():
            print(f"{m['id']}\t{m['name']}\t{m['group_name']}\t{m['note']}")

    elif args.cmd == "list-tasks":
        for t in services.list_tasks():
            print(f"{t['id']}\t{t['date']}\t{t['title']}\t"
                  f"{t['people']}\t{t['total_hours']}")

    elif args.cmd == "backup":
        path = services.backup_db()
        print(f"已备份到 {path}")

    elif args.cmd == "export-summary":
        path = services.export_summary_csv()
        print(f"已导出到 {path}")

    else:
        return False
    return True


def main():
    """主函数：初始化数据库，解析参数，分发执行。"""
    init_db()
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd:
        run_command(args)
        return

    else:
        from src.cli import main_menu
        main_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已退出")
    except Exception as e:
        logger.exception("未处理异常")
        print(f"出错了：{e}")