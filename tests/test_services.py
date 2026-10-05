# tests/test_services.py
"""services 单元测试。运行：python -m unittest discover tests -v"""

import os
import tempfile
import unittest
from pathlib import Path

# 用临时数据库，避免污染真实数据
TMP = tempfile.mkdtemp()
os.environ["APP_DB_PATH"] = str(Path(TMP) / "test.db")

from src import services  # noqa: E402
from src.db import init_db, get_conn  # noqa: E402


class TestServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        """每个测试前清空表。"""
        conn = get_conn()
        conn.execute("DELETE FROM participations")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM members")
        conn.commit()
        conn.close()

    # ---------- 成员 ----------

    def test_add_member(self):
        services.add_member("张三")
        members = services.list_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]["name"], "张三")

    def test_add_member_with_group(self):
        services.add_member("李四", group_name="开发组")
        m = services.list_members()[0]
        self.assertEqual(m["group_name"], "开发组")

    def test_add_duplicate_member(self):
        services.add_member("张三")
        with self.assertRaises(ValueError):
            services.add_member("张三")

    def test_update_member(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        services.update_member(mid, note="备注")
        self.assertEqual(services.list_members()[0]["note"], "备注")

    def test_delete_member(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        result = services.delete_member(mid)
        self.assertIsNotNone(result)
        self.assertEqual(len(services.list_members()), 0)

    def test_search_members(self):
        services.add_member("张三")
        services.add_member("张四")
        services.add_member("李五")
        results = services.search_members("张")
        self.assertEqual(len(results), 2)

    def test_list_groups(self):
        services.add_member("张三", group_name="开发组")
        services.add_member("李四", group_name="宣传组")
        services.add_member("王五", group_name="开发组")
        groups = services.list_groups()
        self.assertEqual(len(groups), 2)
        self.assertIn("开发组", groups)

    # ---------- 任务 ----------

    def test_add_task(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("测试任务", "", "2025-10-01", [(mid, 2.0)])
        self.assertIsNotNone(tid)
        self.assertEqual(len(services.list_tasks()), 1)

    def test_get_task_detail(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "描述", "2025-10-01", [(mid, 2.0)])
        detail = services.get_task_detail(tid)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["task"]["title"], "任务")
        self.assertEqual(len(detail["participants"]), 1)

    def test_delete_task(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "", "2025-10-01", [(mid, 2.0)])
        services.delete_task(tid)
        self.assertEqual(len(services.list_tasks()), 0)

    # ---------- 统计 ----------

    def test_summary_all(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        services.add_task("任务1", "", "2025-10-01", [(mid, 2.0)])
        services.add_task("任务2", "", "2025-10-02", [(mid, 3.0)])
        rows = services.summary_all()
        self.assertEqual(rows[0]["total_hours"], 5.0)
        self.assertEqual(rows[0]["task_count"], 2)

    def test_summary_by_month(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        services.add_task("任务1", "", "2025-10-01", [(mid, 2.0)])
        services.add_task("任务2", "", "2025-10-15", [(mid, 3.0)])
        services.add_task("任务3", "", "2025-11-01", [(mid, 1.0)])
        rows = services.summary_by_month()
        months = {r["month"]: r for r in rows}
        self.assertEqual(months["2025-10"]["task_count"], 2)
        self.assertEqual(months["2025-10"]["total_hours"], 5.0)
        self.assertEqual(months["2025-11"]["total_hours"], 1.0)

    def test_summary_by_group(self):
        services.add_member("张三", group_name="开发组")
        services.add_member("李四", group_name="宣传组")
        mid1 = services.list_members()[0]["id"]
        services.add_task("任务", "", "2025-10-01", [(mid1, 2.0)])
        rows = services.summary_by_group()
        groups = {r["group_name"]: r for r in rows}
        self.assertEqual(groups["开发组"]["total_hours"], 2.0)
        self.assertEqual(groups["宣传组"]["total_hours"], 0)

    def test_never_participated(self):
        services.add_member("张三")
        services.add_member("李四")
        mid1 = services.list_members()[0]["id"]
        services.add_task("任务", "", "2025-10-01", [(mid1, 2.0)])
        rows = services.never_participated()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "李四")

    def test_top_members(self):
        services.add_member("张三")
        services.add_member("李四")
        mid1 = services.list_members()[0]["id"]
        mid2 = services.list_members()[1]["id"]
        services.add_task("任务", "", "2025-10-01", [(mid1, 5.0), (mid2, 2.0)])
        rows = services.top_members(2)
        self.assertEqual(rows[0]["name"], "张三")
        self.assertEqual(rows[0]["total_hours"], 5.0)

    # ---------- 参与记录 ----------

    def test_upsert_participation(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "", "2025-10-01", [(mid, 2.0)])

        action = services.upsert_participation(tid, mid, 3.0)
        self.assertEqual(action, "updated")
        detail = services.get_task_detail(tid)
        self.assertEqual(detail["participants"][0]["hours"], 3.0)

    def test_remove_participation(self):
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "", "2025-10-01", [(mid, 2.0)])

        ok = services.remove_participation(tid, mid)
        self.assertTrue(ok)
        detail = services.get_task_detail(tid)
        self.assertEqual(len(detail["participants"]), 0)

    # ---------- 工具 ----------

    def test_humanize_date(self):
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(services.humanize_date(today), "今天")

    def test_backup_db(self):
        path = services.backup_db()
        self.assertTrue(Path(path).exists())


if __name__ == "__main__":
    unittest.main()