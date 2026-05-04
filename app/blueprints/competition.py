import json
import os
import random
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import (db, Competition, Registration, Group, GroupMember,
                        Match, Announcement, User)

comp_bp = Blueprint('competition', __name__)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_photo(file_obj, prefix='member'):
    """保存上传的相片，返回相对路径"""
    if not file_obj or file_obj.filename == '':
        return ''
    if not allowed_file(file_obj.filename):
        flash('相片格式不支持，仅支持 png/jpg/jpeg/gif/webp', 'warning')
        return ''
    filename = secure_filename(file_obj.filename)
    # 用时间戳+前缀避免重名
    ts = datetime.now().strftime('%Y%m%d%H%M%S%f')
    ext = filename.rsplit('.', 1)[1].lower()
    save_name = f'{prefix}_{ts}.{ext}'
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'photos')
    os.makedirs(upload_dir, exist_ok=True)
    file_obj.save(os.path.join(upload_dir, save_name))
    return f'uploads/photos/{save_name}'


def teacher_required_comp(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher:
            abort(403)
        return f(*args, **kwargs)
    return login_required(decorated)


# ─── 赛事列表 ───
@comp_bp.route('/')
def list_comps():
    status = request.args.get('status', '')
    sport  = request.args.get('sport', '')
    q      = request.args.get('q', '')
    query  = Competition.query
    if status:
        query = query.filter_by(status=status)
    if sport:
        query = query.filter_by(sport_type=sport)
    if q:
        query = query.filter(Competition.name.contains(q))
    comps = query.order_by(Competition.created_at.desc()).all()
    sport_types = db.session.query(Competition.sport_type).distinct().all()
    sport_types = [s[0] for s in sport_types if s[0]]
    return render_template('competition/list.html', comps=comps,
                           sport_types=sport_types, status=status,
                           sport=sport, q=q)


# ─── 赛事详情 ───
@comp_bp.route('/<int:cid>')
def detail(cid):
    comp = Competition.query.get_or_404(cid)
    user_reg = None
    if current_user.is_authenticated:
        user_reg = Registration.query.filter_by(
            competition_id=cid, user_id=current_user.id
        ).first()
    registrations = Registration.query.filter_by(
        competition_id=cid, status='approved'
    ).all()
    groups = Group.query.filter_by(competition_id=cid).all()
    announcements = Announcement.query.filter_by(competition_id=cid)\
        .order_by(Announcement.created_at.desc()).all()
    matches = Match.query.filter_by(competition_id=cid)\
        .order_by(Match.round_num, Match.match_order).all()
    return render_template('competition/detail.html',
                           comp=comp, user_reg=user_reg,
                           registrations=registrations,
                           groups=groups, announcements=announcements,
                           matches=matches)


# ─── 创建赛事 ───
@comp_bp.route('/create', methods=['GET', 'POST'])
@teacher_required_comp
def create():
    if request.method == 'POST':
        comp = Competition(
            name       = request.form['name'].strip(),
            sport_type = request.form.get('sport_type', '').strip(),
            comp_type  = request.form.get('comp_type', 'individual'),
            format     = request.form.get('format', 'round_robin'),
            description= request.form.get('description', '').strip(),
            rules      = request.form.get('rules', '').strip(),
            venue      = request.form.get('venue', '').strip(),
            max_teams  = int(request.form.get('max_teams', 16) or 16),
            team_size  = int(request.form.get('team_size', 1) or 1),
            win_points = int(request.form.get('win_points', 3) or 3),
            draw_points= int(request.form.get('draw_points', 1) or 1),
            loss_points= int(request.form.get('loss_points', 0) or 0),
            top_advance= int(request.form.get('top_advance', 8) or 8),
            reg_start  = _parse_dt(request.form.get('reg_start')),
            reg_end    = _parse_dt(request.form.get('reg_end')),
            start_date = _parse_dt(request.form.get('start_date')),
            end_date   = _parse_dt(request.form.get('end_date')),
            status     = request.form.get('status', 'draft'),
            created_by = current_user.id
        )
        db.session.add(comp)
        db.session.commit()
        flash(f'赛事「{comp.name}」已创建', 'success')
        return redirect(url_for('competition.detail', cid=comp.id))
    return render_template('competition/form.html', comp=None)


# ─── 编辑赛事 ───
@comp_bp.route('/<int:cid>/edit', methods=['GET', 'POST'])
@teacher_required_comp
def edit(cid):
    comp = Competition.query.get_or_404(cid)
    if request.method == 'POST':
        comp.name       = request.form['name'].strip()
        comp.sport_type = request.form.get('sport_type', '').strip()
        comp.comp_type  = request.form.get('comp_type', 'individual')
        comp.format     = request.form.get('format', 'round_robin')
        comp.description= request.form.get('description', '').strip()
        comp.rules      = request.form.get('rules', '').strip()
        comp.venue      = request.form.get('venue', '').strip()
        comp.max_teams  = int(request.form.get('max_teams', 16) or 16)
        comp.team_size  = int(request.form.get('team_size', 1) or 1)
        comp.win_points = int(request.form.get('win_points', 3) or 3)
        comp.draw_points= int(request.form.get('draw_points', 1) or 1)
        comp.loss_points= int(request.form.get('loss_points', 0) or 0)
        comp.top_advance= int(request.form.get('top_advance', 8) or 8)
        comp.reg_start  = _parse_dt(request.form.get('reg_start'))
        comp.reg_end    = _parse_dt(request.form.get('reg_end'))
        comp.start_date = _parse_dt(request.form.get('start_date'))
        comp.end_date   = _parse_dt(request.form.get('end_date'))
        comp.status     = request.form.get('status', comp.status)
        db.session.commit()
        flash('赛事信息已更新', 'success')
        return redirect(url_for('competition.detail', cid=cid))
    return render_template('competition/form.html', comp=comp)


# ─── 删除赛事 ───
@comp_bp.route('/<int:cid>/delete', methods=['POST'])
@teacher_required_comp
def delete(cid):
    comp = Competition.query.get_or_404(cid)
    db.session.delete(comp)
    db.session.commit()
    flash('赛事已删除', 'success')
    return redirect(url_for('competition.list_comps'))


# ─── 报名 ───
@comp_bp.route('/<int:cid>/register', methods=['GET', 'POST'])
@login_required
def register(cid):
    comp = Competition.query.get_or_404(cid)
    if comp.status != 'open':
        flash('当前不在报名阶段', 'warning')
        return redirect(url_for('competition.detail', cid=cid))
    existing = Registration.query.filter_by(
        competition_id=cid, user_id=current_user.id
    ).first()
    if existing:
        flash('您已报名此赛事', 'info')
        return redirect(url_for('competition.detail', cid=cid))

    if request.method == 'POST':
        team_name = request.form.get('team_name', '').strip()
        note      = request.form.get('note', '').strip()

        # 解析队员信息
        member_count = int(request.form.get('member_count', 0) or 0)
        members = []

        # 队长（报名人自身）默认为第一个队员
        captain_photo = ''
        captain_photo_file = request.files.get('captain_photo')
        if captain_photo_file and captain_photo_file.filename:
            captain_photo = save_photo(captain_photo_file, prefix='captain')
        elif current_user.avatar:
            captain_photo = current_user.avatar

        members.append({
            'student_id': current_user.student_id or request.form.get('captain_student_id', ''),
            'class_name': current_user.class_name or request.form.get('captain_class_name', ''),
            'name': current_user.real_name or current_user.username,
            'photo': captain_photo,
            'is_captain': True
        })

        # 额外队员
        for i in range(1, member_count + 1):
            m_student_id = request.form.get(f'member_{i}_student_id', '').strip()
            m_class_name = request.form.get(f'member_{i}_class_name', '').strip()
            m_name       = request.form.get(f'member_{i}_name', '').strip()
            m_photo_file = request.files.get(f'member_{i}_photo')
            m_photo = ''
            if m_photo_file and m_photo_file.filename:
                m_photo = save_photo(m_photo_file, prefix=f'member_{i}')

            if m_name:  # 至少有姓名才算有效
                members.append({
                    'student_id': m_student_id,
                    'class_name': m_class_name,
                    'name': m_name,
                    'photo': m_photo,
                    'is_captain': False
                })

        members_json = json.dumps(members, ensure_ascii=False)

        reg = Registration(
            competition_id=cid,
            user_id=current_user.id,
            team_name=team_name or (current_user.real_name or current_user.username),
            team_members=members_json,
            note=note,
            status='pending'
        )
        db.session.add(reg)
        db.session.commit()
        flash('报名成功，等待审核', 'success')
        return redirect(url_for('competition.detail', cid=cid))

    return render_template('competition/register.html', comp=comp)


# ─── 报名管理（教师）───
@comp_bp.route('/<int:cid>/registrations')
@teacher_required_comp
def manage_registrations(cid):
    comp = Competition.query.get_or_404(cid)
    regs = Registration.query.filter_by(competition_id=cid)\
        .order_by(Registration.created_at).all()
    return render_template('competition/registrations.html', comp=comp, regs=regs)


@comp_bp.route('/<int:cid>/registrations/<int:rid>/approve', methods=['POST'])
@teacher_required_comp
def approve_reg(cid, rid):
    reg = Registration.query.get_or_404(rid)
    reg.status = 'approved'
    db.session.commit()
    flash('已审批通过', 'success')
    return redirect(url_for('competition.manage_registrations', cid=cid))


@comp_bp.route('/<int:cid>/registrations/<int:rid>/reject', methods=['POST'])
@teacher_required_comp
def reject_reg(cid, rid):
    reg = Registration.query.get_or_404(rid)
    reg.status = 'rejected'
    db.session.commit()
    flash('已拒绝报名', 'warning')
    return redirect(url_for('competition.manage_registrations', cid=cid))


@comp_bp.route('/<int:cid>/registrations/<int:rid>/delete', methods=['POST'])
@teacher_required_comp
def delete_reg(cid, rid):
    reg = Registration.query.get_or_404(rid)
    db.session.delete(reg)
    db.session.commit()
    flash('报名记录已删除', 'success')
    return redirect(url_for('competition.manage_registrations', cid=cid))


# ─── 撤销报名（选手）───
@comp_bp.route('/<int:cid>/unregister', methods=['POST'])
@login_required
def unregister(cid):
    reg = Registration.query.filter_by(
        competition_id=cid, user_id=current_user.id
    ).first_or_404()
    if reg.status == 'approved':
        flash('报名已通过，如需退赛请联系管理员', 'warning')
        return redirect(url_for('competition.detail', cid=cid))
    db.session.delete(reg)
    db.session.commit()
    flash('已撤销报名', 'info')
    return redirect(url_for('competition.detail', cid=cid))


# ─── 批量审批 ───
@comp_bp.route('/<int:cid>/registrations/approve_all', methods=['POST'])
@teacher_required_comp
def approve_all(cid):
    regs = Registration.query.filter_by(competition_id=cid, status='pending').all()
    for r in regs:
        r.status = 'approved'
    db.session.commit()
    flash(f'已批量通过 {len(regs)} 条报名', 'success')
    return redirect(url_for('competition.manage_registrations', cid=cid))


def _parse_dt(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None
