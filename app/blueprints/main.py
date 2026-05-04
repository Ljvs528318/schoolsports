from flask import Blueprint, render_template
from flask_login import current_user
from app.models import Competition, Announcement

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    comps = Competition.query.filter(
        Competition.status.in_(['open', 'ongoing'])
    ).order_by(Competition.start_date.desc()).limit(6).all()
    announcements = Announcement.query.filter_by(competition_id=None)\
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())\
        .limit(5).all()
    finished = Competition.query.filter_by(status='finished')\
        .order_by(Competition.end_date.desc()).limit(4).all()
    return render_template('main/index.html',
                           comps=comps,
                           announcements=announcements,
                           finished=finished)


@main_bp.route('/about')
def about():
    return render_template('main/about.html')


@main_bp.route('/miniprogram-guide')
def miniprogram_guide():
    return render_template('miniprogram_guide.html')
