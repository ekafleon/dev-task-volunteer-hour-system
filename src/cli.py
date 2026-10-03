# src/cli.py
from datetime import datetime
from src import services


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
            print(f"不能小于 {min_value} ")
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
            print(f"不能小于 {min_value} ")
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


def collect_participations(members):
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
                print("ID 格式不对，请用逗号分隔数字。")
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


def supplement_hours():
    tasks = services.list_tasks()
    if not tasks:
        print("暂无任务")
        return
    print("\n--- 时长补录 ---")
    print("现有任务：")
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
    if not member_ids:
        print("没有选择成员。")
        return
    hours = input_float("统一补录时长（小时）：", min_value=0.1)
    added, updated, skipped = 0, 0, 0
    for mid in member_ids:
        if not any(m["id"] == mid for m in members):
            skipped += 1
            continue
        action = services.upsert_participation(tid, mid, hours)
        if action == "added":
            added += 1
        else:
            updated += 1
    print(f"\n补录完成：新增 {added} 人，更新 {updated} 人，跳过 {skipped} 人（无效 ID）。")


def member_menu():
    while True:
        print("\n=====成员管理=====")
        print("1. 添加成员")
        print("2. 查看成员")
        print("0. 返回")
        choice = input("请选择: ").strip()
        if choice == "1":
            name = input_non_empty("姓名: ")
            note = input("备注").strip()
            try:
                services.add_member(name, note)
                print("添加成功")
            except ValueError as e:
                print(f" {e} ")
        elif choice == "2":
            members = services.list_members()
            if not members:
                print("暂无成员")
                continue
            for m in members:
                print(f"  {m['id']}. {m['name']}  {m['note']}")
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
        print("4. 删除任务")
        print("5. 时长补录")
        print("0. 返回")
        choice = input("请选择: ").strip()
        if choice == "1":
            title = input_non_empty("任务名称: ")
            desc = input("描述(可回车跳过)").strip()
            date = input_date("日期(YYYY-MM-DD): ")
            members = services.list_members()
            if not members:
                print("请先添加成员")
                continue
            parts = collect_participations(members)
            if not parts:
                print("没有参与者，任务未保存")
                continue
            tid = services.add_task(title, desc, date, parts)
            print(f"已保存, 任务 ID = {tid}，共 {len(parts)} 位参与者")
        elif choice == "2":
            tasks = services.list_tasks()
            if not tasks:
                print("(暂无任务)")
                continue
            print(f"{'ID':<4}{'日期':<12}{'任务名称':<20}{'人数':<6}{'总时长'}")
            print("  " + "-" * 60)
            for t in tasks:
                print(f"{t['id']:<4}{t['date']:<12}{t['title']:<20}"
                      f"{t['people']:<6}{t['total_hours']}")
        elif choice == "3":
            tid = input_int("任务 ID：", min_value=1)
            detail = services.get_task_detail(tid)
            if not detail:
                print("未找到")
                continue
            t = detail["task"]
            print(f"\n任务:{t['title']}")
            print(f"日期: {t['date']}")
            print(f"描述: {t['description'] or '(无)'}")
            print("参与者: ")
            for p in detail["participants"]:
                print(f" - {p['name']}: {p['hours']} 小时")
        elif choice == "4":
            tid = input_int("任务 ID: ", min_value=1)
            services.delete_task(tid)
            print("已删除")
        elif choice == "5":
            supplement_hours()
        elif choice == "0":
            break
        else:
            print("无效选项")


def stats_menu():
    while True:
        print("\n===== 时长统计 =====")
        print("1. 全体汇总")
        print("2. 个人明细")
        print("0. 返回")
        choice = input("请输入: ").strip()
        if choice == "1":
            rows = services.summary_all()
            if not rows:
                print("(暂无成员)")
                continue
            print(f"{'ID':<5}{'姓名':<12}{'任务数':<8}{'总时长'}")
            print("  " + "-" * 40)
            for r in rows:
                print(f"  {r['id']:<5}{r['name']:<12}{r['task_count']:<8}{r['total_hours']} 小时")
        elif choice == "2":
            mid = input_int("成员 ID: ", min_value=1)
            data = services.summary_member(mid)
            if not data:
                print("未找到")
                continue
            print(f"\n{data['member']['name']} 的志愿时长明细: ")
            if not data['records']:
                print("无参与记录")
                continue
            total = 0.0
            for r in data['records']:
                print(f"{r['date']} {r['title']} {r['hours']} 小时")
                total += float(r['hours'])
            print("  " + "-" * 40)
            print(f"总计: {total} 小时")
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
            print("再见! ")
            break
        else:
            print("无效选项")