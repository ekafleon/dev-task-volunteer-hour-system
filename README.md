# 开发组任务登记及志愿时长分配系统

一个用于登记开发组任务、按规则分配志愿时长的命令行工具。
支持成员管理、任务管理、时长统计、报表导出与数据库备份。

## 功能

### 成员管理
- 添加、修改、删除成员
- 按姓名模糊搜索
- 设置成员小组，按小组查看
- 查看成员列表

### 任务管理
- 登记任务，支持多次批量添加参与者
- 查看任务列表与详情
- 修改、删除任务
- 时长补录：为已有任务新增或更新成员时长
- 移除单条参与记录
- 按关键词、日期范围搜索任务
- 导出任务列表为 CSV

### 时长统计
- 全体成员汇总
- 个人明细与总计
- 按月统计
- 按小组统计
- 从未参与任务的成员
- 时长排行榜
- 导出汇总 CSV

### 系统工具
- 备份数据库到 `backups/` 目录

## 技术栈

- Python 3.8+
- SQLite（标准库 `sqlite3`）

## 安装

### 方式一：直接运行

```bash
git clone https://github.com/ekafleon/dev-task-volunteer-hour-system.git
cd dev-task-volunteer-hour-system
python3 main.py
```

仅需python 3.8+，无第三方依赖。

### 方式二：pip安装

```bash
git clone https://github.com/ekafleon/dev-task-volunteer-hour-system.git
cd dev-task-volunteer-hour-system

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
```

安装后即可使用 `task-system` 命令

## 使用方式

### 菜单模式

```bash
python3 main.py
```

或安装后：

```bash
task-system
```

进入交互式菜单，按提示操作。

### 命令模式

适合脚本调用或服务器环境：

```bash
python3 main.py summary                    # 打印全体汇总
python3 main.py list-members               # 列出成员
python3 main.py list-tasks                 # 列出任务
python3 main.py add-member --name 张三 --group 开发组
python3 main.py backup                     # 备份数据库
python3 main.py export-summary             # 导出汇总 CSV
```

### 数据库路径

默认数据库位于 `项目目录/data/app.db` ，可通过环境变量覆盖：

```bash
export APP_DB_PATH=/var/lib/task-system/app.db
python3 main.py
```
## 数据说明

### 数据库表

- `members`：成员表（ID、姓名、备注、小组）
- `tasks`：任务表（ID、标题、描述、日期、创建日期）
- `participations`：参与记录表（ID、任务ID、成员ID、时长）

参与记录同样外键关联任务和成员，删除任务或成员时自动机连你删除相关记录。

### 数据持久化

数据库使用SQLite，数据保存在单个文件内，程序关闭后不丢失。

### 备份

在「系统工具 -> 备份数据库中」可一键备份，备份文件将保存在 `backups/` 目录，文件名带时间戳。

## 开发

### 运行单元测试

```bash
cd 项目根目录
source .venv/bin/activate
python -m unittest discover tests -v
```

### 日志

运行日志写入 `logs/app.log` ，包含时间、级别、模块名和消息。查看日志：

```bash
tail -f logs/app.log
```

## 部署到Linux服务器

```bash
git clone https://github.com/ekafleon/dev-task-volunteer-hour-system.git /opt/task_system
cd /opt/task_system

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

mkdir -p /var/lib/task-system

export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export APP_DB_PATH=/var/lib/task-system/app.db

python3 main.py
```

### 包装脚本

在 `/usr/local/bin/task-system` 创建包装脚本，可在任意目录直接运行：

```bash
#!/bin/bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export APP_DB_PATH="/var/lib/task-system/app.db"
cd /opt/task_system
exec .venv/bin/python main.py "$@"
```

```bash
chmod +x /usr/local/bin/task-system
task-system
```

## 许可

本项目为开发组内部练手任务，仅供学习交流使用。
