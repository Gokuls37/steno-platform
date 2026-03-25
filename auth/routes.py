import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, jsonify)
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── Dashboard ──────────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    from database.db import get_all_students, get_all_attempts, get_all_tests
    from datetime import datetime
    from collections import defaultdict

    students = get_all_students()
    attempts = get_all_attempts()
    tests    = get_all_tests()
    now      = datetime.now()
    month    = f'{now.year:04d}-{now.month:02d}'

    approved  = [s for s in students if str(s.get('Approved','')).upper() == 'YES']
    pending   = [s for s in students if str(s.get('Approved','')).upper() == 'PENDING']
    month_att = [a for a in attempts if str(a.get('Date',''))[:7] == month]
    active_t  = [t for t in tests if str(t.get('Active','')).lower() == 'true']

    err_vals = []
    for a in month_att:
        try: err_vals.append(float(a.get('ErrorPercent',0)))
        except: pass

    stats = {
        'students':       len(approved),
        'pending':        len(pending),
        'month_attempts': len(month_att),
        'active_tests':   len(active_t),
        'avg_err':        round(sum(err_vals)/len(err_vals),2) if err_vals else 0,
        'pass_rate':      round(sum(1 for e in err_vals if e<=5)/len(err_vals)*100,1) if err_vals else 0,
    }

    # Recent attempts
    recent = sorted(attempts, key=lambda a: str(a.get('Date','')), reverse=True)[:8]

    # Student leaderboard this month
    s_map = {str(s['StudentID']): s.get('Name','') for s in approved}
    sdata = defaultdict(lambda:{'n':0,'err':0})
    for a in month_att:
        sid = str(a.get('StudentID',''))
        sdata[sid]['n'] += 1
        try: sdata[sid]['err'] += float(a.get('ErrorPercent',0))
        except: pass
    top_students = sorted(
        [{'id':sid,'name':s_map.get(sid,sid),
          'attempts':d['n'],
          'avg_err':round(d['err']/d['n'],2) if d['n'] else 0}
         for sid,d in sdata.items()],
        key=lambda x: x['avg_err']
    )[:5]

    return render_template('admin/dashboard.html',
        stats=stats, recent=recent,
        pending_students=pending,
        top_students=top_students,
        month=now.strftime('%B %Y'),
        active='dashboard',
        pending_count=len(pending),
    )

# ── Students ───────────────────────────────────────────────────────────────────
@admin_bp.route('/students')
@admin_required
def students():
    from database.db import get_all_students
    all_s = get_all_students()
    pend = sum(1 for s in all_s if str(s.get('Approved','')).upper()=='PENDING')
    return render_template('admin/students.html', students=all_s,
        active='students', pending_count=pend)

@admin_bp.route('/students/<sid>/approve', methods=['POST'])
@admin_required
def approve(sid):
    from database.db import approve_student
    approve_student(sid)
    return jsonify({'status':'ok'})

@admin_bp.route('/students/<sid>/reject', methods=['POST'])
@admin_required
def reject(sid):
    from database.db import reject_student
    reject_student(sid)
    return jsonify({'status':'ok'})

@admin_bp.route('/students/create', methods=['POST'])
@admin_required
def create_student():
    from database.db import admin_create_student
    d = request.get_json()
    sid = admin_create_student(
        d.get('name',''), d.get('mobile',''),
        d.get('email',''), d.get('password',''),
        d.get('batch',''),
    )
    return jsonify({'status':'ok','student_id':sid})

@admin_bp.route('/students/<sid>')
@admin_required
def student_profile(sid):
    from database.db import get_student_by_id, get_attempts_by_student
    student  = get_student_by_id(sid)
    attempts = sorted(get_attempts_by_student(sid),
                      key=lambda a: str(a.get('Date','')), reverse=True)
    return render_template('admin/student_profile.html',
        student=student, attempts=attempts, active='students', pending_count=0)

# ── Passages ───────────────────────────────────────────────────────────────────
@admin_bp.route('/passages')
@admin_required
def passages():
    from database.db import get_all_passages, get_all_attempts
    from collections import defaultdict
    all_p = get_all_passages()
    att   = get_all_attempts()
    cnt   = defaultdict(int)
    for a in att:
        cnt[str(a.get('PassageCode','')).lower()] += 1
    for p in all_p:
        p['_attempts'] = cnt[str(p.get('PassageCode','')).lower()]
    cats = sorted(set(str(p.get('Category','')) for p in all_p if p.get('Category')))
    return render_template('admin/passages.html', passages=all_p, categories=cats,
        active='passages', pending_count=0)

@admin_bp.route('/passages/add', methods=['POST'])
@admin_required
def add_passage():
    from database.db import add_passage
    d = request.get_json()
    text = str(d.get('text',''))
    wc = add_passage(
        code=d.get('code','').strip().upper(),
        name=d.get('name','').strip(),
        category=d.get('category',''),
        speed=d.get('speed',''),
        text=text,
        audio_link=d.get('audio_link',''),
    )
    return jsonify({'status':'ok','word_count':wc})

@admin_bp.route('/passages/toggle', methods=['POST'])
@admin_required
def toggle_passage():
    from database.db import toggle_passage as db_toggle
    d = request.get_json()
    db_toggle(d.get('code'), d.get('active') == True)
    return jsonify({'status':'ok'})

# ── Tests ──────────────────────────────────────────────────────────────────────
@admin_bp.route('/tests')
@admin_required
def tests():
    from database.db import get_all_tests, get_all_students, get_passage
    all_t = get_all_tests()
    for t in all_t:
        p = get_passage(t.get('PassageCode',''))
        t['_passage_name'] = p.get('PassageName','') if p else '—'
    students = [s for s in get_all_students()
                if str(s.get('Approved','')).upper() == 'YES']
    return render_template('admin/tests.html', tests=all_t, students=students,
        active='tests', pending_count=0)

@admin_bp.route('/tests/create', methods=['POST'])
@admin_required
def create_test():
    from database.db import create_test as db_create, get_passage
    d = request.get_json()
    code = str(d.get('passage_code','')).strip().upper()
    if not get_passage(code):
        return jsonify({'status':'error','message':'Passage code not found'}), 404
    allowed = ','.join(d.get('allowed_students',['ALL'])) if isinstance(d.get('allowed_students'), list) else 'ALL'
    tid = db_create(
        passage_code   = code,
        audio_link     = d.get('audio_link',''),
        created_by     = 'Admin',
        expires_at     = d.get('expires_at',''),
        allowed_students = allowed,
        time_limit     = int(d.get('time_limit', 30)),
        notes          = d.get('notes',''),
    )
    return jsonify({'status':'ok','test_id':tid,
                    'test_link': f'/student/test/{tid}'})

@admin_bp.route('/tests/<tid>/deactivate', methods=['POST'])
@admin_required
def deactivate_test(tid):
    from database.db import deactivate_test as db_deact
    db_deact(tid)
    return jsonify({'status':'ok'})

@admin_bp.route('/tests/<tid>')
@admin_required
def test_detail(tid):
    from database.db import get_test, get_passage, get_attempts_by_test, get_student_by_id
    t = get_test(tid)
    if not t: return redirect(url_for('admin.tests'))
    p = get_passage(t.get('PassageCode',''))
    attempts = get_attempts_by_test(tid)
    for a in attempts:
        s = get_student_by_id(a.get('StudentID',''))
        a['_student_name'] = s.get('Name','') if s else '—'
    return render_template('admin/test_detail.html', test=t, passage=p, attempts=attempts,
        active='tests', pending_count=0)

# ── Attempt correction ────────────────────────────────────────────────────────
@admin_bp.route('/attempts')
@admin_required
def attempts():
    from database.db import get_all_attempts, get_student_by_id
    all_a = sorted(get_all_attempts(), key=lambda a: str(a.get('Date','')), reverse=True)
    for a in all_a[:50]:
        s = get_student_by_id(a.get('StudentID',''))
        a['_student_name'] = s.get('Name','') if s else '—'
    return render_template('admin/attempts.html', attempts=all_a[:50],
        active='attempts', pending_count=0)

@admin_bp.route('/attempts/<aid>')
@admin_required
def attempt_detail(aid):
    from database.db import get_attempt, get_passage, get_student_by_id
    a = get_attempt(aid)
    if not a: return redirect(url_for('admin.attempts'))
    p = get_passage(a.get('PassageCode',''))
    s = get_student_by_id(a.get('StudentID',''))
    return render_template('admin/attempt_detail.html', attempt=a, passage=p, student=s,
        active='attempts', pending_count=0)

@admin_bp.route('/attempts/<aid>/correct', methods=['POST'])
@admin_required
def correct_attempt(aid):
    from database.db import update_attempt_correction, get_attempt, get_passage
    d = request.get_json()
    a = get_attempt(aid)
    if not a: return jsonify({'status':'error','message':'Not found'}), 404
    p = get_passage(a.get('PassageCode',''))
    wc = int(p.get('TotalWords', a.get('TypedWords', 100))) if p else int(a.get('TypedWords',100))
    ok, total, pct = update_attempt_correction(
        aid,
        float(d.get('full',0)), float(d.get('half',0)),
        float(d.get('omission',0)), float(d.get('extra',0)),
        float(d.get('cap',0)), float(d.get('fs',0)),
        str(d.get('note','')), wc,
    )
    if ok:
        return jsonify({'status':'ok','new_total':total,'new_pct':pct})
    return jsonify({'status':'error','message':'Row not found'}), 404

# ── Monthly report ────────────────────────────────────────────────────────────
@admin_bp.route('/report/monthly')
@admin_required
def monthly_report():
    from database.db import get_all_attempts, get_all_students
    import calendar
    from datetime import datetime
    from collections import defaultdict

    now   = datetime.now()
    year  = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))

    attempts = get_all_attempts()
    students = get_all_students()
    s_map    = {str(s['StudentID']): s.get('Name','') for s in students}

    month_str = f'{year:04d}-{month:02d}'
    m_att = [a for a in attempts if str(a.get('Date',''))[:7] == month_str]

    sdata = defaultdict(lambda:{'n':0,'err':0,'wpm':0,'best':None,'passed':0})
    for a in m_att:
        sid = str(a.get('StudentID',''))
        s = sdata[sid]
        s['n'] += 1
        try:
            e = float(a.get('ErrorPercent',0))
            s['err'] += e
            s['best'] = e if s['best'] is None else min(s['best'], e)
            if e <= 5: s['passed'] += 1
        except: pass
        try: s['wpm'] += float(a.get('WPM',0))
        except: pass

    all_errs = []
    for a in m_att:
        try: all_errs.append(float(a.get('ErrorPercent',0)))
        except: pass

    summary = {
        'attempts': len(m_att),
        'students': len(sdata),
        'avg_err':  round(sum(all_errs)/len(all_errs),2) if all_errs else 0,
        'pass_rate':round(sum(1 for e in all_errs if e<=5)/len(all_errs)*100,1) if all_errs else 0,
    }

    rows = sorted([{
        'id': sid, 'name': s_map.get(sid, sid),
        'attempts': d['n'],
        'avg_err':  round(d['err']/d['n'],2) if d['n'] else 0,
        'best_err': round(d['best'],2) if d['best'] is not None else '—',
        'avg_wpm':  round(d['wpm']/d['n'],1) if d['n'] else 0,
        'passed':   d['passed'],
    } for sid, d in sdata.items()], key=lambda x: x['avg_err'])

    years = sorted(set(str(a.get('Date',''))[:4] for a in attempts if a.get('Date')), reverse=True) or [str(now.year)]
    return render_template('admin/monthly_report.html',
        year=year, month=month,
        month_name=calendar.month_name[month],
        summary=summary, rows=rows,
        years=years, months=list(range(1,13)),
        calendar=calendar,
        active='report', pending_count=0,
    )

@admin_bp.route('/report/student/<sid>')
@admin_required
def student_report(sid):
    from database.db import get_student_by_id, get_attempts_by_student
    import calendar
    from datetime import datetime

    now   = datetime.now()
    year  = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))

    student  = get_student_by_id(sid)
    attempts = get_attempts_by_student(sid)
    month_str = f'{year:04d}-{month:02d}'
    m_att = sorted([a for a in attempts if str(a.get('Date',''))[:7] == month_str],
                   key=lambda a: str(a.get('Date','')), reverse=True)

    err_vals = []
    wpm_vals = []
    for a in m_att:
        try: err_vals.append(float(a.get('ErrorPercent',0)))
        except: pass
        try: wpm_vals.append(float(a.get('WPM',0)))
        except: pass

    summary = {
        'attempts':  len(m_att),
        'avg_err':   round(sum(err_vals)/len(err_vals),2) if err_vals else 0,
        'best_err':  round(min(err_vals),2) if err_vals else 0,
        'worst_err': round(max(err_vals),2) if err_vals else 0,
        'avg_wpm':   round(sum(wpm_vals)/len(wpm_vals),1) if wpm_vals else 0,
        'passed':    sum(1 for e in err_vals if e<=5),
        'pass_rate': round(sum(1 for e in err_vals if e<=5)/len(err_vals)*100,1) if err_vals else 0,
    }

    years = sorted(set(str(a.get('Date',''))[:4] for a in attempts if a.get('Date')), reverse=True) or [str(now.year)]
    return render_template('admin/student_report.html',
        student=student, sid=sid,
        month=month, year=year,
        month_name=calendar.month_name[month],
        summary=summary, attempts=m_att,
        years=years, months=list(range(1,13)),
        calendar=calendar,
        active='report', pending_count=0,
    )

# ── Settings ───────────────────────────────────────────────────────────────────
@admin_bp.route('/settings', methods=['GET','POST'])
@admin_required
def settings():
    from database.db import get_setting, set_setting
    if request.method == 'POST':
        d = request.get_json()
        for key, val in d.items():
            set_setting(key, val)
        return jsonify({'status':'ok'})
    code = get_setting('CLASS_CODE','STENO2024')
    return render_template('admin/settings.html', class_code=code,
        active='settings', pending_count=0)

# ── Evaluate tool ──────────────────────────────────────────────────────────────
@admin_bp.route('/evaluate')
@admin_required
def evaluate_tool():
    from database.db import get_active_passages
    passages = get_active_passages()
    return render_template('admin/evaluate.html', passages=passages,
        active='evaluate', pending_count=0)

@admin_bp.route('/evaluate/run', methods=['POST'])
@admin_required
def evaluate_run():
    from database.db import get_passage
    from engine.evaluator import evaluate_and_highlight as evaluate
    d = request.get_json()
    code   = str(d.get('passage_code','')).strip()
    typed  = str(d.get('typed_text','')).strip()
    p = get_passage(code)
    if not p:
        return jsonify({'status':'error','message':'Passage not found'}), 404
    original = str(p.get('Passage',''))
    wc = int(p.get('TotalWords', len(original.split())))
    result, highlighted = evaluate(original, typed, wc)
    return jsonify({'status':'ok','result':result,'highlighted':highlighted})
