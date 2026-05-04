from flask import Flask
from flask_login import LoginManager, current_user
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from app.models import db, User
from datetime import datetime

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'

jwt = JWTManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Jinja2 全局变量
    @app.context_processor
    def inject_globals():
        return {
            'current_user': current_user,
            'now': datetime.utcnow()
        }

    # 注册蓝图
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.competition import comp_bp
    from app.blueprints.schedule import schedule_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(comp_bp, url_prefix='/competition')
    app.register_blueprint(schedule_bp, url_prefix='/schedule')
    app.register_blueprint(api_bp, url_prefix='/api')

    # 开发测试路由（仅 TESTING 模式）
    if app.config.get('TESTING'):
        from test_runner import test_bp
        app.register_blueprint(test_bp)

    with app.app_context():
        db.create_all()
        _init_admin(app)

    return app


def _init_admin(app):
    """首次运行自动创建超级管理员"""
    from app.models import User
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            email='admin@school.edu',
            real_name='系统管理员',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('[初始化] 已创建管理员账号: admin / admin123')
