"""
再注册16个用户组成4支新篮球队，报名篮球联赛，
同时自动审批所有8支队伍的报名（4旧+4新）。
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
    print()

    # ============================================================
    # 第一步：再创建16个学生用户 (student17 ~ student32)
    # ============================================================
    students_data = [
        {'username': 'student17', 'real_name': '徐亮', 'student_id': '2024017', 'class_name': '高三4班'},
        {'username': 'student18', 'real_name': '何静', 'student_id': '2024018', 'class_name': '高三4班'},
        {'username': 'student19', 'real_name': '高峰', 'student_id': '2024019', 'class_name': '高三5班'},
        {'username': 'student20', 'real_name': '宋雪', 'student_id': '2024020', 'class_name': '高三5班'},
        {'username': 'student21', 'real_name': '邓超', 'student_id': '2024021', 'class_name': '高三4班'},
        {'username': 'student22', 'real_name': '曹颖', 'student_id': '2024022', 'class_name': '高三5班'},
        {'username': 'student23', 'real_name': '彭勇', 'student_id': '2024023', 'class_name': '高三6班'},
        {'username': 'student24', 'real_name': '潘丽', 'student_id': '2024024', 'class_name': '高三6班'},
        {'username': 'student25', 'real_name': '田磊', 'student_id': '2024025', 'class_name': '高三4班'},
        {'username': 'student26', 'real_name': '董婷', 'student_id': '2024026', 'class_name': '高三5班'},
        {'username': 'student27', 'real_name': '姜涛', 'student_id': '2024027', 'class_name': '高三6班'},
        {'username': 'student28', 'real_name': '钟琳', 'student_id': '2024028', 'class_name': '高三4班'},
        {'username': 'student29', 'real_name': '汪峰', 'student_id': '2024029', 'class_name': '高三5班'},
        {'username': 'student30', 'real_name': '范冰', 'student_id': '2024030', 'class_name': '高三6班'},
        {'username': 'student31', 'real_name': '谢军', 'student_id': '2024031', 'class_name': '高三6班'},
        {'username': 'student32', 'real_name': '韩梅', 'student_id': '2024032', 'class_name': '高三4班'},
    ]

    default_password = 'student123'

    # 新的4支队伍
    new_teams = [
        {'name': '猎豹队', 'members': [0, 1, 2, 3]},   # student17~20
        {'name': '雷霆队', 'members': [4, 5, 6, 7]},   # student21~24
        {'name': '旋风队', 'members': [8, 9, 10, 11]}, # student25~28
        {'name': '火箭队', 'members': [12, 13, 14, 15]}, # student29~32
    ]

    print("=" * 60)
    print("第一步: 创建16个新学生用户 (student17 ~ student32)")
    print("=" * 60)

    new_users = []
    for data in students_data:
        existing = User.query.filter(
            (User.username == data['username']) | (User.student_id == data['student_id'])
        ).first()

        if existing:
            print(f"  跳过: 用户 {data['username']} 已存在")
            new_users.append(existing)
            continue

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
        db.session.flush()
        new_users.append(user)
        print(f"  ✓ 创建用户: {data['username']} ({data['real_name']}, {data['student_id']})")

    try:
        db.session.commit()
        print(f"\n✅ 新用户创建完成！\n")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 用户创建失败: {e}")
        sys.exit(1)

    # ============================================================
    # 第二步：新队伍报名篮球联赛
    # ============================================================
    print("=" * 60)
    print("第二步: 4支新队伍报名篮球联赛")
    print("=" * 60)

    new_reg_count = 0

    for team in new_teams:
        team_name = team['name']
        member_indices = team['members']
        captain = new_users[member_indices[0]]

        # 检查是否已报名
        existing_reg = Registration.query.filter_by(
            competition_id=basketball_comp.id,
            user_id=captain.id
        ).first()

        if existing_reg:
            print(f"  跳过: 队伍「{team_name}」已报名")
            continue

        # 构建队员列表
        members_list = []
        for idx, member_idx in enumerate(member_indices):
            user = new_users[member_idx]
            members_list.append({
                'student_id': user.student_id,
                'class_name': user.class_name,
                'name': user.real_name,
                'photo': user.avatar or '',
                'is_captain': idx == 0
            })

        reg = Registration(
            competition_id=basketball_comp.id,
            user_id=captain.id,
            team_name=team_name,
            team_members=json.dumps(members_list, ensure_ascii=False),
            status='pending',
            note=f'自动创建的测试报名 - {team_name}'
        )
        db.session.add(reg)
        new_reg_count += 1

        print(f"  ✓ 提交报名: 队伍「{team_name}」")
        print(f"    队长: {captain.real_name} ({captain.username})")
        print(f"    队员: {', '.join([new_users[i].real_name for i in member_indices])}")

    try:
        db.session.commit()
        print(f"\n✅ 新队伍报名完成！共提交 {new_reg_count} 个报名\n")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 报名失败: {e}")
        sys.exit(1)

    # ============================================================
    # 第三步：自动审批所有待审报名（包括之前的4支+新的4支）
    # ============================================================
    print("=" * 60)
    print("第三步: 自动审批所有待审报名")
    print("=" * 60)

    pending_regs = Registration.query.filter_by(
        competition_id=basketball_comp.id,
        status='pending'
    ).all()

    approved_count = 0
    for reg in pending_regs:
        reg.status = 'approved'
        approved_count += 1

        # 获取队名
        team_name = reg.team_name or (reg.user.real_name if reg.user else f'ID:{reg.id}')
        print(f"  ✓ 审批通过: {team_name}")

    try:
        db.session.commit()
        print(f"\n✅ 审批完成！共通过 {approved_count} 个报名\n")
    except Exception as e:
        db.session.rollback()
        print(f"❌ 审批失败: {e}")
        sys.exit(1)

    # ============================================================
    # 第四步：汇总信息
    # ============================================================
    print("=" * 60)
    print("第四步: 汇总信息")
    print("=" * 60)

    # 查询所有已通过的报名
    all_approved = Registration.query.filter_by(
        competition_id=basketball_comp.id,
        status='approved'
    ).all()

    print(f"\n📊 篮球联赛报名情况:")
    print(f"  - 已通过报名: {len(all_approved)} 支队伍")
    print()
    print(f"👥 全部参赛队伍:")
    for i, reg in enumerate(all_approved, 1):
        team_name = reg.team_name or '未命名'
        captain_name = reg.user.real_name if reg.user else '未知'
        members = reg.members_list
        member_names = [m.get('name', '?') for m in members]
        print(f"  {i}. {team_name} (队长: {captain_name}) - {', '.join(member_names)}")

    print(f"\n📝 分组建议:")
    print(f"  8支队伍 → 分2组（A组4队 + B组4队）")
    print(f"  每组循环赛: 每组 C(4,2) = 6 场")
    print(f"  总计循环赛: 2 × 6 = 12 场")
    print(f"  淘汰赛: 4支晋级 → 半决赛2场 + 决赛1场 = 3场")

    print(f"\n🌐 操作入口:")
    print(f"  - 赛事详情: http://localhost:5000/competition/{basketball_comp.id}")
    print(f"  - 报名管理: http://localhost:5000/competition/{basketball_comp.id}/registrations")
    print(f"  - 抽签分组: http://localhost:5000/schedule/{basketball_comp.id}/draw")
    print()
