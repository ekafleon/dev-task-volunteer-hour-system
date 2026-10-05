# src/cli.py

from datetime import datetime

from src import services


# ==================== 输入辅助 ====================

def input_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("输入不能为空")


def input_int(prompt, min_value=None):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            print("请输入整数")
            continue
        if min_value is not None and value < min_value:
            print(f"不能小于 {min_value}")
            continue
        return value


def input_float(prompt, min_value=None):
    while True:
        try:
            value = float(input(prompt).strip())
        except ValueError:
            print("请输入数字")
            continue
        if min_value is not None and value < min_value:
            print(f"不能小于 {min_value}")
            continue
        return value


def input_date(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print("日期格式应为 YYYY-MM-DD")


def confirm(prompt):
    """统一的是否确认。"""
    return input(f"{prompt} (y/N)：").strip().lower() == "y"


# ==================== 成员功能 ====================

def add_member_dialog():
    print("\n--- 添加成员 ---")
    name = input_non_empty("姓名: ")
    note = input("备注: ").strip()
    try:
        services.add_member(name, note)
        print("添加成功")
    except ValueError as e:
        print(f"{e}")


def list_members_dialog():
    members = services.list_members()
    if not members:
        print("暂无成员")
        return
    print("\n--- 成员列表 ---")
    for m in members:
        print(f"  {m['id']}. {m['name']}  {m['note']}")


def update_member_dialog():
    members = services.list_members()
    if not members:
        print("暂无成员")
        return

    print("\n--- 修改成员 ---")
    for m in members:
        print(f"  {m['id']}. {m['name']}  {m['note']}")

    mid = input_int("要修改的成员 ID：", min_value=1)
    target = next((m for m in members if m["id"] == mid), None)
    if not target:
        print("未找到该成员。")
        return

    print(f"\n当前：姓名「{target['name']}」，备注「{target['note']}」")
    name = input(f"新姓名 [{target['name']}]（回车保持）：").strip()
    note = input(f"新备注 [{target['note']}]（回车保持）：").strip()

    try:
        services.update_member(
            mid,
            name=name if name else None,
            note=note if note else None,
        )
        print("已更新。")
    except ValueError as e:
        print(f"{e}")


def delete_member_dialog():
    members = services.list_members()
    if not members:
        print("暂无成员")
        return

    print("\n--- 删除成员 ---")
    for m in members:
        print(f"  {m['id']}. {m['name']}")

    mid = input_int("要删除的成员 ID：", min_value=1)
    if not confirm("确认删除？该成员的所有参与记录也会被删除"):
        print("已取消。")
        return

    result = services.delete_member(mid)
    if not result:
        print("未找到该成员。")
    else:
        print(f"已删除「{result['name']}」，同时移除 {result['removed_records']} 条参与记录。")


def search_member_dialog():
    print("\n--- 搜索成员 ---")
    keyword = input_non_empty("搜索关键词：")
    results = services.search_members(keyword)
    if not results:
        print("没有匹配的成员。")
        return
    print(f"\n找到 {len(results)} 位成员：")
    for m in results:
        print(f"  {m['id']}. {m['name']}  {m['note']}")


# ==================== 任务功能 ====================

def collect_participations(members):
    """在内存中多次批量收集参与者，返回 [(member_id, hours), ...]。"""
    member_map = {m["id"]: m["name"] for m in members}
    parts = {}

    while True:
        print("\n当前已添加：")
        if parts:
            for mid, h in parts.items():
                print(f"  {mid}. {member_map[mid]}：{h} 小时")
        else:
            print("  （无）")

        print("\n可选成员：")
        for m in members:
            mark = "（已添加）" if m["id"] in parts else ""
            print(f"  {m['id']}. {m['name']} {mark}")

        raw = input("成员 ID（逗号分隔，all 表示全部，回车结束）：").strip()
        if not raw:
            break

        if raw.lower() == "all":
            member_ids = [m["id"] for m in members]
        else:
            try:
                member_ids = [int(x.strip()) for x in raw.split(",") if x.strip()]
            except ValueError:
                print("ID 格式不对。")
                continue

        valid = [mid for mid in member_ids if mid in member_map]
        if not valid:
            print("没有有效成员。")
            continue

        hours = input_float("统一时长（小时）：", min_value=0.1)

        added, skipped = 0, 0
        for mid in valid:
            if mid in parts:
                skipped += 1
                continue
            parts[mid] = hours
            added += 1
        print(f"本批添加 {added} 人，跳过 {skipped} 人（已存在）。")

    return list(parts.items())


def add_task_dialog():
    print("\n--- 登记任务 ---")
    title = input_non_empty("任务名称: ")
    desc = input("描述(可回车跳过): ").strip()
    date = input_date("日期(YYYY-MM-DD): ")

    members = services.list_members()
    if not members:
        print("请先添加成员")
        return

    parts = collect_participations(members)
    if not parts:
        print("没有参与者，任务未保存")
        return

    tid = services.add_task(title, desc, date, parts)
    print(f"已保存, 任务 ID = {tid}，共 {len(parts)} 位参与者")


def list_tasks_dialog():
    tasks = services.list_tasks()
    if not tasks:
        print("(暂无任务)")
        return
    print("\n--- 任务列表 ---")
    print(f"{'ID':<4}{'日期':<12}{'距今':<10}{'任务名称':<20}{'人数':<6}{'总时长'}")
    print("  " + "-" * 70)
    for t in tasks:
        print(f"{t['id']:<4}{t['date']:<12}{t['ago']:<10}"
              f"{t['title']:<20}{t['people']:<6}{t['total_hours']}")


def show_task_detail_dialog():
    tid = input_int("\n任务 ID：", min_value=1)
    detail = services.get_task_detail(tid)
    if not detail:
        print("未找到")
        return

    t = detail["task"]
    print(f"\n--- 任务详情 ---")
    print(f"任务:{t['title']}")
    print(f"日期: {t['date']}")
    print(f"描述: {t['description'] or '(无)'}")
    print("参与者: ")
    for p in detail["participants"]:
        print(f" - {p['name']}: {p['hours']} 小时")


def update_task_dialog():
    tasks = services.list_tasks()
    if not tasks:
        print("暂无任务")
        return

    print("\n--- 修改任务 ---")
    for t in tasks:
        print(f"  {t['id']}. {t['date']} {t['title']}")

    tid = input_int("要修改的任务 ID：", min_value=1)
    detail = services.get_task_detail(tid)
    if not detail:
        print("未找到该任务。")
        return

    t = detail["task"]
    print(f"\n当前：")
    print(f"  标题：{t['title']}")
    print(f"  描述：{t['description'] or '（无）'}")
    print(f"  日期：{t['date']}")

    title = input(f"新标题 [{t['title']}]（回车保持）：").strip()
    desc = input(f"新描述 [{t['description']}]（回车保持）：").strip()
    date = input(f"新日期 [{t['date']}]（回车保持）：").strip()

    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print("日期格式不对，保持原值。")
            date = ""

    services.update_task(
        tid,
        title=title if title else None,
        description=desc if desc else None,
        date=date if date else None,
    )
    print("已更新。")


def delete_task_dialog():
    tasks = services.list_tasks()
    if not tasks:
        print("暂无任务")
        return

    print("\n--- 删除任务 ---")
    for t in tasks:
        print(f"  {t['id']}. {t['date']} {t['title']}")

    tid = input_int("要删除的任务 ID：", min_value=1)
    if not confirm("确认删除该任务及其所有参与记录"):
        print("已取消。")
        return

    services.delete_task(tid)
    print("已删除")


def supplement_hours_dialog():
    tasks = services.list_tasks()
    if not tasks:
        print("暂无任务")
        return

    print("\n--- 时长补录 ---")
    for t in tasks:
        print(f"  {t['id']}. {t['date']} {t['title']}")

    tid = input_int("任务 ID：", min_value=1)
    detail = services.get_task_detail(tid)
    if not detail:
        print("未找到该任务。")
        return

    print(f"\n任务「{detail['task']['title']}」当前参与者：")
    if detail["participants"]:
        for p in detail["participants"]:
            print(f"  - {p['name']}：{p['hours']} 小时")
    else:
        print("  （暂无参与者）")

    members = services.list_members()
    if not members:
        print("请先添加成员。")
        return

    print("\n所有成员：")
    for m in members:
        print(f"  {m['id']}. {m['name']}")

    raw = input("要补录的成员 ID（逗号分隔，all 表示全部，回车取消）：").strip()
    if not raw:
        print("已取消。")
        return

    if raw.lower() == "all":
        member_ids = [m["id"] for m in members]
    else:
        try:
            member_ids = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            print("ID 格式不对。")
            return

    hours = input_float("统一补录时长（小时）：", min_value=0.1)

    added, updated, skipped = 0, 0, 0
    valid_ids = {m["id"] for m in members}
    for mid in member_ids:
        if mid not in valid_ids:
            skipped += 1
            continue
        action = services.upsert_participation(tid, mid, hours)
        if action == "added":
            added += 1
        else:
            updated += 1

    print(f"\n补录完成：新增 {added} 人，更新 {updated} 人，跳过 {skipped} 人。")


def search_task_dialog():
    print("\n--- 搜索任务 ---")
    keyword = input("关键词（回车跳过）：").strip()
    start = input("起始日期 YYYY-MM-DD（回车跳过）：").strip()
    end = input("结束日期 YYYY-MM-DD（回车跳过）：").strip()

    results = services.search_tasks(
        keyword=keyword or None,
        start_date=start or None,
        end_date=end or None,
    )
    if not results:
        print("没有匹配的任务。")
        return
    print(f"\n找到 {len(results)} 个任务：")
    for t in results:
        print(f"  {t['id']}. {t['date']} {t['title']} "
              f"({t['people']}人, {t['total_hours']}h)")


def export_tasks_dialog():
    print("\n--- 导出任务 CSV ---")
    raw = input("导出路径（回车用默认 exports/tasks.csv）：").strip()
    path = services.export_tasks_csv(raw if raw else None)
    print(f"已导出到 {path}")


# ==================== 统计功能 ====================

def summary_all_dialog():
    rows = services.summary_all()
    if not rows:
        print("(暂无成员)")
        return
    print("\n--- 全体成员汇总 ---")
    print(f"{'ID':<5}{'姓名':<12}{'任务数':<8}{'总时长'}")
    print("  " + "-" * 40)
    for r in rows:
        print(f"  {r['id']:<5}{r['name']:<12}{r['task_count']:<8}{r['total_hours']} 小时")


def summary_member_dialog():
    mid = input_int("\n成员 ID: ", min_value=1)
    data = services.summary_member(mid)
    if not data:
        print("未找到")
        return

    print(f"\n--- {data['member']['name']} 的志愿时长明细 ---")
    if not data['records']:
        print("无参与记录")
        return

    total = 0.0
    for r in data['records']:
        print(f"{r['date']} {r['title']} {r['hours']} 小时")
        total += float(r['hours'])
    print("  " + "-" * 40)
    print(f"总计: {total} 小时")


def export_summary_dialog():
    print("\n--- 导出汇总 CSV ---")
    raw = input("导出路径（回车用默认 exports/summary.csv）：").strip()
    path = services.export_summary_csv(raw if raw else None)
    print(f"已导出到 {path}")


# ==================== 菜单 ====================

def member_menu():
    while True:
        print("\n===== 成员管理 =====")
        print("1. 添加成员")
        print("2. 查看成员")
        print("3. 修改成员")
        print("4. 删除成员")
        print("5. 搜索成员")
        print("0. 返回")
        choice = input("请选择: ").strip()

        if choice == "1":
            add_member_dialog()
        elif choice == "2":
            list_members_dialog()
        elif choice == "3":
            update_member_dialog()
        elif choice == "4":
            delete_member_dialog()
        elif choice == "5":
            search_member_dialog()
        elif choice == "0":
            break
        else:
            print("无效选项")


def task_menu():
    while True:
        print("\n===== 任务管理 =====")
        print("1. 登记任务")
        print("2. 任务列表")
        print("3. 任务详情")
        print("4. 修改任务")
        print("5. 删除任务")
        print("6. 时长补录")
        print("7. 搜索任务")
        print("8. 导出任务 CSV")
        print("0. 返回")
        choice = input("请选择: ").strip()

        if choice == "1":
            add_task_dialog()
        elif choice == "2":
            list_tasks_dialog()
        elif choice == "3":
            show_task_detail_dialog()
        elif choice == "4":
            update_task_dialog()
        elif choice == "5":
            delete_task_dialog()
        elif choice == "6":
            supplement_hours_dialog()
        elif choice == "7":
            search_task_dialog()
        elif choice == "8":
            export_tasks_dialog()
        elif choice == "0":
            break
        else:
            print("无效选项")


def stats_menu():
    while True:
        print("\n===== 时长统计 =====")
        print("1. 全体汇总")
        print("2. 个人明细")
        print("3. 导出汇总 CSV")
        print("0. 返回")
        choice = input("请输入: ").strip()

        if choice == "1":
            summary_all_dialog()
        elif choice == "2":
            summary_member_dialog()
        elif choice == "3":
            export_summary_dialog()
        elif choice == "0":
            break
        else:
            print("无效选项")


def main_menu():
    print("========================================")
    print("  开发组任务登记及志愿时长分配系统 v1.0")
    print("========================================")
    while True:
        print("\n===== 主菜单 =====")
        print("1. 成员管理")
        print("2. 任务管理")
        print("3. 时长统计")
        print("0. 退出")
        choice = input("请选择: ").strip()

        if choice == "1":
            member_menu()
        elif choice == "2":
            task_menu()
        elif choice == "3":
            stats_menu()
        elif choice == "0":
            print("再见!")
            break
        else:
            print("无效选项")
