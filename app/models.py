import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ─────────────────── 用户 ───────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(64), unique=True, nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    real_name   = db.Column(db.String(64))
    student_id  = db.Column(db.String(32))          # 学号/工号
    class_name  = db.Column(db.String(64))           # 班级/部门
    phone       = db.Column(db.String(20))
    # 角色: admin / teacher / student
    role        = db.Column(db.String(20), default='student')
    avatar      = db.Column(db.String(200), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    is_active_user = db.Column(db.Boolean, default=True)

    registrations = db.relationship('Registration', backref='user', lazy='dynamic')

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_teacher(self):
        return self.role in ('admin', 'teacher')

    def __repr__(self):
        return f'<User {self.username}>'


# ─────────────────── 赛事 ───────────────────
class Competition(db.Model):
    __tablename__ = 'competitions'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(128), nullable=False)
    sport_type   = db.Column(db.String(64))          # 篮球/足球/田径/…
    # team / individual / mixed
    comp_type    = db.Column(db.String(20), default='individual')
    # 赛制: round_robin(积分赛) / knockout(淘汰赛) / hybrid(混合赛)
    format       = db.Column(db.String(20), default='round_robin')
    description  = db.Column(db.Text)
    rules        = db.Column(db.Text)
    venue        = db.Column(db.String(128))
    max_teams    = db.Column(db.Integer, default=16)
    team_size    = db.Column(db.Integer, default=1)  # 团体赛每队人数
    # 积分规则
    win_points   = db.Column(db.Integer, default=3)
    draw_points  = db.Column(db.Integer, default=1)
    loss_points  = db.Column(db.Integer, default=0)
    # 混合赛中积分赛转淘汰赛时取前几名
    top_advance  = db.Column(db.Integer, default=8)
    # 状态: draft / open / ongoing / finished / cancelled
    status       = db.Column(db.String(20), default='draft')
    reg_start    = db.Column(db.DateTime)
    reg_end      = db.Column(db.DateTime)
    start_date   = db.Column(db.DateTime)
    end_date     = db.Column(db.DateTime)
    created_by   = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    creator       = db.relationship('User', foreign_keys=[created_by])
    registrations = db.relationship('Registration', backref='competition', lazy='dynamic',
                                    cascade='all, delete-orphan')
    groups        = db.relationship('Group', backref='competition', lazy='dynamic',
                                    cascade='all, delete-orphan')
    matches       = db.relationship('Match', backref='competition', lazy='dynamic',
                                    cascade='all, delete-orphan')

    @property
    def status_label(self):
        labels = {'draft':'草稿','open':'报名中','ongoing':'进行中',
                  'finished':'已结束','cancelled':'已取消'}
        return labels.get(self.status, self.status)

    @property
    def format_label(self):
        labels = {'round_robin':'积分循环赛','knockout':'单淘汰赛','hybrid':'混合赛(积分+淘汰)'}
        return labels.get(self.format, self.format)

    def __repr__(self):
        return f'<Competition {self.name}>'


# ─────────────────── 报名 / 参赛队伍 ───────────────────
class Registration(db.Model):
    """个人赛直接报名；团体赛 captain 代表整队报名，members 存队员详情JSON"""
    __tablename__ = 'registrations'
    id            = db.Column(db.Integer, primary_key=True)
    competition_id= db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_name     = db.Column(db.String(64))         # 团体赛队名
    # JSON: [{"student_id":"xxx", "class_name":"xxx", "name":"xxx", "photo":"xxx"}, ...]
    team_members  = db.Column(db.Text)
    # 状态: pending / approved / rejected
    status        = db.Column(db.String(20), default='pending')
    note          = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def members_list(self):
        """解析 team_members JSON 为列表"""
        if not self.team_members:
            return []
        try:
            return json.loads(self.team_members)
        except (ValueError, TypeError):
            return []

    def __repr__(self):
        return f'<Registration {self.id} comp={self.competition_id}>'


# ─────────────────── 分组 ───────────────────
class Group(db.Model):
    __tablename__ = 'groups'
    id            = db.Column(db.Integer, primary_key=True)
    competition_id= db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    name          = db.Column(db.String(32))          # A组/B组…
    stage         = db.Column(db.String(20), default='group')  # group / knockout
    members       = db.relationship('GroupMember', backref='group', lazy='dynamic',
                                    cascade='all, delete-orphan')
    matches       = db.relationship('Match', backref='group', lazy='dynamic')

    def __repr__(self):
        return f'<Group {self.name}>'


class GroupMember(db.Model):
    __tablename__ = 'group_members'
    id              = db.Column(db.Integer, primary_key=True)
    group_id        = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    registration_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), nullable=False)
    # 积分榜
    played  = db.Column(db.Integer, default=0)
    wins    = db.Column(db.Integer, default=0)
    draws   = db.Column(db.Integer, default=0)
    losses  = db.Column(db.Integer, default=0)
    points  = db.Column(db.Integer, default=0)
    score_for     = db.Column(db.Integer, default=0)
    score_against = db.Column(db.Integer, default=0)
    rank    = db.Column(db.Integer, default=0)

    registration = db.relationship('Registration')

    @property
    def score_diff(self):
        return self.score_for - self.score_against

    def __repr__(self):
        return f'<GroupMember reg={self.registration_id}>'


# ─────────────────── 比赛场次 ───────────────────
class Match(db.Model):
    __tablename__ = 'matches'
    id            = db.Column(db.Integer, primary_key=True)
    competition_id= db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    group_id      = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    round_num     = db.Column(db.Integer, default=1)   # 轮次
    match_order   = db.Column(db.Integer, default=1)   # 场次序号
    stage         = db.Column(db.String(20), default='group')  # group/r16/qf/sf/final
    home_reg_id   = db.Column(db.Integer, db.ForeignKey('registrations.id'))
    away_reg_id   = db.Column(db.Integer, db.ForeignKey('registrations.id'))
    home_score    = db.Column(db.Integer)
    away_score    = db.Column(db.Integer)
    home_detail   = db.Column(db.Text)    # 附加信息（分局/时间等）
    away_detail   = db.Column(db.Text)
    venue         = db.Column(db.String(128))
    scheduled_at  = db.Column(db.DateTime)
    played_at     = db.Column(db.DateTime)
    # 状态: pending / ongoing / finished / bye
    status        = db.Column(db.String(20), default='pending')
    winner_reg_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), nullable=True)
    note          = db.Column(db.Text)
    # 淘汰赛晋级关联
    next_match_id = db.Column(db.Integer, db.ForeignKey('matches.id'), nullable=True)
    next_slot     = db.Column(db.String(4))   # 'home' or 'away'

    home_reg  = db.relationship('Registration', foreign_keys=[home_reg_id])
    away_reg  = db.relationship('Registration', foreign_keys=[away_reg_id])
    winner    = db.relationship('Registration', foreign_keys=[winner_reg_id])

    @property
    def stage_label(self):
        labels = {'group':'小组赛','r16':'淘汰赛16强','r8':'淘汰赛8强',
                  'qf':'四分之一决赛','sf':'半决赛','final':'决赛',
                  'third':'三四名决赛'}
        return labels.get(self.stage, self.stage)

    def __repr__(self):
        return f'<Match {self.id} {self.stage} R{self.round_num}-{self.match_order}>'


# ─────────────────── 公告 ───────────────────
class Announcement(db.Model):
    __tablename__ = 'announcements'
    id           = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=True)
    title        = db.Column(db.String(128), nullable=False)
    content      = db.Column(db.Text)
    author_id    = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    is_pinned    = db.Column(db.Boolean, default=False)

    author = db.relationship('User')
    competition = db.relationship('Competition')
