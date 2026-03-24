from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from database.db import init_db, get_db
import hashlib, os, json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dt-steno-secret-2024")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ── Init DB on startup ─────────────────────────────────────────────
with app.app_context():
    init_db()

# ══════════════════════════════════════
#  PUBLIC / AUTH ROUTES
# ══════════════════════════════════════

@app.route("/")
def home():
    return redirect(url_for("landing"))

@app.route("/landing")
def landing():
    return render_template("index.html")

# ── Student Registration ───────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name       = data.get("name","").strip()
    mobile     = data.get("mobile","").strip()
    class_code = data.get("class_code","").strip().upper()
    password   = data.get("password","")

    if not all([name, mobile, class_code, password]):
        return jsonify(status="error", message="All fields are required.")
    if len(mobile) != 10 or not mobile.isdigit():
        return jsonify(status="error", message="Enter a valid 10-digit mobile number.")
    if len(password) < 6:
        return jsonify(status="error", message="Password must be at least 6 characters.")

    db = get_db()
    # Check class code exists
    batch = db.execute("SELECT id FROM batches WHERE code=?", (class_code,)).fetchone()
    if not batch:
        return jsonify(status="error", message="Invalid class code. Ask your instructor.")
    # Check duplicate mobile
    existing = db.execute("SELECT id FROM students WHERE mobile=?", (mobile,)).fetchone()
    if existing:
        return jsonify(status="error", message="This mobile number is already registered.")

    db.execute(
        "INSERT INTO students (name, mobile, password_hash, batch_id, status) VALUES (?,?,?,?,?)",
        (name, mobile, hash_pw(password), batch["id"], "pending")
    )
    db.commit()
    return jsonify(status="ok", message="Registration request sent. Wait for instructor approval.")

# ── Student Login ──────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    mobile   = data.get("identifier","").strip()
    password = data.get("password","")

    db  = get_db()
    row = db.execute("SELECT * FROM students WHERE mobile=?", (mobile,)).fetchone()
    if not row or row["password_hash"] != hash_pw(password):
        return jsonify(status="error", message="Invalid mobile number or password.")
    if row["status"] == "pending":
        return jsonify(status="error", message="Your account is pending instructor approval.")
    if row["status"] == "rejected":
        return jsonify(status="error", message="Your registration was rejected. Contact your instructor.")

    session["student_id"]   = row["id"]
    session["student_name"] = row["name"]
    return jsonify(status="ok", redirect="/student/dashboard")

# ── Admin Login ────────────────────────────────────────────────────
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()
    if data.get("password") == ADMIN_PASSWORD:
        session["admin"] = True
        return jsonify(status="ok", redirect="/admin/dashboard")
    return jsonify(status="error", message="Incorrect admin password.")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

# ══════════════════════════════════════
#  STUDENT DASHBOARD
# ══════════════════════════════════════

@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect(url_for("landing"))
    db  = get_db()
    sid = session["student_id"]
    student  = db.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    passages = db.execute(
        "SELECT p.* FROM passages p "
        "JOIN batches b ON p.batch_id = b.id "
        "WHERE b.id = ? ORDER BY p.created_at DESC", (student["batch_id"],)
    ).fetchall()
    results = db.execute(
        "SELECT r.*, p.title FROM results r JOIN passages p ON r.passage_id=p.id "
        "WHERE r.student_id=? ORDER BY r.submitted_at DESC LIMIT 10", (sid,)
    ).fetchall()
    # Leaderboard (same batch)
    leaderboard = db.execute("""
        SELECT s.name,
               COUNT(r.id) as attempts,
               ROUND(AVG(r.error_pct),1) as avg_error,
               MAX(r.wpm) as best_wpm,
               SUM(CASE WHEN r.verdict='PASS' THEN 1 ELSE 0 END) as passes
        FROM students s
        LEFT JOIN results r ON r.student_id = s.id
        WHERE s.batch_id = ? AND s.status='approved'
        GROUP BY s.id ORDER BY avg_error ASC LIMIT 20
    """, (student["batch_id"],)).fetchall()
    return render_template("student_dashboard.html",
        student=student, passages=passages,
        results=results, leaderboard=leaderboard)

# ── Take a test ────────────────────────────────────────────────────
@app.route("/student/test/<int:passage_id>")
def take_test(passage_id):
    if "student_id" not in session:
        return redirect(url_for("landing"))
    db = get_db()
    passage = db.execute("SELECT * FROM passages WHERE id=?", (passage_id,)).fetchone()
    if not passage:
        return redirect(url_for("student_dashboard"))
    return render_template("typing_test.html", passage=passage)

@app.route("/student/submit", methods=["POST"])
def submit_test():
    if "student_id" not in session:
        return jsonify(status="error", message="Not logged in")
    data       = request.get_json()
    passage_id = data.get("passage_id")
    typed      = data.get("typed","").strip()
    time_taken = data.get("time_taken", 0)
    db         = get_db()
    passage    = db.execute("SELECT * FROM passages WHERE id=?", (passage_id,)).fetchone()
    if not passage:
        return jsonify(status="error", message="Passage not found")

    original = passage["content"]
    result   = evaluate(original, typed, time_taken)
    db.execute(
        "INSERT INTO results (student_id, passage_id, typed_text, full_errors, half_errors, "
        "omit_errors, extra_errors, error_pct, wpm, verdict, submitted_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (session["student_id"], passage_id, typed,
         result["full"], result["half"], result["omit"], result["extra"],
         result["error_pct"], result["wpm"], result["verdict"], datetime.now().isoformat())
    )
    db.commit()
    return jsonify(status="ok", result=result)

def evaluate(original, typed, time_taken):
    """Simple word-level evaluation matching the 5% error threshold rule."""
    orig_words  = original.split()
    typed_words = typed.split()
    total       = len(orig_words)

    full = half = omit = extra = 0
    for i, ow in enumerate(orig_words):
        if i >= len(typed_words):
            omit += 1
        else:
            tw = typed_words[i]
            if tw.lower() == ow.lower() and tw != ow:
                half += 1          # capitalisation only
            elif tw.lower() != ow.lower():
                full += 1          # wrong word

    extra = max(0, len(typed_words) - len(orig_words))
    weighted_errors = full + (half * 0.5) + (omit * 0.5) + (extra * 0.5)
    error_pct = round((weighted_errors / total) * 100, 2) if total else 0
    wpm = round((len(typed.split()) / (time_taken / 60))) if time_taken > 0 else 0
    verdict = "PASS" if error_pct <= 5 else "FAIL"
    return dict(full=full, half=half, omit=omit, extra=extra,
                error_pct=error_pct, wpm=wpm, verdict=verdict, total=total)

# ══════════════════════════════════════
#  ADMIN DASHBOARD
# ══════════════════════════════════════

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("landing"))
    db = get_db()
    pending  = db.execute(
        "SELECT s.*, b.name as batch_name FROM students s JOIN batches b ON s.batch_id=b.id "
        "WHERE s.status='pending' ORDER BY s.created_at DESC").fetchall()
    students = db.execute(
        "SELECT s.*, b.name as batch_name, "
        "COUNT(r.id) as attempts, "
        "ROUND(AVG(r.error_pct),1) as avg_error "
        "FROM students s JOIN batches b ON s.batch_id=b.id "
        "LEFT JOIN results r ON r.student_id=s.id "
        "WHERE s.status='approved' GROUP BY s.id ORDER BY s.name").fetchall()
    passages = db.execute("SELECT p.*, b.name as batch_name FROM passages p JOIN batches b ON p.batch_id=b.id ORDER BY p.created_at DESC").fetchall()
    batches  = db.execute("SELECT * FROM batches ORDER BY name").fetchall()
    return render_template("admin_dashboard.html",
        pending=pending, students=students,
        passages=passages, batches=batches)

@app.route("/admin/approve/<int:sid>", methods=["POST"])
def approve_student(sid):
    if not session.get("admin"): return jsonify(status="error")
    get_db().execute("UPDATE students SET status='approved' WHERE id=?", (sid,))
    get_db().commit()
    return jsonify(status="ok")

@app.route("/admin/reject/<int:sid>", methods=["POST"])
def reject_student(sid):
    if not session.get("admin"): return jsonify(status="error")
    get_db().execute("UPDATE students SET status='rejected' WHERE id=?", (sid,))
    get_db().commit()
    return jsonify(status="ok")

@app.route("/admin/passage/add", methods=["POST"])
def add_passage():
    if not session.get("admin"): return jsonify(status="error")
    data     = request.get_json()
    title    = data.get("title","").strip()
    content  = data.get("content","").strip()
    category = data.get("category","General")
    batch_id = data.get("batch_id")
    audio_url= data.get("audio_url","")
    if not all([title, content, batch_id]):
        return jsonify(status="error", message="Title, content and batch are required.")
    db = get_db()
    db.execute(
        "INSERT INTO passages (title, content, category, batch_id, audio_url, created_at) VALUES (?,?,?,?,?,?)",
        (title, content, category, batch_id, audio_url, datetime.now().isoformat())
    )
    db.commit()
    return jsonify(status="ok")

@app.route("/admin/passage/delete/<int:pid>", methods=["POST"])
def delete_passage(pid):
    if not session.get("admin"): return jsonify(status="error")
    get_db().execute("DELETE FROM passages WHERE id=?", (pid,))
    get_db().commit()
    return jsonify(status="ok")

@app.route("/admin/batch/add", methods=["POST"])
def add_batch():
    if not session.get("admin"): return jsonify(status="error")
    data = request.get_json()
    name = data.get("name","").strip()
    code = data.get("code","").strip().upper()
    if not name or not code:
        return jsonify(status="error", message="Name and code required.")
    db = get_db()
    try:
        db.execute("INSERT INTO batches (name, code) VALUES (?,?)", (name, code))
        db.commit()
        return jsonify(status="ok")
    except:
        return jsonify(status="error", message="Class code already exists.")

@app.route("/admin/results/<int:sid>")
def student_results(sid):
    if not session.get("admin"): return jsonify(status="error")
    db = get_db()
    rows = db.execute(
        "SELECT r.*, p.title FROM results r JOIN passages p ON r.passage_id=p.id "
        "WHERE r.student_id=? ORDER BY r.submitted_at DESC", (sid,)
    ).fetchall()
    return jsonify(results=[dict(r) for r in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
