# src/db.py
import sqlite3
from src.config import DB_PATH


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS members (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name    TEXT NOT NULL UNIQUE,
            note    TEXT NOT NULL DEFAULT ''
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
    conn.commit()
    conn.close()
