from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, User, Competition, Registration, Announcement
from functools import wraps

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @login_required
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    @login_required
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_teacher:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@teacher_required
def dashboard():
    stats = {
        'users': User.query.count(),
        'comps': Competition.query.count(),
        'open_comps': Competition.query.filter_by(status='open').count(),
        'ongoing_comps': Competition.query.filter_by(status='ongoing').count(),
        'registrations': Registration.query.count(),
        'pending_reg': Registration.query.filter_by(status='pending').count(),
    }
    recent_comps = Competition.query.order_by(Competition.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_comps=recent_comps, recent_users=recent_users)


# ─── 用户管理 ───
@admin_bp.route('/users')
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    query = User.query
    if q:
        query = query.filter(
            (User.username.contains(q)) |
            (User.real_name.contains(q)) |
            (User.student_id.contains(q))
        )
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users, q=q)


@admin_bp.route('/users/<int:uid>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(uid):
    user = User.query.get_or_404(uid)
    if request.method == 'POST':
        user.real_name  = request.form.get('real_name', '').strip()
        user.email      = request.form.get('email', '').strip()
        user.student_id = request.form.get('student_id', '').strip()
        user.class_name = request.form.get('class_name', '').strip()
        user.phone      = request.form.get('phone', '').strip()
        user.role       = request.form.get('role', 'student')
        user.is_active_user = request.form.get('is_active') == 'on'
        new_pwd = request.form.get('new_password', '')
        if new_pwd:
            user.set_password(new_pwd)
        db.session.commit()
        flash('用户信息已更新', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/user_edit.html', user=user)


@admin_bp.route('/users/<int:uid>/delete', methods=['POST'])
@admin_required
def user_delete(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        flash('不能删除自己', 'danger')
        return redirect(url_for('admin.user_list'))
    db.session.delete(user)
    db.session.commit()
    flash('用户已删除', 'success')
    return redirect(url_for('admin.user_list'))


# ─── 公告管理 ───
@admin_bp.route('/announcements')
@teacher_required
def announcements():
    items = Announcement.query.order_by(
        Announcement.is_pinned.desc(),
        Announcement.created_at.desc()
    ).all()
    return render_template('admin/announcements.html', items=items)


@admin_bp.route('/announcements/create', methods=['GET', 'POST'])
@teacher_required
def announcement_create():
    competitions = Competition.query.order_by(Competition.name).all()
    if request.method == 'POST':
        ann = Announcement(
            title=request.form.get('title', '').strip(),
            content=request.form.get('content', '').strip(),
            competition_id=request.form.get('competition_id') or None,
            author_id=current_user.id,
            is_pinned=request.form.get('is_pinned') == 'on'
        )
        db.session.add(ann)
        db.session.commit()
        flash('公告已发布', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/announcement_form.html', ann=None,
                           competitions=competitions)


@admin_bp.route('/announcements/<int:aid>/edit', methods=['GET', 'POST'])
@teacher_required
def announcement_edit(aid):
    ann = Announcement.query.get_or_404(aid)
    competitions = Competition.query.order_by(Competition.name).all()
    if request.method == 'POST':
        ann.title    = request.form.get('title', '').strip()
        ann.content  = request.form.get('content', '').strip()
        ann.competition_id = request.form.get('competition_id') or None
        ann.is_pinned = request.form.get('is_pinned') == 'on'
        db.session.commit()
        flash('公告已更新', 'success')
        return redirect(url_for('admin.announcements'))
    return render_template('admin/announcement_form.html', ann=ann,
                           competitions=competitions)


@admin_bp.route('/announcements/<int:aid>/delete', methods=['POST'])
@teacher_required
def announcement_delete(aid):
    ann = Announcement.query.get_or_404(aid)
    db.session.delete(ann)
    db.session.commit()
    flash('公告已删除', 'success')
    return redirect(url_for('admin.announcements'))
