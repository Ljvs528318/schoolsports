from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, User
import os
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_active_user:
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'欢迎回来，{user.real_name or user.username}！', 'success')
            return redirect(next_page or url_for('main.index'))
        flash('用户名或密码错误', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm', '')
        real_name = request.form.get('real_name', '').strip()
        student_id= request.form.get('student_id', '').strip()
        class_name= request.form.get('class_name', '').strip()
        phone     = request.form.get('phone', '').strip()

        if password != confirm:
            flash('两次密码不一致', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('用户名已存在', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'danger')
        else:
            user = User(username=username, email=email, real_name=real_name,
                        student_id=student_id, class_name=class_name, phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.real_name   = request.form.get('real_name', '').strip()
        current_user.student_id  = request.form.get('student_id', '').strip()
        current_user.class_name  = request.form.get('class_name', '').strip()
        current_user.phone       = request.form.get('phone', '').strip()

        # 头像上传
        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename:
            allowed_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            ext = avatar_file.filename.rsplit('.', 1)[1].lower() if '.' in avatar_file.filename else ''
            if ext in allowed_ext:
                ts = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = secure_filename(avatar_file.filename)
                save_name = f'avatar_{ts}.{ext}'
                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
                os.makedirs(upload_dir, exist_ok=True)
                avatar_file.save(os.path.join(upload_dir, save_name))
                current_user.avatar = f'uploads/avatars/{save_name}'
            else:
                flash('头像格式不支持，仅支持 png/jpg/jpeg/gif/webp', 'warning')

        new_pwd = request.form.get('new_password', '')
        if new_pwd:
            if not current_user.check_password(request.form.get('old_password', '')):
                flash('原密码错误', 'danger')
                return redirect(url_for('auth.profile'))
            current_user.set_password(new_pwd)
        db.session.commit()
        flash('资料已更新', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html')
