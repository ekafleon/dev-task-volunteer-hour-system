# tests/test_services.py
"""services 单元测试。

运行方式：python -m unittest discover tests -v
"""

import os
import tempfile
import unittest
from pathlib import Path

# 使用临时数据库，避免污染真实数据
TMP = tempfile.mkdtemp()
os.environ["APP_DB_PATH"] = str(Path(TMP) / "test.db")

from src import services  # noqa: E402
from src.db import init_db, get_conn  # noqa: E402


class TestServices(unittest.TestCase):
    """测试 services 模块的各项功能。"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化：创建数据库表。"""
        init_db()

    def setUp(self):
        """每个测试方法执行前清空所有表。"""
        conn = get_conn()
        conn.execute("DELETE FROM participations")
        conn.execute("DELETE FROM tasks")
        conn.execute("DELETE FROM members")
        conn.commit()
        conn.close()

    # ---------- 成员 ----------

    def test_add_member(self):
        """测试添加成员。"""
        services.add_member("张三")
        members = services.list_members()
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]["name"], "张三")

    def test_add_member_with_group(self):
        """测试添加成员时指定小组。"""
        services.add_member("李四", group_name="开发组")
        m = services.list_members()[0]
        self.assertEqual(m["group_name"], "开发组")

    def test_add_duplicate_member(self):
        """测试添加重复成员时抛出 ValueError。"""
        services.add_member("张三")
        with self.assertRaises(ValueError):
            services.add_member("张三")

    def test_update_member(self):
        """测试修改成员信息。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        services.update_member(mid, note="备注")
        self.assertEqual(services.list_members()[0]["note"], "备注")

    def test_delete_member(self):
        """测试删除成员。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        result = services.delete_member(mid)
        self.assertIsNotNone(result)
        self.assertEqual(len(services.list_members()), 0)

    def test_search_members(self):
        """测试按姓名模糊搜索成员。"""
        services.add_member("张三")
        services.add_member("张四")
        services.add_member("李五")
        results = services.search_members("张")
        self.assertEqual(len(results), 2)

    def test_list_groups(self):
        """测试获取所有小组名。"""
        services.add_member("张三", group_name="开发组")
        services.add_member("李四", group_name="创意组")
        services.add_member("王五", group_name="开发组")
        groups = services.list_groups()
        self.assertEqual(len(groups), 2)
        self.assertIn("开发组", groups)

    # ---------- 任务 ----------

    def test_add_task(self):
        """测试添加任务。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("测试任务", "", "2025-10-01", [(mid, 2.0)])
        self.assertIsNotNone(tid)
        self.assertEqual(len(services.list_tasks()), 1)

    def test_get_task_detail(self):
        """测试获取任务详情。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "描述", "2025-10-01", [(mid, 2.0)])
        detail = services.get_task_detail(tid)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["task"]["title"], "任务")
        self.assertEqual(len(detail["participants"]), 1)

    def test_delete_task(self):
        """测试删除任务。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "", "2025-10-01", [(mid, 2.0)])
        services.delete_task(tid)
        self.assertEqual(len(services.list_tasks()), 0)

    # ---------- 统计 ----------

    def test_summary_all(self):
        """测试全体成员汇总。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        services.add_task("任务1", "", "2025-10-01", [(mid, 2.0)])
        services.add_task("任务2", "", "2025-10-02", [(mid, 3.0)])
        rows = services.summary_all()
        self.assertEqual(rows[0]["total_hours"], 5.0)
        self.assertEqual(rows[0]["task_count"], 2)

    def test_summary_by_month(self):
        """测试按月统计。"""
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
        """测试按小组统计。"""
        services.add_member("张三", group_name="开发组")
        services.add_member("李四", group_name="创意组")
        mid1 = services.list_members()[0]["id"]
        services.add_task("任务", "", "2025-10-01", [(mid1, 2.0)])
        rows = services.summary_by_group()
        groups = {r["group_name"]: r for r in rows}
        self.assertEqual(groups["开发组"]["total_hours"], 2.0)
        self.assertEqual(groups["创意组"]["total_hours"], 0)

    def test_never_participated(self):
        """测试从未参与任务的成员查询。"""
        services.add_member("张三")
        services.add_member("李四")
        mid1 = services.list_members()[0]["id"]
        services.add_task("任务", "", "2025-10-01", [(mid1, 2.0)])
        rows = services.never_participated()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "李四")

    def test_top_members(self):
        """测试时长排行榜。"""
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
        """测试补录参与记录（更新已存在的记录）。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "", "2025-10-01", [(mid, 2.0)])

        action = services.upsert_participation(tid, mid, 3.0)
        self.assertEqual(action, "updated")
        detail = services.get_task_detail(tid)
        self.assertEqual(detail["participants"][0]["hours"], 3.0)

    def test_remove_participation(self):
        """测试移除参与记录。"""
        services.add_member("张三")
        mid = services.list_members()[0]["id"]
        tid = services.add_task("任务", "", "2025-10-01", [(mid, 2.0)])

        ok = services.remove_participation(tid, mid)
        self.assertTrue(ok)
        detail = services.get_task_detail(tid)
        self.assertEqual(len(detail["participants"]), 0)

    # ---------- 工具 ----------

    def test_humanize_date(self):
        """测试日期人性化显示。"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(services.humanize_date(today), "今天")

    def test_backup_db(self):
        """测试数据库备份。"""
        path = services.backup_db()
        self.assertTrue(Path(path).exists())


if __name__ == "__main__":
    unittest.main()
