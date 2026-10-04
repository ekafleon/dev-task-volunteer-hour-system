# src/services.py
import sqlite3

import csv
from pathlib import Path

from src.db import get_conn
from src.config import BASE_DIR


def add_member(name, note=""):
    """
    添加成员到数据库中
    :param name: 成员姓名
    :param note: 成员备注
    """
    conn = get_conn()
    try:
        conn.execute("INSERT INTO members (name, note) VALUES (?, ?)", (name, note))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError(f"成员 [{name}] 已存在. ")
    finally:
        conn.close()


def list_members():
    """
    列出在数据库中的成员
    """
    conn = get_conn()
    rows = conn.execute("SELECT id, name, note FROM members ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_members(member_id, name=None, note=None):
    """
    更新成员在数据库中的信息
    :param member_id: 成员ID
    :param name: 成员姓名，可选
    :param note: 成员备注，可选
    """
    conn = get_conn()
    try:
        member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        if not member:
            return None
        new_name = name if name is not None else member['name']
        new_note = note if note is not None else member['note']
        try:
            conn.execute("UPDATE members SET name=?, note=? WHERE id = ?", (new_name, new_note, member_id))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"成员名 [{new_name}] 已存在. ")
        return {"id": member_id, "name": new_name, "note": new_note}
    finally:
        conn.close()

def search_members(keyword):
    """
    通过关键词模糊搜索成员
    :param keyword: 关键词
    """
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, note FROM members WHERE name LIKE ? ORDER BY id",
        (f"%{keyword}%",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_task(title, description, date, participations):
    """
    添加任务到数据库中
    :param title: 任务名称
    :param description: 任务描述
    :param date: 任务日期
    :param participations: 任务的参与者
    """
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO tasks (title, description, date) VALUES (?, ?, ?)",
            (title, description, date),
        )
        task_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO participations (task_id, member_id, hours) VALUES (?, ?, ?)",
            [(task_id, mid, h) for mid, h in participations]
        )
        conn.commit()
        return task_id
    finally:
        conn.close()


def list_tasks():
    """
    列出数据库中的任务
    """
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
    return [dict(r) for r in rows]


def get_task_detail(task_id):
    """
    获取任务详情
    :param task_id: 任务ID
    """
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
    return {
        "task": dict(task),
        "participants": [dict(p) for p in parts],
    }


def update_task(task_id, title=None, description=None, date=None):
    """
    更新数据库中的任务
    :param task_id: 任务ID
    :param title: 任务标题，可选
    :param description: 任务描述，可选
    :param date: 任务日期，可选
    """
    conn = get_conn()
    try:
        task = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
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
    """
    删除任务
    :param task_id: 任务ID
    """
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def search_task(keyword=None, start_date=None, end_date=None):
    """
    按关键词和日期范围搜索任务
    :param keyword: 关键词
    :param start_date: 搜索开始日期
    :param end_date: 搜索结束日期
    """
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
        params.append(keyword)
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


def summary_all():
    """
    列出全体时长信息
    """
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
    """
    列出某个成员的时长信息
    :param member_id: 成员ID
    """
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


def upsert_participation(task_id, member_id, hours):
    """
    补录时长或成员
    :param task_id: 任务ID
    :param member_id: 成员ID
    :param hours: 要修改的时长
    """
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM participations WHERE task_id = ? AND member_id = ?",
            (task_id, member_id)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE participations SET hours = ? WHERE task_id = ? AND member_id = ?",
                (hours, task_id, member_id)
            )
            action = "updated"
        else:
            conn.execute(
                "INSERT INTO participations (task_id, member_id, hours) VALUES (?, ?, ?)",
                (task_id, member_id, hours)
            )
            action = "added"
        conn.commit()
        return action
    finally:
        conn.close()


def export_summary_csv(path=None):
    """
    导出全体成员时长到csv
    :param path: 存储csv的路径
    """
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
    """
    导出任务列表到csv
    :param path: 存储csv的路径
    """
    if path is None:
        path = BASE_DIR / "exports" / "tasks.csv"
    else:
        path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list_tasks()
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "日期", "任务名称", "人数", " 总时长"])
        for r in rows:
            writer.writerow([r["id"], r["date"], r["title"], r["people"], r["total_hours"]])
    return path
