import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, jsonify)
from functools import wraps

student_bp = Blueprint('student', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'student':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def _sid():
    return session.get('student_id')

# ── Dashboard ──────────────────────────────────────────────────────────────────
@student_bp.route('/dashboard')
@login_required
def dashboard():
    from database.db import (get_student_by_id, get_attempts_by_student,
                              get_active_tests, get_passage)
    from collections import defaultdict

    student  = get_student_by_id(_sid()) or {}
    attempts = get_attempts_by_student(_sid())
    attempts_sorted = sorted(attempts, key=lambda a: str(a.get('Date','')), reverse=True)

    # Stats
    err_vals = []
    wpm_vals = []
    for a in attempts:
        try: err_vals.append(float(a.get('ErrorPercent',0)))
        except: pass
        try: wpm_vals.append(float(a.get('WPM',0)))
        except: pass

    stats = {
        'total': len(attempts),
        'avg_err': round(sum(err_vals)/len(err_vals),2) if err_vals else 0,
        'best_err': round(min(err_vals),2) if err_vals else 0,
        'avg_wpm': round(sum(wpm_vals)/len(wpm_vals),1) if wpm_vals else 0,
        'passed': sum(1 for e in err_vals if e <= 5),
    }

    # Streak — count consecutive days with at least one attempt
    from datetime import datetime, timedelta
    today = datetime.now().date()
    attempt_dates = set()
    for a in attempts:
        try:
            d = str(a.get('Date',''))[:10]
            attempt_dates.add(d)
        except: pass
    streak = 0
    check = today
    while str(check) in attempt_dates:
        streak += 1
        check -= timedelta(days=1)

    # Active tests for this student
    active_tests = []
    for t in get_active_tests():
        allowed = str(t.get('AllowedStudents','ALL'))
        if allowed == 'ALL' or _sid() in allowed.split(','):
            p = get_passage(t.get('PassageCode',''))
            active_tests.append({**t, '_passage': p})

    # Chart data — last 10 attempts error%
    chart_data = []
    for a in attempts_sorted[:10][::-1]:
        chart_data.append({
            'date': str(a.get('Date',''))[:10],
            'err':  float(a.get('ErrorPercent',0)),
            'wpm':  float(a.get('WPM',0)),
        })

    from datetime import datetime
    return render_template('student/dashboard.html',
        now_hour=datetime.now().hour,
        student=student,
        stats=stats,
        streak=streak,
        recent=attempts_sorted[:5],
        active_tests=active_tests,
        chart_data=chart_data,
    )

# ── Passage Library ────────────────────────────────────────────────────────────
@student_bp.route('/passages')
@login_required
def passages():
    from database.db import get_active_passages
    all_p = get_active_passages()
    cats  = sorted(set(str(p.get('Category','')) for p in all_p if p.get('Category')))
    return render_template('student/passages.html', passages=all_p, categories=cats)

# ── Practice — view passage and transcribe ─────────────────────────────────────
@student_bp.route('/practice/<code>')
@login_required
def practice(code):
    from database.db import get_passage, get_attempts_by_student
    passage = get_passage(code)
    if not passage or str(passage.get('Active','')).lower() != 'true':
        return redirect(url_for('student.passages'))
    prev = [a for a in get_attempts_by_student(_sid())
            if str(a.get('PassageCode','')).lower() == code.lower()]
    prev_sorted = sorted(prev, key=lambda a: str(a.get('Date','')), reverse=True)
    return render_template('student/practice.html',
        passage=passage, prev_attempts=prev_sorted[:3])

# ── Submit practice transcription ─────────────────────────────────────────────
@student_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    from database.db import get_passage, save_attempt
    from engine.evaluator import evaluate_and_highlight as evaluate
    data = request.get_json()
    if not data:
        return jsonify({'status':'error','message':'No data'}), 400

    code       = str(data.get('passage_code','')).strip()
    typed_text = str(data.get('typed_text','')).strip()
    time_taken = int(data.get('time_taken', 0))

    passage = get_passage(code)
    if not passage:
        return jsonify({'status':'error','message':'Passage not found'}), 404

    original = str(passage.get('Passage',''))
    word_count = int(passage.get('TotalWords', len(original.split())))

    result, highlighted = evaluate(original, typed_text, word_count)
    typed_words = len(typed_text.split())

    attempt_id = save_attempt(
        student_id=_sid(),
        passage_code=code,
        result=result,
        time_taken=time_taken,
        typed_words=typed_words,
        highlighted=highlighted,
        test_id='',
        mode='Practice',
    )

    return jsonify({
        'status': 'ok',
        'attempt_id': attempt_id,
        'result': result,
        'highlighted': highlighted,
    })

# ── Test by code (PC+mobile split workflow) ────────────────────────────────────
@student_bp.route('/test')
@login_required
def test_entry():
    """Student enters a test/passage code to start a test."""
    return render_template('student/test_entry.html')

@student_bp.route('/test/<test_id>')
@login_required
def test(test_id):
    from database.db import get_test, get_passage
    t = get_test(test_id)
    if not t:
        return render_template('student/test_entry.html',
                               error='Test not found. Check the code.')
    if str(t.get('Active','')).lower() != 'true':
        return render_template('student/test_entry.html',
                               error='This test is no longer active.')
    allowed = str(t.get('AllowedStudents','ALL'))
    if allowed != 'ALL' and _sid() not in allowed.split(','):
        return render_template('student/test_entry.html',
                               error='You are not enrolled in this test.')
    passage = get_passage(t.get('PassageCode',''))
    if not passage:
        return render_template('student/test_entry.html',
                               error='Passage not found for this test.')
    return render_template('student/test.html', test=t, passage=passage)

@student_bp.route('/test/<test_id>/submit', methods=['POST'])
@login_required
def test_submit(test_id):
    from database.db import get_test, get_passage, save_attempt
    from engine.evaluator import evaluate_and_highlight as evaluate
    data = request.get_json()
    t = get_test(test_id)
    if not t:
        return jsonify({'status':'error','message':'Test not found'}), 404

    typed_text = str(data.get('typed_text','')).strip()
    time_taken = int(data.get('time_taken', 0))
    passage    = get_passage(t.get('PassageCode',''))

    original   = str(passage.get('Passage',''))
    word_count = int(passage.get('TotalWords', len(original.split())))

    result, highlighted = evaluate(original, typed_text, word_count)

    attempt_id = save_attempt(
        student_id=_sid(),
        passage_code=t.get('PassageCode',''),
        result=result,
        time_taken=time_taken,
        typed_words=len(typed_text.split()),
        highlighted=highlighted,
        test_id=test_id,
        mode='Test',
    )

    return jsonify({
        'status': 'ok',
        'attempt_id': attempt_id,
        'result': result,
        'highlighted': highlighted,
    })

# ── Attempt result view ────────────────────────────────────────────────────────
@student_bp.route('/attempt/<attempt_id>')
@login_required
def attempt_result(attempt_id):
    from database.db import get_attempt, get_passage
    a = get_attempt(attempt_id)
    if not a or str(a.get('StudentID','')) != _sid():
        return redirect(url_for('student.dashboard'))
    passage = get_passage(a.get('PassageCode',''))
    return render_template('student/attempt_result.html', attempt=a, passage=passage)

# ── History ────────────────────────────────────────────────────────────────────
@student_bp.route('/history')
@login_required
def history():
    from database.db import get_attempts_by_student
    attempts = sorted(get_attempts_by_student(_sid()),
                      key=lambda a: str(a.get('Date','')), reverse=True)
    return render_template('student/history.html', attempts=attempts)

# ── Leaderboard ───────────────────────────────────────────────────────────────
@student_bp.route('/leaderboard')
@login_required
def leaderboard():
    from database.db import get_all_students, get_all_attempts
    from datetime import datetime
    from collections import defaultdict

    students  = {str(s['StudentID']): s.get('Name','') for s in get_all_students()
                 if str(s.get('Approved','')).upper() == 'YES'}
    attempts  = get_all_attempts()

    now   = datetime.now()
    month = f'{now.year:04d}-{now.month:02d}'

    month_stats = defaultdict(lambda: {'attempts':0,'total_err':0,'total_wpm':0,'passed':0})
    for a in attempts:
        if str(a.get('Date',''))[:7] != month: continue
        sid = str(a.get('StudentID',''))
        if sid not in students: continue
        s = month_stats[sid]
        s['attempts'] += 1
        try: s['total_err'] += float(a.get('ErrorPercent',0))
        except: pass
        try: s['total_wpm'] += float(a.get('WPM',0))
        except: pass
        try:
            if float(a.get('ErrorPercent',0)) <= 5: s['passed'] += 1
        except: pass

    rows = []
    for sid, s in month_stats.items():
        n = s['attempts'] or 1
        rows.append({
            'id':      sid,
            'name':    students.get(sid, sid),
            'attempts': s['attempts'],
            'avg_err': round(s['total_err']/n, 2),
            'avg_wpm': round(s['total_wpm']/n, 1),
            'passed':  s['passed'],
            'is_me':   sid == _sid(),
        })
    rows.sort(key=lambda x: (x['avg_err'], -x['attempts']))

    return render_template('student/leaderboard.html',
                           rows=rows, month=now.strftime('%B %Y'))
