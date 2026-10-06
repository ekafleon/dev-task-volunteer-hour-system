# src/db.py
"""数据库连接与初始化模块。

提供获取数据库连接的函数 get_conn()，以及初始化表结构的 init_db()。
使用 SQLite，开启外键约束、WAL 日志模式，并设置忙等待超时。
"""

import sqlite3

from src.config import DB_PATH


def get_conn():
    """创建并返回一个 SQLite 数据库连接。

    连接配置：
    - row_factory 设置为 sqlite3.Row，使查询结果可按列名访问。
    - 开启外键约束（PRAGMA foreign_keys = ON）。
    - 使用 WAL 日志模式，提高并发读写性能。
    - 设置忙等待超时为 5000 毫秒。

    Returns:
        sqlite3.Connection: 已配置好的数据库连接对象。
    """
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db():
    """初始化数据库表结构。

    创建以下表（如果不存在）：
    - members: 成员表，包含 id, name, note, group_name。
    - tasks: 任务表，包含 id, title, description, date, created_at。
    - participations: 参与记录表，包含 id, task_id, member_id, hours。
      外键关联 tasks 和 members，并设置级联删除。
    - 创建必要的索引以加速查询。

    同时兼容旧版本数据库：如果 members 表缺少 group_name 列，则自动添加。
    """
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL UNIQUE,
            note    TEXT NOT NULL DEFAULT '',
            group_name TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            date        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS participations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     INTEGER NOT NULL,
            member_id   INTEGER NOT NULL,
            hours       REAL NOT NULL CHECK (hours > 0),
            FOREIGN KEY (task_id)   REFERENCES tasks(id)   ON DELETE CASCADE,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
            UNIQUE (task_id, member_id)
        );

        CREATE INDEX IF NOT EXISTS idx_part_member ON participations(member_id);
        CREATE INDEX IF NOT EXISTS idx_part_task   ON participations(task_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_date  ON tasks(date);
    """)

    # 兼容旧数据库：如果 members 表缺少 group_name 列，则添加
    cols = conn.execute("PRAGMA table_info(members)").fetchall()
    col_names = [c["name"] for c in cols]
    if "group_name" not in col_names:
        conn.execute("ALTER TABLE members \
                     ADD COLUMN group_name TEXT NOT NULL DEFAULT ''")

    conn.commit()
    conn.close()