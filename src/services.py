# src/services.py
"""业务逻辑层。

处理成员、任务、参与记录、统计、导出和备份等核心业务。
所有数据库操作均通过 db.get_conn() 获取连接，并保证连接关闭。
"""

import csv
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.db import get_conn
from src.logger import logger
from src.config import BASE_DIR, DB_PATH


# ==================== 成员 ====================

def add_member(name, note="", group_name=""):
    """添加一个新成员。

    Args:
        name (str): 成员姓名，必须唯一。
        note (str, optional): 备注，默认为空字符串。
        group_name (str, optional): 组名，默认为空字符串，表现为（未分组）。

    Raises:
        ValueError: 如果姓名已存在。
    """
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO members (name, note, group_name) VALUES (?, ?, ?)",
            (name, note, group_name)
        )
        conn.commit()
        logger.info(f"添加成员 {name} （小组：{group_name or '无'}）")
    except sqlite3.IntegrityError:
        raise ValueError(f"成员「{name}」已存在")
    finally:
        conn.close()


def list_members() -> list[dict]:
    """列出数据库中全部成员。

    Returns:
        list[dict]: 每个元素包含 id, name, note, group_name 四个键。
    """
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, note, group_name FROM members ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_member(member_id, name=None, note=None, group_name=None):
    """修改成员。参数为 None 时保持原值。找不到返回 None。

    Args:
        member_id (int): 成员ID。
        name (str, optional): 成员姓名，可选修改项。
        note (str, optional): 成员备注，可选修改项。
        group_name (str, optional): 成员组别，可选修改项。

    Returns:
        dict | None: 成功时返回包含 id, name, note, group_name 的字典；
                     找不到成员时返回 None。

    Raises:
        ValueError: 如果成员名与现有成员名重复。
    """
    conn = get_conn()
    try:
        member = conn.execute(
            "SELECT * FROM members WHERE id = ?", (member_id,)
        ).fetchone()
        if not member:
            return None

        new_name = name if name is not None else member["name"]
        new_note = note if note is not None else member["note"]
        new_group = group_name if group_name is not None else member["group_name"]

        try:
            conn.execute(
                "UPDATE members SET name = ?, note = ?, group_name = ? WHERE id = ?",
                (new_name, new_note, new_group, member_id),
            )
            conn.commit()
            logger.info(f"修改成员 id={member_id}")
        except sqlite3.IntegrityError:
            raise ValueError(f"成员名「{new_name}」已存在")

        return {"id": member_id, "name": new_name,
                "note": new_note, "group_name": new_group}
    finally:
        conn.close()


def delete_member(member_id):
    """删除成员，级联删除参与记录。返回信息或 None。

    Args:
        member_id (int): 成员ID。

    Returns:
        dict | None: 成功时返回 {"name": 成员名, "removed_records": 删除的参与记录数}；
                     找不到成员时返回 None。
    """
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
        logger.info(f"删除成员 {member['name']}, 移除 {cnt} 条参与记录")
        return {"name": member["name"], "removed_records": cnt}
    finally:
        conn.close()


def search_members(keyword):
    """按姓名模糊搜索成员。

    Args:
        keyword (str): 搜索关键词，用于匹配姓名。

    Returns:
        list[dict]: 匹配的成员列表，每个字典包含 id, name, note, group_name。
    """
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, note, group_name FROM members WHERE name LIKE ? ORDER BY id",
        (f"%{keyword}%",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_groups():
    """返回所有小组名（去重，按名称排序）。

    Returns:
        list[str]: 小组名称列表。
    """
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT group_name FROM members WHERE group_name != '' ORDER BY group_name"
    ).fetchall()
    conn.close()
    return [r["group_name"] for r in rows]


def list_members_by_group(group_name):
    """按小组查询成员。group_name 为空字符串时查询未分组。

    Args:
        group_name (str): 小组名称，空字符串表示未分组。

    Returns:
        list[dict]: 成员列表，每个字典包含 id, name, note, group_name。
    """
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, note, group_name FROM members WHERE group_name = ? ORDER BY id",
        (group_name,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== 任务 ====================

def add_task(title, description, date, participations):
    """添加任务及其参与记录。

    Args:
        title (str): 任务标题。
        description (str): 任务描述。
        date (str): 任务日期，格式 YYYY-MM-DD。
        participations (list[tuple[int, float]]): 参与者列表，
            每个元素为 (成员ID, 时长)。

    Returns:
        int: 新插入任务的 ID。
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
            [(task_id, mid, h) for mid, h in participations],
        )
        conn.commit()
        logger.info(f"登记任务 {title}, 参与者 {len(participations)} 人")
        return task_id
    finally:
        conn.close()


def list_tasks():
    """列出所有任务，包含参与人数和总时长，并计算距今时间。

    Returns:
        list[dict]: 每个字典包含 id, title, date, people, total_hours, ago。
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

    result = []
    for r in rows:
        item = dict(r)
        item["ago"] = humanize_date(item["date"])
        result.append(item)
    return result


def get_task_detail(task_id):
    """获取任务详情及参与者列表。

    Args:
        task_id (int): 任务 ID。

    Returns:
        dict | None: 包含 "task" 和 "participants" 两个键的字典；
                     找不到任务返回 None。
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
    return {"task": dict(task), "participants": [dict(p) for p in parts]}


def update_task(task_id, title=None, description=None, date=None):
    """修改任务信息。参数为 None 时保持原值。找不到返回 None。

    Args:
        task_id (int): 任务 ID。
        title (str, optional): 新标题。
        description (str, optional): 新描述。
        date (str, optional): 新日期。

    Returns:
        dict | None: 更新后的任务信息字典，找不到返回 None。
    """
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
    """删除任务及其所有参与记录（级联删除）。

    Args:
        task_id (int): 任务 ID。
    """
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    logger.info(f"删除任务 id={task_id}")


def search_tasks(keyword=None, start_date=None, end_date=None):
    """按关键词和日期范围搜索任务。

    Args:
        keyword (str, optional): 标题关键词。
        start_date (str, optional): 起始日期 YYYY-MM-DD。
        end_date (str, optional): 结束日期 YYYY-MM-DD。

    Returns:
        list[dict]: 任务列表，每个字典包含 id, title, date, people, total_hours。
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
    """为已存在任务批量添加时长。

    Args:
        task_id (int): 任务 ID。
        member_ids (list[int]): 成员 ID 列表。
        hours (float): 统一时长。

    Returns:
        tuple[int, int]: (成功添加数, 跳过数)。

    Raises:
        ValueError: 如果任务不存在。
    """
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
                    "INSERT INTO participations (task_id, member_id, hours) \
                        VALUES (?, ?, ?)",
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
    """补录参与记录：存在则更新，不存在则新增。

    Args:
        task_id (int): 任务 ID。
        member_id (int): 成员 ID。
        hours (float): 时长。

    Returns:
        str: 'added' 表示新增，'updated' 表示更新。
    """
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
    """移除某人在某任务中的参与记录。

    Args:
        task_id (int): 任务 ID。
        member_id (int): 成员 ID。

    Returns:
        bool: 删除成功返回 True，否则 False。
    """
    conn = get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM participations WHERE task_id = ? AND member_id = ?",
            (task_id, member_id),
        )
        conn.commit()
        logger.info(f"移除参与记录 task={task_id} member={member_id}")
        return cur.rowcount > 0
    finally:
        conn.close()


# ==================== 统计 ====================

def summary_all():
    """全体成员时长汇总。

    Returns:
        list[dict]: 每个字典包含 id, name, total_hours, task_count。
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
    """指定成员的时长明细及总计。

    Args:
        member_id (int): 成员 ID。

    Returns:
        dict | None: 包含 "member" 和 "records" 的字典；
                     找不到成员返回 None。
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


def summary_by_month():
    """按月统计任务数和总时长。

    Returns:
        list[dict]: 每个字典包含 month, task_count, total_hours。
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT substr(t.date, 1, 7) AS month,
               COUNT(DISTINCT t.id) AS task_count,
               IFNULL(SUM(p.hours), 0) AS total_hours
        FROM tasks t
        LEFT JOIN participations p ON p.task_id = t.id
        GROUP BY month
        ORDER BY month DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def summary_by_group():
    """按小组统计人数和总时长。

    Returns:
        list[dict]: 每个字典包含 group_name, member_count, total_hours。
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.group_name,
               COUNT(DISTINCT m.id) AS member_count,
               IFNULL(SUM(p.hours), 0) AS total_hours
        FROM members m
        LEFT JOIN participations p ON p.member_id = m.id
        GROUP BY m.group_name
        ORDER BY total_hours DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def never_participated():
    """从未参与任何任务的成员。

    Returns:
        list[dict]: 每个字典包含 id, name, group_name。
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.id, m.name, m.group_name
        FROM members m
        LEFT JOIN participations p ON p.member_id = m.id
        WHERE p.id IS NULL
        ORDER BY m.id
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def top_members(n=10):
    """时长排行榜前 n 名。

    Args:
        n (int): 返回的成员数量，默认 10。

    Returns:
        list[dict]: 汇总列表的前 n 项。
    """
    return summary_all()[:n]


# ==================== 工具 ====================

def humanize_date(date_str):
    """将日期字符串转换为“x 天前”等易读格式。

    Args:
        date_str (str): 日期字符串，格式 YYYY-MM-DD。

    Returns:
        str: 易读的时间描述，如“今天”、“3 天前”。
    """
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
    """导出汇总数据为 CSV 文件。

    Args:
        path (str | Path, optional): 导出路径，为 None 时使用默认路径
            (exports/summary.csv)。

    Returns:
        Path: 实际导出的文件路径。
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
    """导出任务列表为 CSV 文件。

    Args:
        path (str | Path, optional): 导出路径，为 None 时使用默认路径
            (exports/tasks.csv)。

    Returns:
        Path: 实际导出的文件路径。
    """
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


def backup_db():
    """备份数据库到 backups/ 目录。

    Returns:
        Path: 备份文件的完整路径。
    """
    backup_dir = BASE_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    name = f"backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    path = backup_dir / name
    shutil.copy(DB_PATH, path)
    logger.info(f"备份数据库到 {path}")
    return path