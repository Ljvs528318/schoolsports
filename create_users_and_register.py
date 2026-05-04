"""
注册16个学生用户，并组队报名参加2026年校园篮球联赛
- 创建16个学生账号
- 组成4支篮球队（每队4人）
- 提交报名申请
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import db, User, Competition, Registration
from app import create_app

app = create_app()

with app.app_context():
    # 查找篮球联赛
    basketball_comp = Competition.query.filter_by(name='2026年校园篮球联赛').first()
    if not basketball_comp:
        print("错误: 找不到赛事「2026年校园篮球联赛」")
        sys.exit(1)

    print(f"目标赛事: {basketball_comp.name} (ID={basketball_comp.id})")
    print(f"  参赛形式: {basketball_comp.comp_type}")
    print(f"  赛制: {basketball_comp.format}")
    print(f"  每队人数: {basketball_comp.team_size}")
    print()

    # 16个学生的测试数据
    students_data = [
        {'username': 'student01', 'real_name': '张伟', 'student_id': '2024001', 'class_name': '高三1班'},
        {'username': 'student02', 'real_name': '李娜', 'student_id': '2024002', 'class_name': '高三2班'},
        {'username': 'student03', 'real_name': '王强', 'student_id': '2024003', 'class_name': '高三3班'},
        {'username': 'student04', 'real_name': '赵敏', 'student_id': '2024004', 'class_name': '高三1班'},
        {'username': 'student05', 'real_name': '刘洋', 'student_id': '2024005', 'class_name': '高三2班'},
        {'username': 'student06', 'real_name': '陈杰', 'student_id': '2024006', 'class_name': '高三3班'},
        {'username': 'student07', 'real_name': '杨丽', 'student_id': '2024007', 'class_name': '高三1班'},
        {'username': 'student08', 'real_name': '黄明', 'student_id': '2024008', 'class_name': '高三2班'},
        {'username': 'student09', 'real_name': '周芳', 'student_id': '2024009', 'class_name': '高三3班'},
        {'username': 'student10', 'real_name': '吴刚', 'student_id': '2024010', 'class_name': '高三1班'},
        {'username': 'student11', 'real_name': '郑华', 'student_id': '2024011', 'class_name': '高三2班'},
        {'username': 'student12', 'real_name': '孙磊', 'student_id': '2024012', 'class_name': '高三3班'},
        {'username': 'student13', 'real_name': '马超', 'student_id': '2024013', 'class_name': '高三1班'},
        {'username': 'student14', 'real_name': '朱婷', 'student_id': '2024014', 'class_name': '高三2班'},
        {'username': 'student15', 'real_name': '胡歌', 'student_id': '2024015', 'class_name': '高三3班'},
        {'username': 'student16', 'real_name': '林丹', 'student_id': '2024016', 'class_name': '高三1班'},
    ]

    # 密码统一为 student123
    default_password = 'student123'

    # 组队方案：4支队伍，每队4人
    teams = [
        {'name': '猛龙队', 'members': [0, 1, 2, 3]},
        {'name': '飞鹰队', 'members': [4, 5, 6, 7]},
        {'name': '雄狮队', 'members': [8, 9, 10, 11]},
        {'name': '战狼队', 'members': [12, 13, 14, 15]},
    ]

    print("=" * 60)
    print("第一步: 创建16个学生用户")
    print("=" * 60)

    created_users = []
    for data in students_data:
        # 检查用户是否已存在
        existing = User.query.filter(
            (User.username == data['username']) | (User.student_id == data['student_id'])
        ).first()

        if existing:
            print(f"  跳过: 用户 {data['username']} / {data['student_id']} 已存在")
            created_users.append(existing)
            continue

        # 创建新用户
        user = User(
            username=data['username'],
            email=f"{data['username']}@school.edu",
            real_name=data['real_name'],
            student_id=data['student_id'],
            class_name=data['class_name'],
            role='student',
            is_active_user=True
        )
        user.set_password(default_password)
        db.session.add(user)
        db.session.flush()  # 获取ID

        created_users.append(user)
        print(f"  ✓ 创建用户: {data['username']} ({data['real_name']}, {data['student_id']})")

    try:
        db.session.commit()
        print(f"\n✅ 用户创建完成！共 {len(created_users)} 个学生用户\n")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 用户创建失败: {e}")
        sys.exit(1)

    print("=" * 60)
    print("第二步: 组队报名篮球联赛")
    print("=" * 60)

    registration_count = 0

    for team in teams:
        team_name = team['name']
        member_indices = team['members']

        # 获取队长（第一个队员）
        captain = created_users[member_indices[0]]

        # 检查是否已报名
        existing_reg = Registration.query.filter_by(
            competition_id=basketball_comp.id,
            user_id=captain.id
        ).first()

        if existing_reg:
            print(f"\n  跳过: 队伍「{team_name}」已报名 (队长: {captain.username})")
            continue

        # 构建队员列表 JSON
        members_list = []

        for idx, member_idx in enumerate(member_indices):
            user = created_users[member_idx]
            members_list.append({
                'student_id': user.student_id,
                'class_name': user.class_name,
                'name': user.real_name,
                'photo': user.avatar or '',
                'is_captain': idx == 0  # 第一个人为队长
            })

        # 创建报名记录
        reg = Registration(
            competition_id=basketball_comp.id,
            user_id=captain.id,  # 队长作为报名人
            team_name=team_name,
            team_members=json.dumps(members_list, ensure_ascii=False),
            status='pending',  # 待审核
            note=f'自动创建的测试报名 - {team_name}'
        )
        db.session.add(reg)
        registration_count += 1

        print(f"\n  ✓ 提交报名: 队伍「{team_name}」")
        print(f"    队长: {captain.real_name} ({captain.username})")
        print(f"    队员: {', '.join([created_users[i].real_name for i in member_indices])}")

    try:
        db.session.commit()
        print(f"\n✅ 报名完成！共提交 {registration_count} 个队伍报名")
        print(f"   所有报名状态: 待审核 (pending)\n")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 报名失败: {e}")
        sys.exit(1)

    print("=" * 60)
    print("第三步: 汇总信息")
    print("=" * 60)
    print(f"\n📊 数据统计:")
    print(f"  - 学生用户总数: {len(created_users)}")
    print(f"  - 报名队伍数: {registration_count}")
    print(f"  - 参赛总人数: {len(students_data)}")

    print(f"\n👥 队伍列表:")
    for team in teams:
        captain = created_users[team['members'][0]]
        print(f"  - {team['name']} (队长: {captain.real_name})")

    print(f"\n🔐 登录信息:")
    print(f"  - 用户名格式: student01 ~ student16")
    print(f"  - 统一密码: {default_password}")

    print(f"\n📝 下一步操作建议:")
    print(f"  1. 以教师/管理员身份登录")
    print(f"  2. 进入赛事详情 → 报名管理")
    print(f"  3. 审批通过这 {registration_count} 个队伍报名")
    print(f"  4. 开始分组和赛程编排")

    print(f"\n🌐 访问地址:")
    print(f"  - 首页: http://localhost:5000/")
    print(f"  - 赛事详情: http://localhost:5000/competition/{basketball_comp.id}")
    print()
