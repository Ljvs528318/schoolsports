"""
快速创建三个示例赛事
赛事1: 乒乓球男子单打 - 个人赛 + 积分循环赛
赛事2: 羽毛球男子单打 - 个人赛 + 单淘汰赛
赛事3: 篮球联赛 - 团体赛 + 混合赛（积分+淘汰）
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import db, Competition, User
from app import create_app

app = create_app()

with app.app_context():
    # 查找管理员用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("错误: 找不到管理员用户 'admin'")
        sys.exit(1)

    print(f"使用用户 '{admin.username}' (ID={admin.id}) 创建赛事\n")

    # 赛事列表
    competitions = [
        {
            'name': '2026年校园乒乓球男子单打锦标赛',
            'sport_type': '乒乓球',
            'comp_type': 'individual',  # 个人赛
            'format': 'round_robin',    # 积分循环赛
            'description': '校园乒乓球男子单打比赛，采用积分循环赛制，所有选手进行单循环比赛，按积分排名。',
            'rules': '1. 采用国际乒联最新规则\n2. 每场比赛采用5局3胜制\n3. 每局11分制，10平后需领先2分\n4. 循环赛胜一场得3分，平得1分，负得0分\n5. 最终按积分排名，积分相同看胜负关系',
            'venue': '学校体育馆乒乓球室',
            'max_teams': 16,  # 最多16人参赛
            'team_size': 1,
            'win_points': 3,
            'draw_points': 1,
            'loss_points': 0,
            'top_advance': 8,
            'status': 'open',  # 直接开放报名
        },
        {
            'name': '2026年校园羽毛球男子单打挑战赛',
            'sport_type': '羽毛球',
            'comp_type': 'individual',  # 个人赛
            'format': 'knockout',      # 单淘汰赛
            'description': '校园羽毛球男子单打挑战赛，采用单淘汰赛制，一战定胜负，紧张刺激！',
            'rules': '1. 采用世界羽联最新规则\n2. 每场比赛采用3局2胜制\n3. 每局21分制，20平后需领先2分，29平后先到30分者胜\n4. 单淘汰赛制，输一场即被淘汰\n5. 决赛胜者为冠军',
            'venue': '学校体育馆羽毛球场',
            'max_teams': 32,  # 淘汰赛建议2的幂次
            'team_size': 1,
            'win_points': 3,
            'draw_points': 1,
            'loss_points': 0,
            'top_advance': 8,
            'status': 'open',  # 直接开放报名
        },
        {
            'name': '2026年校园篮球联赛',
            'sport_type': '篮球',
            'comp_type': 'team',      # 团体赛
            'format': 'hybrid',       # 混合赛（积分+淘汰）
            'description': '校园篮球联赛，采用混合赛制：小组赛阶段采用积分循环赛，小组前两名晋级淘汰赛阶段。',
            'rules': '1. 采用国际篮联最新规则\n2. 每队最多12人，上场5人\n3. 比赛分4节，每节10分钟\n4. 小组赛阶段：单循环，胜得3分，平得1分，负得0分\n5. 小组前两名晋级8强淘汰赛\n6. 淘汰赛阶段：单场淘汰制，胜者晋级',
            'venue': '学校篮球场',
            'max_teams': 16,  # 最多16支队伍
            'team_size': 12,   # 每队最多12人
            'win_points': 3,
            'draw_points': 1,
            'loss_points': 0,
            'top_advance': 8,  # 小组赛后前8名进淘汰赛
            'status': 'open',  # 直接开放报名
        }
    ]

    created = 0
    skipped = 0

    for comp_data in competitions:
        # 检查是否已存在同名赛事
        existing = Competition.query.filter_by(name=comp_data['name']).first()
        if existing:
            print(f"跳过: 赛事「{comp_data['name']}」已存在 (ID={existing.id})")
            skipped += 1
            continue

        # 创建赛事
        comp = Competition(
            name=comp_data['name'],
            sport_type=comp_data['sport_type'],
            comp_type=comp_data['comp_type'],
            format=comp_data['format'],
            description=comp_data['description'],
            rules=comp_data['rules'],
            venue=comp_data['venue'],
            max_teams=comp_data['max_teams'],
            team_size=comp_data['team_size'],
            win_points=comp_data['win_points'],
            draw_points=comp_data['draw_points'],
            loss_points=comp_data['loss_points'],
            top_advance=comp_data['top_advance'],
            status=comp_data['status'],
            created_by=admin.id
        )

        # 设置时间（可选）
        from datetime import datetime, timedelta
        now = datetime.now()
        comp.reg_start = now
        comp.reg_end = now + timedelta(days=7)
        comp.start_date = now + timedelta(days=10)
        comp.end_date = now + timedelta(days=30)

        db.session.add(comp)
        created += 1
        print(f"创建: 赛事「{comp_data['name']}」")
        print(f"       参赛形式: {comp_data['comp_type']} | 赛制: {comp_data['format']}")
        print(f"       运动项目: {comp_data['sport_type']} | 状态: {comp_data['status']}")
        print()

    # 提交到数据库
    if created > 0:
        try:
            db.session.commit()
            print(f"✅ 成功创建 {created} 个赛事！")
            print(f"   跳过 {skipped} 个已存在的赛事")
            print("\n你可以：")
            print("  1. 在浏览器中访问 http://localhost:5000/ 查看赛事列表")
            print("  2. 点击赛事名称查看详情")
            print("  3. 学生用户可以报名参赛")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建失败: {e}")
            sys.exit(1)
    else:
        print(f"ℹ️  所有赛事已存在，无需创建（跳过 {skipped} 个）")
