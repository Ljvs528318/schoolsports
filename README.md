# 校园体育赛事管理系统

基于 Flask 的校园体育赛事管理平台，支持赛事发布、报名管理、抽签分组、赛程生成、成绩录入及积分排名等完整业务流程。

## 项目简介

本系统旨在为学校体育赛事提供一套完整的数字化管理解决方案。支持多种赛制（积分循环赛、单淘汰赛、混合赛），可满足篮球、足球、乒乓球、田径等多种体育项目的管理需求。

## 功能介绍

### 1. 用户与权限管理
- **三种角色**：管理员、教师、学生
- **用户注册/登录**：支持邮箱注册、头像上传、个人资料修改
- **权限控制**：管理员和教师可进入管理后台

### 2. 赛事管理
- **创建赛事**：设置赛事名称、类型、赛制、规则、场地、时间等
- **三种赛制**：
  - 积分循环赛：所有队伍相互比赛，按积分排名
  - 单淘汰赛：失败即淘汰，直至决出冠军
  - 混合赛：小组赛+淘汰赛，先积分后淘汰
- **赛事状态**：草稿 → 报名中 → 进行中 → 已结束 / 已取消

### 3. 报名管理
- **个人赛报名**：学生直接报名参赛
- **团体赛报名**：队长代团队报名，可添加队员信息（学号、班级、姓名、照片）
- **报名审批**：教师审核报名申请，批量审批通过

### 4. 抽签分组
- 支持随机分组和手动分组
- 自定义分组数量（A组、B组等）
- 支持种子队设置

### 5. 赛程管理
- **自动生成赛程**：
  - 循环赛：生成所有队伍两两对决场次
  - 淘汰赛：自动构建晋级树（16强→8强→4强→决赛）
  - 混合赛：小组赛结束后自动生成淘汰赛
- **赛程展示**：按阶段/轮次分组展示比赛场次
- **实时积分榜**：自动计算并排名

### 6. 比赛结果管理
- 录入比赛成绩（主客队比分）
- 自动判断胜负、更新积分
- 淘汰赛自动晋级
- 支持结果重置

### 7. 公告系统
- 发布赛事公告
- 支持置顶公告
- 可关联特定赛事

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Flask 3.0.3 |
| 数据库 | SQLite + SQLAlchemy 2.0.30 |
| 用户认证 | Flask-Login 0.6.3 |
| 表单处理 | Flask-WTF 1.2.1 |
| 前端框架 | Bootstrap 5.3 + Bootstrap Icons |
| Python版本 | 3.10+ |

## 目录结构

```
schoolsports/
├── app/                        # 应用主目录
│   ├── __init__.py             # 应用工厂函数
│   ├── models.py               # 数据模型定义
│   ├── blueprints/             # 蓝图模块
│   │   ├── __init__.py
│   │   ├── admin.py            # 管理后台（用户/公告）
│   │   ├── auth.py             # 认证（登录/注册/个人资料）
│   │   ├── competition.py       # 赛事管理
│   │   ├── main.py             # 首页
│   │   └── schedule.py          # 赛程管理
│   ├── static/                  # 静态资源
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   └── uploads/            # 上传文件（头像、照片）
│   │       ├── avatars/
│   │       └── photos/
│   └── templates/              # Jinja2 模板
│       ├── base.html           # 基础模板
│       ├── 403.html
│       ├── 404.html
│       ├── admin/              # 管理后台模板
│       ├── auth/               # 认证模板
│       ├── competition/         # 赛事模板
│       ├── main/               # 首页模板
│       └── schedule/            # 赛程模板
├── config.py                   # 配置文件
├── requirements.txt            # Python 依赖
├── run.py                      # 应用入口
├── sports.db                   # SQLite 数据库文件
└── add_teams_and_approve.py    # 辅助脚本（添加测试数据）
└── create_sample_comps.py       # 辅助脚本（创建示例赛事）
└── create_users_and_register.py # 辅助脚本（创建测试用户）
```

## 数据库

### 数据表结构

| 表名 | 说明 |
|------|------|
| `users` | 用户表（用户名、邮箱、密码、角色、头像等） |
| `competitions` | 赛事表（名称、类型、赛制、规则、场地、状态等） |
| `registrations` | 报名表（关联赛事和用户，含队员JSON） |
| `groups` | 分组表（A组、B组等） |
| `group_members` | 分组成员表（积分、胜负记录） |
| `matches` | 比赛场次表（主客队、比分、状态、轮次等） |
| `announcements` | 公告表（标题、内容、置顶等） |

### 关系图

```
User ─┬─< Registration ─< GroupMember >─ Group
      │                              │
      └─< Announcement               │
                                      │
Competition ─< Registration ─< GroupMember
      │
      └─< Match
      │
      └─< Announcement
```

## 安装配置

### 1. 环境要求

- Python 3.10 或更高版本
- pip 包管理器

### 2. 安装步骤

```bash
# 1. 克隆或下载项目后，进入项目目录
cd schoolsports

# 2. 创建虚拟环境（推荐）
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

### 3. 配置说明

编辑 `config.py` 文件：

```python
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'sports.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 最大上传 16MB
```

### 4. 启动服务器

```bash
python run.py
```

服务器启动后，访问 http://localhost:5000

### 5. 生产环境部署（可选）

建议使用 Gunicorn：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

或使用 Nginx + uWSGI 部署。

## 数据初始化

### 自动初始化

首次启动服务器时，系统会自动：
1. 创建数据库表
2. 创建默认管理员账号

### 默认管理员账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

**首次登录后请立即修改密码！**

### 测试数据脚本

项目提供了几个辅助脚本用于测试：

#### 添加测试用户并报名
```bash
python create_users_and_register.py
```

#### 创建示例赛事
```bash
python create_sample_comps.py
```

#### 添加团队并审批
```bash
python add_teams_and_approve.py
```

### 重置数据库

如果需要重置所有数据，删除 `sports.db` 文件后重新启动服务器即可。

## 页面访问

| 页面 | URL | 权限 |
|------|-----|------|
| 首页 | `/` | 公开 |
| 赛事列表 | `/competition/` | 公开 |
| 登录 | `/auth/login` | 公开 |
| 注册 | `/auth/register` | 公开 |
| 管理后台 | `/admin/` | 教师/管理员 |
| 用户管理 | `/admin/users` | 管理员 |
| 公告管理 | `/admin/announcements` | 教师/管理员 |

## 开发说明

### 项目结构

- **蓝图模式**：按功能模块划分蓝图，便于维护
- **ORM模式**：使用 SQLAlchemy 进行数据库操作
- **模板继承**：使用 Jinja2 模板继承简化页面开发

### 添加新功能

1. 在 `app/blueprints/` 创建新蓝图
2. 在 `app/templates/` 创建对应模板
3. 在 `app/__init__.py` 注册蓝图
4. 更新模型：`app/models.py`

## 许可证

本项目仅供学习交流使用。
