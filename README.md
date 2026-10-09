# 开发组任务登记及志愿时长分配系统

一个用于登记开发组任务、按规则分配志愿时长的管理系统。
同时提供 **命令行（CLI）** 和 **网页（Web）** 两种使用方式，
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
- Web 界面：标准库 `http.server` + 原生 HTML/CSS/JS，无第三方依赖

## 项目结构

```
task_system/
├── main.py              # CLI 入口
├── server.py            # Web 入口
├── pyproject.toml       # 打包配置
├── README.md
├── .gitignore
├── src/
│   ├── config.py        # 路径与配置
│   ├── db.py            # 数据库连接与建表
│   ├── services.py      # 业务逻辑
│   ├── cli.py           # 命令行界面
│   ├── colors.py        # 终端彩色输出与显示工具
│   └── logger.py        # 日志系统
├── templates/
│   └── index.html       # Web 页面
├── tests/
│   └── test_services.py # 单元测试
├── data/                # 运行时数据库
├── logs/                # 运行日志
├── backups/             # 数据库备份
└── exports/             # 导出的 CSV
```

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

### 一、命令行（CLI）

#### 菜单模式

```bash
python3 main.py
```

或安装后：

```bash
task-system
```

进入交互式菜单，按提示操作。

#### 命令模式

适合脚本调用或服务器环境：

```bash
python3 main.py summary                    # 打印全体汇总
python3 main.py list-members               # 列出成员
python3 main.py list-tasks                 # 列出任务
python3 main.py add-member --name 张三 --group 开发组
python3 main.py backup                     # 备份数据库
python3 main.py export-summary             # 导出汇总 CSV
```

### 二、网页（Web）

#### 启动服务

```bash
python3 server.py
```

启动后终端显示

```bash
服务已启动：http://127.0.0.1:34004
模板目录：/opt/task_system/templates
```

#### 访问

浏览器打开： `http://服务器IP:34004`

本地测试用： `http://127.0.0.1:34004` 或： `localhost:34004`

### 页面功能

顶部标签页切换，纯只读展示，数据与 CLI 共用同一数据库

| 标签  | 内容                      |
|-----|-------------------------|
| 汇总  | 全体成员时长汇总                |
| 成员  | 成员列表（ID、姓名、小组、备注）       |
| 任务  | 任务列表（ID、日期、任务名称、人数、总时长） |
| 按月  | 每月任务数与总时长               |
| 按组  | 每个小组的人数与总时长             |
| 排行榜 | 时长前十名成员                 |

| 接口                         | 说明     |
|----------------------------|--------|
| `GET /api/members`         | 	成员列表  |
| `GET /api/tasks`           | 	任务列表  |
| `GET /api/summary`         | 	全体汇总  |
| `GET/api/summary-by-month` | 	按月统计  |
| `GET/api/summary-by-group` | 	按组统计  |
| `GET/api/top-members`      | 	时长排行榜 |

示例

```bash
curl http://127.0.0.1:34004/api/members
```

#### 停止服务

在运行的终端按 `Ctrl+C` 。

### 数据库路径

默认数据库位于 `项目目录/data/app.db` ，可通过环境变量覆盖：

```bash
export APP_DB_PATH=/var/lib/task-system/app.db
python3 main.py
python3 server.py
```

CLI 和 Web 共用同一个数据库，数据实时同步。

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

### 全局命令

创建两个包装脚本，可在任意目录直接启动。

#### CLI 命令

```bash
cat > /usr/local/bin/task-cli << 'EOF'
#!/bin/bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export APP_DB_PATH="${APP_DB_PATH:-/var/lib/task-system/app.db}"
cd /opt/task_system
exec .venv/bin/python main.py "$@"
EOF

chmod +x /usr/local/bin/task-cli
```

使用：

```bash
task-cli              # 进菜单
task-cli summary      # 查看汇总
task-cli backup       # 备份数据库
```

#### Web 命令

```bash
cat > /usr/local/bin/task-web << 'EOF'
#!/bin/bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export APP_DB_PATH="${APP_DB_PATH:-/var/lib/task-system/app.db}"
cd /opt/task_system
exec .venv/bin/python server.py
EOF

chmod +x /usr/local/bin/task-web
```

使用：

```bash
task-web              # 启动 Web 服务
```

浏览器访问 `http://服务器IP:34004`。

#### 后台运行 Web

```bash
nohup task-web > /opt/task_system/logs/web.log 2>&1 &
```

查看进程：

```bash
ps aux | grep server.py
```

停止：

```bash
pkill -f server.py
```

### 防火墙与安全组

Web 服务默认端口 `34004`，需确保：

1. 服务器防火墙放行 34004 端口。
2. 云厂商安全组入方向放行 34004 端口。

测试端口是否监听：

```bash
ss -tlnp | grep 34004
```

## 许可

本项目为开发组内部练手任务，仅供学习交流使用。

## 版本

- `v1.0.0`：首个正式版，完整 CLI 功能、注释、单元测试
- `v1.1.0`：新增 Web 界面，支持只读展示与 JSON API