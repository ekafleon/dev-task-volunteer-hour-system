# src/cli.py

from datetime import datetime

from src import services
from src import colors as c


# ==================== 输入辅助 ====================

def input_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        c.warn("输入不能为空")


def input_int(prompt, min_value=None):
    while True:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            c.warn("请输入整数")
            continue
        if min_value is not None and value < min_value:
            c.warn(f"不能小于 {min_value}")
            continue
        return value


def input_float(prompt, min_value=None):
    while True:
        try:
            value = float(input(prompt).strip())
        except ValueError:
            c.warn("请输入数字")
            continue
        if min_value is not None and value < min_value:
            c.warn(f"不能小于 {min_value}")
            continue
        return value


def input_date(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            c.warn("日期格式应为 YYYY-MM-DD")


def confirm(prompt):
    """统一的是否确认。"""
    return input(f"{prompt} (y/N)：").strip().lower() == "y"


# ==================== 通用打印函数 ====================

def print_member_table(members, mark_ids=None):
    """完整成员表：ID 姓名 小组 备注。"""
    mark_ids = mark_ids or set()

    header = (
        c.pad("ID", 5) +
        c.pad("姓名", 14) +
        c.pad("小组", 14) +
        c.pad("备注", 20)
    )
    print(header)
    print("-" * 53)

    for m in members:
        group = m['group_name'] or '[未分组]'
        mark = "（已添加）" if m["id"] in mark_ids else ""
        row = (
            c.pad(m["id"], 5) +
            c.pad(m["name"], 14) +
            c.pad(group, 14) +
            c.pad(m["note"], 20) +
            mark
        )
        print(row)


def print_member_brief(members):
    """简略成员列表：ID. 姓名  备注。"""
    for m in members:
        print(f"  {m['id']}. {m['name']}  {m['note']}")


def print_task_table(tasks):
    """完整任务表：ID 日期 距今 任务名称 人数 总时长。"""
    header = (
        c.pad("ID", 5) +
        c.pad("日期", 13) +
        c.pad("距今", 12) +
        c.pad("任务名称", 22) +
        c.pad("人数", 8) +
        c.pad("总时长", 10)
    )
    print(header)
    print("-" * 70)

    for t in tasks:
        row = (
            c.pad(t["id"], 5) +
            c.pad(t["date"], 13) +
            c.pad(t["ago"], 12) +
            c.pad(t["title"], 22) +
            c.pad(t["people"], 8) +
            c.pad(t["total_hours"], 10)
        )
        print(row)


def print_task_brief(tasks, show_stats=False):
    """简略任务列表：ID. 日期 标题。
    show_stats=True 时，行末附上（人数, 总时长）。
    """
    for t in tasks:
        line = f"  {t['id']}. {t['date']} {t['title']}"
        if show_stats:
            line += f"  ({t['people']}人, {t['total_hours']}h)"
        print(line)


def print_summary_table(rows):
    """汇总表：ID 姓名 任务数 总时长。"""
    header = (
        c.pad("ID", 5) +
        c.pad("姓名", 14) +
        c.pad("任务数", 10) +
        c.pad("总时长", 12)
    )
    print(header)
    print("-" * 41)

    for r in rows:
        row = (
            c.pad(r["id"], 5) +
            c.pad(r["name"], 14) +
            c.pad(r["task_count"], 10) +
            c.pad(str(r["total_hours"]) + " 小时", 12)
        )
        print(row)


def print_group_list(groups):
    """小组编号列表。"""
    for i, g in enumerate(groups, 1):
        print(f"  {i}. {g}")
    print(f"  {len(groups) + 1}. （未分组）")


# ==================== 成员功能 ====================

def add_member_dialog():
    print(c.bold("\n--- 添加成员 ---"))
    name = input_non_empty("姓名: ")
    note = input("备注: ").strip()
    group = input("小组（可回车跳过）: ").strip()
    try:
        services.add_member(name, note, group)
        c.success("添加成功")
    except ValueError as e:
        c.error(f"{e}")


def list_members_dialog():
    members = services.list_members()
    if not members:
        c.warn("暂无成员")
        return
    print(c.bold("\n--- 成员列表 ---"))
    print_member_table(members)


def update_member_dialog():
    members = services.list_members()
    if not members:
        c.warn("暂无成员")
        return

    print(c.bold("\n--- 修改成员 ---"))
    print_member_table(members)

    mid = input_int("要修改的成员 ID：", min_value=1)
    target = next((m for m in members if m["id"] == mid), None)
    if not target:
        c.error("未找到该成员。")
        return

    print(f"\n当前：姓名「{target['name']}」，小组「{target['group_name'] or '未分组'}」，备注「{target['note']}」")
    name = input(f"新姓名 [{target['name']}]（回车保持）：").strip()
    group = input(f"新小组 [{target['group_name']}]（回车保持）：").strip()
    note = input(f"新备注 [{target['note']}]（回车保持）：").strip()

    try:
        services.update_member(
            mid,
            name=name if name else None,
            note=note if note else None,
            group_name=group if group else None,
        )
        c.success("已更新。")
    except ValueError as e:
        c.error(f"{e}")


def delete_member_dialog():
    members = services.list_members()
    if not members:
        c.warn("暂无成员")
        return

    print(c.bold("\n--- 删除成员 ---"))
    print_member_table(members)

    mid = input_int("要删除的成员 ID：", min_value=1)
    if not confirm("确认删除？该成员的所有参与记录也会被删除"):
        c.warn("已取消。")
        return

    result = services.delete_member(mid)
    if not result:
        c.error("未找到该成员。")
    else:
        c.success(f"已删除「{result['name']}」，同时移除 {result['removed_records']} 条参与记录。")


def search_member_dialog():
    print(c.bold("\n--- 搜索成员 ---"))
    keyword = input_non_empty("搜索关键词：")
    results = services.search_members(keyword)
    if not results:
        c.warn("没有匹配的成员。")
        return
    print(f"\n找到 {len(results)} 位成员：")
    print_member_brief(results)


def members_by_group_dialog():
    groups = services.list_groups()
    if not groups:
        c.warn("暂无小组。可以先去修改成员信息，给成员设置小组。")
        return

    print(c.bold("\n--- 按小组查看成员 ---"))
    print("现有小组：")
    print_group_list(groups)

    idx = input_int("选择小组编号：", min_value=1)
    if idx == len(groups) + 1:
        group_name = ""
        label = "未分组"
    elif 1 <= idx <= len(groups):
        group_name = groups[idx - 1]
        label = group_name
    else:
        c.warn("编号超出范围。")
        return

    members = services.list_members_by_group(group_name)
    if not members:
        c.warn(f"「{label}」下暂无成员。")
        return

    print(c.bold(f"\n--- 小组「{label}」成员 ---"))
    print_member_brief(members)


# ==================== 任务功能 ====================

def collect_participations(members):
    """在内存中多次批量收集参与者，返回 [(member_id, hours), ...]。"""
    member_map = {m["id"]: m["name"] for m in members}
    parts = {}

    while True:
        print(c.bold("\n当前已添加："))
        if parts:
            for mid, h in parts.items():
                print(f"  {mid}. {member_map[mid]}：{h} 小时")
        else:
            print("  （无）")

        print(c.bold("\n可选成员："))
        print_member_table(members, mark_ids=set(parts.keys()))

        raw = input("成员 ID（逗号分隔，all 表示全部，回车结束）：").strip()
        if not raw:
            break

        if raw.lower() == "all":
            member_ids = [m["id"] for m in members]
        else:
            try:
                member_ids = [int(x.strip()) for x in raw.split(",") if x.strip()]
            except ValueError:
                c.warn("ID 格式不对。")
                continue

        valid = [mid for mid in member_ids if mid in member_map]
        if not valid:
            c.warn("没有有效成员。")
            continue

        hours = input_float("统一时长（小时）：", min_value=0.1)

        added, skipped = 0, 0
        for mid in valid:
            if mid in parts:
                skipped += 1
                continue
            parts[mid] = hours
            added += 1
        c.info(f"本批添加 {added} 人，跳过 {skipped} 人（已存在）。")

    return list(parts.items())


def add_task_dialog():
    print(c.bold("\n--- 登记任务 ---"))
    title = input_non_empty("任务名称: ")
    desc = input("描述(可回车跳过): ").strip()
    date = input_date("日期(YYYY-MM-DD): ")

    members = services.list_members()
    if not members:
        c.warn("请先添加成员")
        return

    parts = collect_participations(members)
    if not parts:
        c.warn("没有参与者，任务未保存")
        return

    tid = services.add_task(title, desc, date, parts)
    c.success(f"已保存, 任务 ID = {tid}，共 {len(parts)} 位参与者")


def list_tasks_dialog():
    tasks = services.list_tasks()
    if not tasks:
        c.warn("(暂无任务)")
        return
    print(c.bold("\n--- 任务列表 ---"))
    print_task_table(tasks)


def show_task_detail_dialog():
    tid = input_int("\n任务 ID：", min_value=1)
    detail = services.get_task_detail(tid)
    if not detail:
        c.error("未找到")
        return

    t = detail["task"]
    print(c.bold("\n--- 任务详情 ---"))
    print(f"任务:{t['title']}")
    print(f"日期: {t['date']}")
    print(f"描述: {t['description'] or '(无)'}")
    print("参与者: ")
    for p in detail["participants"]:
        print(f" - {p['name']}: {p['hours']} 小时")


def update_task_dialog():
    tasks = services.list_tasks()
    if not tasks:
        c.warn("暂无任务")
        return

    print(c.bold("\n--- 修改任务 ---"))
    print_task_brief(tasks)

    tid = input_int("要修改的任务 ID：", min_value=1)
    detail = services.get_task_detail(tid)
    if not detail:
        c.error("未找到该任务。")
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
            c.warn("日期格式不对，保持原值。")
            date = ""

    services.update_task(
        tid,
        title=title if title else None,
        description=desc if desc else None,
        date=date if date else None,
    )
    c.success("已更新。")


def delete_task_dialog():
    tasks = services.list_tasks()
    if not tasks:
        c.warn("暂无任务")
        return

    print(c.bold("\n--- 删除任务 ---"))
    print_task_brief(tasks)

    tid = input_int("要删除的任务 ID：", min_value=1)
    if not confirm("确认删除该任务及其所有参与记录"):
        c.warn("已取消。")
        return

    services.delete_task(tid)
    c.success("已删除")


def supplement_hours_dialog():
    tasks = services.list_tasks()
    if not tasks:
        c.warn("暂无任务")
        return

    print(c.bold("\n--- 时长补录 ---"))
    print_task_brief(tasks)

    tid = input_int("任务 ID：", min_value=1)
    detail = services.get_task_detail(tid)
    if not detail:
        c.error("未找到该任务。")
        return

    print(f"\n任务「{detail['task']['title']}」当前参与者：")
    if detail["participants"]:
        for p in detail["participants"]:
            print(f"  - {p['name']}：{p['hours']} 小时")
    else:
        print("  （暂无参与者）")

    members = services.list_members()
    if not members:
        c.warn("请先添加成员。")
        return

    print(c.bold("\n所有成员："))
    print_member_brief(members)

    raw = input("要补录的成员 ID（逗号分隔，all 表示全部，回车取消）：").strip()
    if not raw:
        c.warn("已取消。")
        return

    if raw.lower() == "all":
        member_ids = [m["id"] for m in members]
    else:
        try:
            member_ids = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            c.warn("ID 格式不对。")
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

    c.success(f"补录完成：新增 {added} 人，更新 {updated} 人，跳过 {skipped} 人。")


def remove_participation_dialog():
    tasks = services.list_tasks()
    if not tasks:
        c.warn("暂无任务")
        return

    print(c.bold("\n--- 移除参与记录 ---"))
    print_task_brief(tasks)

    tid = input_int("任务ID: ", min_value=1)
    detail = services.get_task_detail(tid)
    if not detail:
        c.error("未找到该任务。")
        return

    if not detail["participants"]:
        c.warn("该任务暂无参与者")
        return

    print(f"\n任务「{detail['task']['title']}」当前参与者: ")
    for p in detail["participants"]:
        print(f"  - {p['name']}: {p['hours']} 小时")

    members = services.list_members()
    name = input_non_empty("要移除的成员姓名: ")
    member = next((m for m in members if m["name"] == name), None)
    if not member:
        c.error("未找到该成员。")
        return

    if not confirm(f"确认移除 「{name}」 在该任务中的记录"):
        c.warn("已取消。")
        return

    ok = services.remove_participation(tid, member["id"])
    if ok:
        c.success(f"已移除 「{name}」 的参与记录。")
    else:
        c.error("移除失败，该成员可能不在此任务中。")


def search_task_dialog():
    print(c.bold("\n--- 搜索任务 ---"))
    keyword = input("关键词（回车跳过）：").strip()
    start = input("起始日期 YYYY-MM-DD（回车跳过）：").strip()
    end = input("结束日期 YYYY-MM-DD（回车跳过）：").strip()

    results = services.search_tasks(
        keyword=keyword or None,
        start_date=start or None,
        end_date=end or None,
    )
    if not results:
        c.warn("没有匹配的任务。")
        return
    print(f"\n找到 {len(results)} 个任务：")
    print_task_brief(results, show_stats=True)


def export_tasks_dialog():
    print(c.bold("\n--- 导出任务 CSV ---"))
    raw = input("导出路径（回车用默认 exports/tasks.csv）：").strip()
    path = services.export_tasks_csv(raw if raw else None)
    c.success(f"已导出到 {path}")


# ==================== 统计功能 ====================

def summary_all_dialog():
    rows = services.summary_all()
    if not rows:
        c.warn("(暂无成员)")
        return
    print(c.bold("\n--- 全体成员汇总 ---"))
    print_summary_table(rows)


def summary_member_dialog():
    mid = input_int("\n成员 ID: ", min_value=1)
    data = services.summary_member(mid)
    if not data:
        c.error("未找到")
        return

    print(c.bold(f"\n--- {data['member']['name']} 的志愿时长明细 ---"))
    if not data['records']:
        c.warn("无参与记录")
        return

    total = 0.0
    for r in data['records']:
        print(f"{r['date']} {r['title']} {r['hours']} 小时")
        total += float(r['hours'])
    print("  " + "-" * 40)
    c.success(f"总计: {total} 小时")


def export_summary_dialog():
    print(c.bold("\n--- 导出汇总 CSV ---"))
    raw = input("导出路径（回车用默认 exports/summary.csv）：").strip()
    path = services.export_summary_csv(raw if raw else None)
    c.success(f"已导出到 {path}")


# ==================== 系统功能 ====================

def backup_dialog():
    print(c.bold("\n--- 备份数据库 ---"))
    path = services.backup_db()
    c.success(f"已备份到 {path}")


# ==================== 菜单 ====================

def member_menu():
    while True:
        print(c.bold("\n===== 成员管理 ====="))
        print("1. 添加成员")
        print("2. 查看成员")
        print("3. 修改成员")
        print("4. 删除成员")
        print("5. 搜索成员")
        print("6. 按小组查看")
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
        elif choice == "6":
            members_by_group_dialog()
        elif choice == "0":
            break
        else:
            c.warn("无效选项")


def task_menu():
    while True:
        print(c.bold("\n===== 任务管理 ====="))
        print("1. 登记任务")
        print("2. 任务列表")
        print("3. 任务详情")
        print("4. 修改任务")
        print("5. 删除任务")
        print("6. 时长补录")
        print("7. 移除参与记录")
        print("8. 搜索任务")
        print("9. 导出任务 CSV")
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
            remove_participation_dialog()
        elif choice == "8":
            search_task_dialog()
        elif choice == "9":
            export_tasks_dialog()
        elif choice == "0":
            break
        else:
            c.warn("无效选项")


def stats_menu():
    while True:
        print(c.bold("\n===== 时长统计 ====="))
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
            c.warn("无效选项")


def system_menu():
    while True:
        print(c.bold("\n===== 系统工具 ====="))
        print("1. 备份数据库")
        print("0. 返回")
        choice = input("请选: ").strip()

        if choice == "1":
            backup_dialog()
        elif choice == "0":
            break
        else:
            c.warn("无效选项")


def main_menu():
    print(c.bold("========================================"))
    print(c.bold("  开发组任务登记及志愿时长分配系统 v1.0"))
    print(c.bold("========================================"))
    while True:
        print(c.bold("\n===== 主菜单 ====="))
        print("1. 成员管理")
        print("2. 任务管理")
        print("3. 时长统计")
        print("4. 系统工具")
        print("0. 退出")
        choice = input("请选择: ").strip()

        if choice == "1":
            member_menu()
        elif choice == "2":
            task_menu()
        elif choice == "3":
            stats_menu()
        elif choice == "4":
            system_menu()
        elif choice == "0":
            c.success("再见!")
            break
        else:
            c.warn("无效选项")