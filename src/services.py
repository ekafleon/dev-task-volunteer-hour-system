# src/services.py

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

from src.db import get_conn
from src.config import BASE_DIR


# ==================== 成员 ====================

def add_member(name, note=""):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO members (name, note) VALUES (?, ?)", (name, note))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"成员「{name}」已存在")
    finally:
        conn.close()


def list_members():
    conn = get_conn()
    rows = conn.execute("SELECT id, name, note FROM members ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_member(member_id, name=None, note=None):
    """修改成员。参数为 None 时保持原值。找不到返回 None。"""
    conn = get_conn()
    try:
        member = conn.execute(
            "SELECT * FROM members WHERE id = ?", (member_id,)
        ).fetchone()
        if not member:
            return None

        new_name = name if name is not None else member["name"]
        new_note = note if note is not None else member["note"]

        try:
            conn.execute(
                "UPDATE members SET name = ?, note = ? WHERE id = ?",
                (new_name, new_note, member_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"成员名「{new_name}」已存在")

        return {"id": member_id, "name": new_name, "note": new_note}
    finally:
        conn.close()


def delete_member(member_id):
    """删除成员，级联删除参与记录。返回信息或 None。"""
    conn = get_conn()
    try:
        member = conn.execute(
            "SELECT name FROM members WHERE id = ?", (member_id,)
        ).fetchone()
        if not member:
            return None

        cnt = conn.execute(
            "SELECT COUNT(*) AS c FROM participations WHERE member_id = ?",
            (member_id,),
        ).fetchone()["c"]

        conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        return {"name": member["name"], "removed_records": cnt}
    finally:
        conn.close()


def search_members(keyword):
    """按姓名模糊搜索。"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, note FROM members WHERE name LIKE ? ORDER BY id",
        (f"%{keyword}%",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== 任务 ====================

def add_task(title, description, date, participations):
    """participations: [(member_id, hours), ...]"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, date) VALUES (?, ?, ?)",
            (title, description, date),
        )
        task_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO participations (task_id, member_id, hours) VALUES (?, ?, ?)",
            [(task_id, mid, h) for mid, h in participations],
        )
        conn.commit()
        return task_id
    finally:
        conn.close()


def list_tasks():
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.id, t.title, t.date,
               COUNT(p.id) AS people,
               IFNULL(SUM(p.hours), 0) AS total_hours
        FROM tasks t
        LEFT JOIN participations p ON p.task_id = t.id
        GROUP BY t.id
        ORDER BY t.date DESC, t.id DESC
    """).fetchall()
    conn.close()

    result = []
    for r in rows:
        item = dict(r)
        item["ago"] = humanize_date(item["date"])
        result.append(item)
    return result


def get_task_detail(task_id):
    conn = get_conn()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        return None

    parts = conn.execute("""
        SELECT m.name, p.hours
        FROM participations p
        JOIN members m ON m.id = p.member_id
        WHERE p.task_id = ?
        ORDER BY m.name
    """, (task_id,)).fetchall()
    conn.close()
    return {"task": dict(task), "participants": [dict(p) for p in parts]}


def update_task(task_id, title=None, description=None, date=None):
    conn = get_conn()
    try:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return None

        new_title = title if title is not None else task["title"]
        new_desc = description if description is not None else task["description"]
        new_date = date if date is not None else task["date"]

        conn.execute(
            "UPDATE tasks SET title = ?, description = ?, date = ? WHERE id = ?",
            (new_title, new_desc, new_date, task_id),
        )
        conn.commit()
        return {"id": task_id, "title": new_title,
                "description": new_desc, "date": new_date}
    finally:
        conn.close()


def delete_task(task_id):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def search_tasks(keyword=None, start_date=None, end_date=None):
    sql = """
        SELECT t.id, t.title, t.date,
               COUNT(p.id) AS people,
               IFNULL(SUM(p.hours), 0) AS total_hours
        FROM tasks t
        LEFT JOIN participations p ON p.task_id = t.id
        WHERE 1=1
    """
    params = []
    if keyword:
        sql += " AND t.title LIKE ?"
        params.append(f"%{keyword}%")
    if start_date:
        sql += " AND t.date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND t.date <= ?"
        params.append(end_date)
    sql += " GROUP BY t.id ORDER BY t.date DESC"

    conn = get_conn()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== 参与记录 ====================

def batch_add_hours(task_id, member_ids, hours):
    """为已存在任务批量添加时长。返回 (成功数, 跳过数)。"""
    conn = get_conn()
    try:
        task = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise ValueError("任务不存在")

        success, skipped = 0, 0
        for mid in member_ids:
            exists = conn.execute(
                "SELECT 1 FROM members WHERE id = ?", (mid,)
            ).fetchone()
            if not exists:
                skipped += 1
                continue
            try:
                conn.execute(
                    "INSERT INTO participations (task_id, member_id, hours) VALUES (?, ?, ?)",
                    (task_id, mid, hours),
                )
                success += 1
            except sqlite3.IntegrityError:
                skipped += 1
        conn.commit()
        return success, skipped
    finally:
        conn.close()


def upsert_participation(task_id, member_id, hours):
    """补录：存在则更新，不存在则新增。返回 'added' 或 'updated'。"""
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM participations WHERE task_id = ? AND member_id = ?",
            (task_id, member_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE participations SET hours = ? WHERE task_id = ? AND member_id = ?",
                (hours, task_id, member_id),
            )
            action = "updated"
        else:
            conn.execute(
                "INSERT INTO participations (task_id, member_id, hours) VALUES (?, ?, ?)",
                (task_id, member_id, hours),
            )
            action = "added"
        conn.commit()
        return action
    finally:
        conn.close()


def remove_participation(task_id, member_id):
    """移除某人在某任务中的参与记录。返回是否删除成功。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM participations WHERE task_id = ? AND member_id = ?",
            (task_id, member_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ==================== 统计 ====================

def summary_all():
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.id, m.name,
               IFNULL(SUM(p.hours), 0) AS total_hours,
               COUNT(p.id) AS task_count
        FROM members m
        LEFT JOIN participations p ON p.member_id = m.id
        GROUP BY m.id
        ORDER BY total_hours DESC, m.id
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def summary_member(member_id):
    conn = get_conn()
    member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        conn.close()
        return None

    rows = conn.execute("""
        SELECT t.title, t.date, p.hours
        FROM participations p
        JOIN tasks t ON t.id = p.task_id
        WHERE p.member_id = ?
        ORDER BY t.date
    """, (member_id,)).fetchall()
    conn.close()
    return {"member": dict(member), "records": [dict(r) for r in rows]}


# ==================== 工具 ====================

def humanize_date(date_str):
    """把 YYYY-MM-DD 转成 '3 天前' 这样的字符串。"""
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return date_str

    today = datetime.now().date()
    delta = (today - target).days

    if delta < 0:
        return f"{-delta} 天后"
    if delta == 0:
        return "今天"
    if delta == 1:
        return "昨天"
    if delta < 30:
        return f"{delta} 天前"
    if delta < 365:
        return f"{delta // 30} 个月前"
    return f"{delta // 365} 年前"


# ==================== 导出 ====================

def export_summary_csv(path=None):
    """导出汇总 CSV。path 为 None 用默认路径。"""
    if path is None:
        path = BASE_DIR / "exports" / "summary.csv"
    else:
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = summary_all()
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "姓名", "任务数", "总时长"])
        for r in rows:
            writer.writerow([r["id"], r["name"], r["task_count"], r["total_hours"]])
    return path


def export_tasks_csv(path=None):
    """导出任务 CSV。path 为 None 用默认路径。"""
    if path is None:
        path = BASE_DIR / "exports" / "tasks.csv"
    else:
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = list_tasks()
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "日期", "任务名称", "人数", "总时长"])
        for r in rows:
            writer.writerow([r["id"], r["date"], r["title"],
                             r["people"], r["total_hours"]])
    return path
