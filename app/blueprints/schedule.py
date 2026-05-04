"""
赛程管理蓝图：
  - 抽签/随机分组
  - 生成比赛场次（循环赛 / 淘汰赛 / 混合赛）
  - 录入比赛结果、更新积分排名
  - 淘汰赛晋级推进
"""
import json
import math
import random
from datetime import datetime
from itertools import combinations

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort, jsonify)
from flask_login import login_required, current_user
from app.models import (db, Competition, Registration, Group,
                        GroupMember, Match)

schedule_bp = Blueprint('schedule', __name__)


def teacher_req(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_teacher:
            abort(403)
        return f(*args, **kwargs)
    return login_required(wrapped)


# ════════════════════════════════════════
#  抽签 / 分组
# ════════════════════════════════════════
@schedule_bp.route('/<int:cid>/draw', methods=['GET', 'POST'])
@teacher_req
def draw(cid):
    comp = Competition.query.get_or_404(cid)
    approved = Registration.query.filter_by(
        competition_id=cid, status='approved'
    ).all()

    if request.method == 'POST':
        # 清除旧分组和比赛
        for g in comp.groups:
            db.session.delete(g)
        for m in comp.matches:
            db.session.delete(m)
        db.session.commit()

        action = request.form.get('action', 'random')  # random / manual
        num_groups = int(request.form.get('num_groups', 1) or 1)

        regs = list(approved)
        if action == 'random':
            random.shuffle(regs)

        # 按组数分组
        groups_data = _split_groups(regs, num_groups)

        group_names = [chr(65 + i) for i in range(len(groups_data))]  # A B C …
        for i, (gname, grp_regs) in enumerate(zip(group_names, groups_data)):
            g = Group(competition_id=cid, name=f'{gname}组', stage='group')
            db.session.add(g)
            db.session.flush()
            for reg in grp_regs:
                gm = GroupMember(group_id=g.id, registration_id=reg.id)
                db.session.add(gm)

        db.session.commit()
        flash(f'抽签完成，共分 {len(groups_data)} 组', 'success')
        return redirect(url_for('schedule.generate_matches', cid=cid))

    return render_template('schedule/draw.html', comp=comp, approved=approved)


# ════════════════════════════════════════
#  生成比赛场次
# ════════════════════════════════════════
@schedule_bp.route('/<int:cid>/generate', methods=['GET', 'POST'])
@teacher_req
def generate_matches(cid):
    comp = Competition.query.get_or_404(cid)
    groups = Group.query.filter_by(competition_id=cid, stage='group').all()

    if request.method == 'POST':
        # 清除旧场次
        Match.query.filter_by(competition_id=cid).delete()
        db.session.commit()

        fmt = comp.format

        if fmt in ('round_robin', 'hybrid'):
            _gen_round_robin(comp, groups)

        if fmt == 'knockout':
            # 直接生成淘汰赛，用所有已通过报名
            approved = Registration.query.filter_by(
                competition_id=cid, status='approved'
            ).all()
            _gen_knockout(comp, approved, stage_prefix='')

        if fmt == 'hybrid':
            flash('小组循环赛场次已生成；淘汰赛将在小组赛完成后自动生成', 'info')
        else:
            comp.status = 'ongoing'

        db.session.commit()
        flash('比赛场次已生成', 'success')
        return redirect(url_for('schedule.schedule_view', cid=cid))

    return render_template('schedule/generate.html', comp=comp, groups=groups)


# ════════════════════════════════════════
#  赛程总览
# ════════════════════════════════════════
@schedule_bp.route('/<int:cid>')
def schedule_view(cid):
    comp = Competition.query.get_or_404(cid)
    groups = Group.query.filter_by(competition_id=cid).all()
    matches = Match.query.filter_by(competition_id=cid)\
        .order_by(Match.stage, Match.round_num, Match.match_order).all()

    # 按阶段分类
    group_matches = [m for m in matches if m.stage == 'group']
    knockout_matches = [m for m in matches if m.stage != 'group']

    # 积分榜（每组）
    standings = {}
    for g in groups:
        if g.stage == 'group':
            members = GroupMember.query.filter_by(group_id=g.id)\
                .order_by(GroupMember.points.desc(),
                           GroupMember.score_for.desc()).all()
            standings[g.id] = members

    return render_template('schedule/view.html',
                           comp=comp, groups=groups,
                           group_matches=group_matches,
                           knockout_matches=knockout_matches,
                           standings=standings)


# ════════════════════════════════════════
#  录入比赛结果
# ════════════════════════════════════════
@schedule_bp.route('/match/<int:mid>/result', methods=['GET', 'POST'])
@teacher_req
def match_result(mid):
    match = Match.query.get_or_404(mid)
    comp  = match.competition

    if request.method == 'POST':
        home_score = request.form.get('home_score', type=int)
        away_score = request.form.get('away_score', type=int)
        venue      = request.form.get('venue', '').strip()
        note       = request.form.get('note', '').strip()

        if home_score is None or away_score is None:
            flash('请输入双方成绩', 'danger')
            return redirect(url_for('schedule.match_result', mid=mid))

        match.home_score = home_score
        match.away_score = away_score
        match.venue      = venue or match.venue
        match.note       = note
        match.played_at  = datetime.utcnow()
        match.status     = 'finished'

        # 判断胜负
        if home_score > away_score:
            match.winner_reg_id = match.home_reg_id
        elif away_score > home_score:
            match.winner_reg_id = match.away_reg_id
        else:
            match.winner_reg_id = None  # 平局

        # 更新积分榜
        if match.stage == 'group' and match.group_id:
            _update_standings(match, comp)

        # 淘汰赛晋级
        if match.stage != 'group' and match.winner_reg_id:
            _advance_knockout(match)

        db.session.commit()

        # 检查是否需要生成淘汰赛（混合赛）
        if comp.format == 'hybrid':
            _check_and_gen_knockout(comp)

        flash('成绩已录入', 'success')
        return redirect(url_for('schedule.schedule_view', cid=comp.id))

    return render_template('schedule/match_result.html', match=match, comp=comp)


# ════════════════════════════════════════
#  取消/重置比赛结果
# ════════════════════════════════════════
@schedule_bp.route('/match/<int:mid>/reset', methods=['POST'])
@teacher_req
def match_reset(mid):
    match = Match.query.get_or_404(mid)
    if match.stage == 'group' and match.status == 'finished':
        _undo_standings(match, match.competition)
    match.home_score = None
    match.away_score = None
    match.winner_reg_id = None
    match.status = 'pending'
    match.played_at = None
    db.session.commit()
    flash('比赛结果已重置', 'info')
    return redirect(url_for('schedule.schedule_view', cid=match.competition_id))


# ════════════════════════════════════════
#  修改场次信息（时间/场地）
# ════════════════════════════════════════
@schedule_bp.route('/match/<int:mid>/edit', methods=['GET', 'POST'])
@teacher_req
def match_edit(mid):
    match = Match.query.get_or_404(mid)
    if request.method == 'POST':
        dt_str = request.form.get('scheduled_at', '')
        if dt_str:
            for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'):
                try:
                    match.scheduled_at = datetime.strptime(dt_str, fmt)
                    break
                except ValueError:
                    pass
        match.venue = request.form.get('venue', '').strip()
        db.session.commit()
        flash('场次信息已更新', 'success')
        return redirect(url_for('schedule.schedule_view', cid=match.competition_id))
    return render_template('schedule/match_edit.html', match=match)


# ════════════════════════════════════════
#  积分榜 API（JSON）
# ════════════════════════════════════════
@schedule_bp.route('/<int:cid>/standings.json')
def standings_json(cid):
    groups = Group.query.filter_by(competition_id=cid, stage='group').all()
    result = []
    for g in groups:
        members = GroupMember.query.filter_by(group_id=g.id)\
            .order_by(GroupMember.points.desc(),
                       GroupMember.score_for.desc()).all()
        result.append({
            'group': g.name,
            'members': [{
                'name': (m.registration.team_name or
                         (m.registration.user.real_name
                          if m.registration.user else '')),
                'played': m.played, 'wins': m.wins, 'draws': m.draws,
                'losses': m.losses, 'points': m.points,
                'score_for': m.score_for, 'score_against': m.score_against,
                'score_diff': m.score_diff
            } for m in members]
        })
    return jsonify(result)


# ════════════════════════════════════════
#  内部辅助函数
# ════════════════════════════════════════
def _split_groups(regs, num_groups):
    """将报名列表随机分成 num_groups 组"""
    groups = [[] for _ in range(num_groups)]
    for i, reg in enumerate(regs):
        groups[i % num_groups].append(reg)
    return groups


def _gen_round_robin(comp, groups):
    """生成循环赛场次"""
    match_order = 1
    for g in groups:
        members = [gm.registration_id for gm in g.members]
        pairs = list(combinations(members, 2))
        random.shuffle(pairs)
        for rnd, (a, b) in enumerate(pairs, 1):
            m = Match(
                competition_id=comp.id,
                group_id=g.id,
                round_num=rnd,
                match_order=match_order,
                stage='group',
                home_reg_id=a,
                away_reg_id=b,
                status='pending'
            )
            db.session.add(m)
            match_order += 1


def _gen_knockout(comp, regs, stage_prefix=''):
    """生成单淘汰赛（支持 bye 轮空）"""
    n = len(regs)
    if n < 2:
        return
    random.shuffle(regs)

    # 扩充到 2 的幂次
    size = 2 ** math.ceil(math.log2(n))
    byes = size - n

    stage = _knockout_stage_name(size)
    slots = list(regs) + [None] * byes
    random.shuffle(slots)

    matches = []
    order = 1
    for i in range(0, size, 2):
        a = slots[i]
        b = slots[i + 1]
        if a is None and b is None:
            continue
        m = Match(
            competition_id=comp.id,
            round_num=1,
            match_order=order,
            stage=stage,
            home_reg_id=a.id if a else None,
            away_reg_id=b.id if b else None,
            status='bye' if (a is None or b is None) else 'pending',
            winner_reg_id=(a.id if b is None else (b.id if a is None else None))
        )
        db.session.add(m)
        db.session.flush()
        matches.append(m)
        order += 1

    # 递归创建后续轮次的空位场次，并链接 next_match
    _build_knockout_tree(comp, matches, size // 2)


def _build_knockout_tree(comp, prev_round_matches, total_in_round):
    """递归建立淘汰赛后续轮次空场次并链接"""
    if total_in_round <= 1:
        return
    next_stage_size = total_in_round // 2
    if next_stage_size < 1:
        return

    stage = _knockout_stage_name(total_in_round)
    next_stage = _knockout_stage_name(total_in_round)
    next_matches = []
    for i in range(0, len(prev_round_matches), 2):
        if i + 1 >= len(prev_round_matches):
            break
        nm = Match(
            competition_id=comp.id,
            round_num=prev_round_matches[i].round_num + 1,
            match_order=i // 2 + 1,
            stage=next_stage,
            status='pending'
        )
        db.session.add(nm)
        db.session.flush()
        prev_round_matches[i].next_match_id = nm.id
        prev_round_matches[i].next_slot = 'home'
        prev_round_matches[i + 1].next_match_id = nm.id
        prev_round_matches[i + 1].next_slot = 'away'
        next_matches.append(nm)

        # 处理 bye 自动晋级
        for pm in [prev_round_matches[i], prev_round_matches[i + 1]]:
            if pm.status == 'bye' and pm.winner_reg_id:
                _advance_knockout(pm)

    _build_knockout_tree(comp, next_matches, next_stage_size)


def _knockout_stage_name(remaining):
    mapping = {2: 'final', 4: 'sf', 8: 'qf', 16: 'r16', 32: 'r32'}
    return mapping.get(remaining, f'r{remaining}')


def _advance_knockout(match):
    """将获胜者填入下一场"""
    if match.next_match_id and match.winner_reg_id:
        nm = Match.query.get(match.next_match_id)
        if nm:
            if match.next_slot == 'home':
                nm.home_reg_id = match.winner_reg_id
            else:
                nm.away_reg_id = match.winner_reg_id


def _update_standings(match, comp):
    """更新小组赛积分榜"""
    home_gm = GroupMember.query.filter_by(
        group_id=match.group_id, registration_id=match.home_reg_id
    ).first()
    away_gm = GroupMember.query.filter_by(
        group_id=match.group_id, registration_id=match.away_reg_id
    ).first()
    if not home_gm or not away_gm:
        return

    hs, as_ = match.home_score, match.away_score
    home_gm.played += 1
    away_gm.played += 1
    home_gm.score_for     += hs
    home_gm.score_against += as_
    away_gm.score_for     += as_
    away_gm.score_against += hs

    if hs > as_:
        home_gm.wins   += 1; home_gm.points += comp.win_points
        away_gm.losses += 1; away_gm.points += comp.loss_points
    elif hs < as_:
        away_gm.wins   += 1; away_gm.points += comp.win_points
        home_gm.losses += 1; home_gm.points += comp.loss_points
    else:
        home_gm.draws += 1; home_gm.points += comp.draw_points
        away_gm.draws += 1; away_gm.points += comp.draw_points

    _recalc_rank(match.group_id)


def _undo_standings(match, comp):
    """撤销积分更新"""
    home_gm = GroupMember.query.filter_by(
        group_id=match.group_id, registration_id=match.home_reg_id
    ).first()
    away_gm = GroupMember.query.filter_by(
        group_id=match.group_id, registration_id=match.away_reg_id
    ).first()
    if not home_gm or not away_gm:
        return

    hs, as_ = match.home_score, match.away_score
    home_gm.played = max(0, home_gm.played - 1)
    away_gm.played = max(0, away_gm.played - 1)
    home_gm.score_for     = max(0, home_gm.score_for - hs)
    home_gm.score_against = max(0, home_gm.score_against - as_)
    away_gm.score_for     = max(0, away_gm.score_for - as_)
    away_gm.score_against = max(0, away_gm.score_against - hs)

    if hs > as_:
        home_gm.wins   = max(0, home_gm.wins - 1)
        home_gm.points = max(0, home_gm.points - comp.win_points)
        away_gm.losses = max(0, away_gm.losses - 1)
        away_gm.points = max(0, away_gm.points - comp.loss_points)
    elif hs < as_:
        away_gm.wins   = max(0, away_gm.wins - 1)
        away_gm.points = max(0, away_gm.points - comp.win_points)
        home_gm.losses = max(0, home_gm.losses - 1)
        home_gm.points = max(0, home_gm.points - comp.loss_points)
    else:
        home_gm.draws  = max(0, home_gm.draws - 1)
        home_gm.points = max(0, home_gm.points - comp.draw_points)
        away_gm.draws  = max(0, away_gm.draws - 1)
        away_gm.points = max(0, away_gm.points - comp.draw_points)

    _recalc_rank(match.group_id)


def _recalc_rank(group_id):
    """重新计算组内排名"""
    members = GroupMember.query.filter_by(group_id=group_id)\
        .order_by(GroupMember.points.desc(),
                   (GroupMember.score_for - GroupMember.score_against).desc(),
                   GroupMember.score_for.desc()).all()
    for i, m in enumerate(members, 1):
        m.rank = i


def _check_and_gen_knockout(comp):
    """混合赛：检查小组赛是否全部结束，若是则生成淘汰赛"""
    group_matches = Match.query.filter_by(
        competition_id=comp.id, stage='group'
    ).all()
    if not group_matches:
        return
    if any(m.status not in ('finished', 'bye') for m in group_matches):
        return

    # 已有淘汰赛则跳过
    ko_exists = Match.query.filter(
        Match.competition_id == comp.id,
        Match.stage != 'group'
    ).first()
    if ko_exists:
        return

    # 取各组前 N 名晋级
    groups = Group.query.filter_by(competition_id=comp.id, stage='group').all()
    per_group = max(1, comp.top_advance // len(groups)) if groups else comp.top_advance
    qualifiers = []
    for g in groups:
        members = GroupMember.query.filter_by(group_id=g.id)\
            .order_by(GroupMember.points.desc(),
                       GroupMember.score_for.desc()).limit(per_group).all()
        qualifiers.extend([m.registration for m in members])

    qualifiers = qualifiers[:comp.top_advance]
    if len(qualifiers) >= 2:
        _gen_knockout(comp, qualifiers)
        db.session.commit()
        flash(f'小组赛已全部结束，已自动生成淘汰赛（{len(qualifiers)} 支队伍晋级）', 'success')
