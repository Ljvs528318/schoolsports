import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from app.models import db, User, Competition, Registration, Match, Group, GroupMember, Announcement

api_bp = Blueprint('api', __name__)


# ──────────────────── 辅助函数 ────────────────────

def success_response(data=None, message='success', code=200):
    """成功响应"""
    resp = {'code': 0, 'message': message}
    if data is not None:
        resp['data'] = data
    return jsonify(resp), code


def error_response(message='error', code=400, http_status=400):
    """错误响应"""
    return jsonify({'code': code, 'message': message}), http_status


def get_current_user():
    """获取当前登录用户"""
    user_id = get_jwt_identity()
    if user_id:
        return User.query.get(int(user_id))
    return None


# ──────────────────── 认证接口 ────────────────────

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data:
        return error_response('Missing credentials', 1001)

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error_response('Username and password required', 1002)

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return error_response('Invalid credentials', 1003)

    if not user.is_active_user:
        return error_response('Account disabled', 1004)

    access_token = create_access_token(identity=str(user.id))

    return success_response({
        'token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'role': user.role,
            'avatar': user.avatar or ''
        }
    }, 'Login success')


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return error_response('Missing registration data', 1001)

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return error_response('Username and password required', 1002)

    if len(password) < 6:
        return error_response('Password too short', 1005)

    if User.query.filter_by(username=username).first():
        return error_response('Username exists', 1006)

    email = data.get('email', '').strip()
    if email and User.query.filter_by(email=email).first():
        return error_response('Email exists', 1007)

    user = User(
        username=username,
        email=email or f'{username}@school.edu',
        real_name=data.get('real_name', '').strip(),
        student_id=data.get('student_id', '').strip(),
        class_name=data.get('class_name', '').strip(),
        phone=data.get('phone', '').strip(),
        role='student'
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(identity=str(user.id))

        return success_response({
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'role': user.role,
                'avatar': user.avatar or ''
            }
        }, 'Registration success', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'Registration failed: {str(e)}', 1008, 500)


@api_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户资料"""
    user = get_current_user()
    if not user:
        return error_response('User not found', 1009, 404)

    return success_response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'real_name': user.real_name,
        'student_id': user.student_id,
        'class_name': user.class_name,
        'phone': user.phone,
        'role': user.role,
        'avatar': user.avatar or '',
        'created_at': user.created_at.isoformat() if user.created_at else ''
    })


@api_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新当前用户资料"""
    user = get_current_user()
    if not user:
        return error_response('User not found', 1009, 404)

    data = request.get_json()
    if not data:
        return error_response('No data provided', 1010)

    try:
        # 更新允许修改的字段
        if 'real_name' in data:
            user.real_name = data['real_name'].strip()
        if 'email' in data:
            new_email = data['email'].strip()
            # 检查邮箱是否被其他用户使用
            if new_email and new_email != user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing and existing.id != user.id:
                    return error_response('Email already exists', 1011)
            user.email = new_email or f'{user.username}@school.edu'
        if 'phone' in data:
            user.phone = data['phone'].strip()
        if 'student_id' in data:
            user.student_id = data['student_id'].strip()
        if 'class_name' in data:
            user.class_name = data['class_name'].strip()

        db.session.commit()

        return success_response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'real_name': user.real_name,
            'student_id': user.student_id,
            'class_name': user.class_name,
            'phone': user.phone,
            'role': user.role,
            'avatar': user.avatar or ''
        }, 'Profile updated successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 1012, 500)


@api_bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    user = get_current_user()
    if not user:
        return error_response('User not found', 1009, 404)

    data = request.get_json()
    if not data:
        return error_response('No data provided', 1010)

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return error_response('Old password and new password required', 1013)

    if len(new_password) < 6:
        return error_response('New password too short', 1014)

    if not user.check_password(old_password):
        return error_response('Old password incorrect', 1015)

    try:
        user.set_password(new_password)
        db.session.commit()
        return success_response(message='Password changed successfully')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Change password failed: {str(e)}', 1016, 500)


# ──────────────────── 赛事接口 ────────────────────

@api_bp.route('/competitions', methods=['GET'])
def get_competitions():
    """获取赛事列表"""
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Competition.query
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Competition.created_at.desc())

    total = query.count()
    competitions = query.offset((page - 1) * per_page).limit(per_page).all()

    result = []
    for comp in competitions:
        result.append({
            'id': comp.id,
            'name': comp.name,
            'sport_type': comp.sport_type,
            'comp_type': comp.comp_type,
            'comp_type_label': 'Team' if comp.comp_type == 'team' else 'Individual',
            'format': comp.format,
            'format_label': comp.format_label,
            'status': comp.status,
            'status_label': comp.status_label,
            'venue': comp.venue,
            'team_size': comp.team_size,
            'max_teams': comp.max_teams,
            'start_date': comp.start_date.isoformat() if comp.start_date else '',
            'end_date': comp.end_date.isoformat() if comp.end_date else '',
        })

    return success_response({
        'competitions': result,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })


@api_bp.route('/competitions/<int:cid>', methods=['GET'])
def get_competition_detail(cid):
    """获取赛事详情"""
    comp = Competition.query.get_or_404(cid)

    reg_count = Registration.query.filter_by(competition_id=cid, status='approved').count()

    user_registration = None
    try:
        user = get_current_user()
        if user:
            reg = Registration.query.filter_by(competition_id=cid, user_id=user.id).first()
            if reg:
                user_registration = {
                    'id': reg.id,
                    'status': reg.status,
                    'team_name': reg.team_name,
                }
    except:
        pass

    return success_response({
        'id': comp.id,
        'name': comp.name,
        'sport_type': comp.sport_type,
        'comp_type': comp.comp_type,
        'comp_type_label': 'Team' if comp.comp_type == 'team' else 'Individual',
        'format': comp.format,
        'format_label': comp.format_label,
        'status': comp.status,
        'status_label': comp.status_label,
        'description': comp.description or '',
        'rules': comp.rules or '',
        'venue': comp.venue,
        'team_size': comp.team_size,
        'max_teams': comp.max_teams,
        'reg_count': reg_count,
        'win_points': comp.win_points,
        'draw_points': comp.draw_points,
        'loss_points': comp.loss_points,
        'start_date': comp.start_date.isoformat() if comp.start_date else '',
        'end_date': comp.end_date.isoformat() if comp.end_date else '',
        'reg_start': comp.reg_start.isoformat() if comp.reg_start else '',
        'reg_end': comp.reg_end.isoformat() if comp.reg_end else '',
        'user_registration': user_registration
    })


@api_bp.route('/competitions/<int:cid>/register', methods=['POST'])
@jwt_required()
def register_competition(cid):
    """报名参赛"""
    user = get_current_user()
    comp = Competition.query.get_or_404(cid)

    if comp.status != 'open':
        return error_response('Registration not open', 2001)

    existing = Registration.query.filter_by(competition_id=cid, user_id=user.id).first()
    if existing:
        return error_response('Already registered', 2002)

    data = request.get_json() or {}

    reg = Registration(
        competition_id=cid,
        user_id=user.id,
        team_name=data.get('team_name', ''),
        status='pending'
    )

    if comp.comp_type == 'team' and 'team_members' in data:
        reg.team_members = json.dumps(data['team_members'], ensure_ascii=False)

    try:
        db.session.add(reg)
        db.session.commit()
        return success_response({'id': reg.id, 'status': reg.status}, 'Registration submitted')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Registration failed: {str(e)}', 2003, 500)


# ──────────────────── 赛程接口 ────────────────────

@api_bp.route('/competitions/<int:cid>/schedule', methods=['GET'])
def get_schedule(cid):
    """获取赛程"""
    comp = Competition.query.get_or_404(cid)

    # 赛阶段排序顺序：小组赛 → 16强 → 8强 → 四分之一决赛 → 半决赛 → 三四名决赛 → 决赛
    STAGE_ORDER = {
        'group': 1,
        'r16': 2,
        'r8': 3,
        'qf': 4,
        'sf': 5,
        'third': 6,
        'final': 7
    }

    # 阶段中文标签
    STAGE_LABELS = {
        'group': '小组赛',
        'r16': '16强',
        'r8': '8强',
        'qf': '四分之一决赛',
        'sf': '半决赛',
        'third': '三四名决赛',
        'final': '决赛'
    }

    matches = Match.query.filter_by(competition_id=cid).order_by(
        Match.round_num, Match.match_order
    ).all()

    stages = {}
    for match in matches:
        stage = match.stage or 'group'
        if stage not in stages:
            stages[stage] = {
                'stage': stage,
                'stage_label': STAGE_LABELS.get(stage, stage),
                'stage_order': STAGE_ORDER.get(stage, 99),
                'matches': []
            }

        home_reg = Registration.query.get(match.home_reg_id) if match.home_reg_id else None
        away_reg = Registration.query.get(match.away_reg_id) if match.away_reg_id else None

        stages[stage]['matches'].append({
            'id': match.id,
            'round_num': match.round_num,
            'match_order': match.match_order,
            'home_team': home_reg.team_name if home_reg else 'TBD',
            'away_team': away_reg.team_name if away_reg else 'TBD',
            'home_score': match.home_score,
            'away_score': match.away_score,
            'venue': match.venue,
            'scheduled_at': match.scheduled_at.isoformat() if match.scheduled_at else '',
            'status': match.status,
        })

    # 按比赛进展顺序排序：小组赛 → 淘汰赛各轮 → 决赛
    sorted_stages = sorted(stages.values(), key=lambda s: s['stage_order'])

    return success_response({
        'competition_id': cid,
        'stages': sorted_stages
    })


@api_bp.route('/competitions/<int:cid>/standings', methods=['GET'])
def get_standings(cid):
    """获取积分榜"""
    comp = Competition.query.get_or_404(cid)

    # 如果是淘汰赛制，不显示积分榜
    if comp.format == 'knockout':
        return success_response({
            'competition_id': cid,
            'format': 'knockout',
            'message': '淘汰赛制无积分榜'
        })

    groups = Group.query.filter_by(competition_id=cid, stage='group').all()

    result = []
    for group in groups:
        members = GroupMember.query.filter_by(group_id=group.id).order_by(
            GroupMember.points.desc(),
            (GroupMember.score_for - GroupMember.score_against).desc()
        ).all()

        standings = []
        for gm in members:
            reg = Registration.query.get(gm.registration_id)
            standings.append({
                'registration_id': gm.registration_id,
                'team_name': reg.team_name if reg else 'Unknown',
                'played': gm.played,
                'wins': gm.wins,
                'draws': gm.draws,
                'losses': gm.losses,
                'points': gm.points,
                'score_for': gm.score_for,
                'score_against': gm.score_against,
            })

        result.append({
            'group_id': group.id,
            'group_name': group.name,
            'standings': standings
        })

    return success_response({'competition_id': cid, 'groups': result})


# ──────────────────── 用户相关接口 ────────────────────

@api_bp.route('/user/registrations', methods=['GET'])
@jwt_required()
def get_my_registrations():
    """获取我的报名"""
    user = get_current_user()

    registrations = Registration.query.filter_by(user_id=user.id).all()

    result = []
    for reg in registrations:
        comp = Competition.query.get(reg.competition_id)
        result.append({
            'id': reg.id,
            'competition_id': reg.competition_id,
            'competition_name': comp.name if comp else '',
            'team_name': reg.team_name,
            'status': reg.status,
            'created_at': reg.created_at.isoformat() if reg.created_at else ''
        })

    return success_response({'registrations': result})


# ──────────────────── 管理接口（管理员）────────────────────

@api_bp.route('/competitions/<int:cid>/registrations', methods=['GET'])
@jwt_required()
def get_competition_registrations(cid):
    """获取赛事的报名列表（管理员）"""
    user = get_current_user()
    if not user or user.role != 'admin':
        return error_response('Unauthorized', 4001, 403)

    comp = Competition.query.get_or_404(cid)

    status = request.args.get('status', '')
    query = Registration.query.filter_by(competition_id=cid)
    if status:
        query = query.filter_by(status=status)

    registrations = query.order_by(Registration.created_at.desc()).all()

    result = []
    for reg in registrations:
        user = User.query.get(reg.user_id)
        members = []
        if reg.team_members:
            try:
                members = json.loads(reg.team_members)
            except:
                members = []

        result.append({
            'id': reg.id,
            'user_id': reg.user_id,
            'user_name': user.real_name if user else '',
            'student_id': user.student_id if user else '',
            'team_name': reg.team_name,
            'status': reg.status,
            'members_list': members,
            'created_at': reg.created_at.isoformat() if reg.created_at else ''
        })

    return success_response({
        'competition_id': cid,
        'competition_name': comp.name,
        'registrations': result
    })


@api_bp.route('/registrations/<int:rid>/status', methods=['PUT'])
@jwt_required()
def update_registration_status(rid):
    """审核报名（批准/拒绝）"""
    user = get_current_user()
    if not user or user.role != 'admin':
        return error_response('Unauthorized', 4001, 403)

    reg = Registration.query.get_or_404(rid)

    data = request.get_json()
    if not data or 'status' not in data:
        return error_response('Status required', 4002)

    new_status = data['status']
    if new_status not in ('approved', 'rejected'):
        return error_response('Invalid status', 4003)

    try:
        reg.status = new_status
        db.session.commit()
        return success_response(message=f'Registration {new_status}')
    except Exception as e:
        db.session.rollback()
        return error_response(f'Update failed: {str(e)}', 4004, 500)


# ──────────────────── 公告接口 ────────────────────

@api_bp.route('/announcements', methods=['GET'])
def get_announcements():
    """获取公告列表"""
    announcements = Announcement.query.order_by(
        Announcement.is_pinned.desc(),
        Announcement.created_at.desc()
    ).limit(20).all()

    result = []
    for ann in announcements:
        result.append({
            'id': ann.id,
            'title': ann.title,
            'content': ann.content,
            'is_pinned': ann.is_pinned,
            'created_at': ann.created_at.isoformat() if ann.created_at else ''
        })

    return success_response({'announcements': result})
