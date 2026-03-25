import os
"""
DT-STENO — Google Sheets Database Layer
Sheet: DT-STENO_DB
Tabs:
  Students     — StudentID, Name, Mobile, Email, Password(hashed), ClassCode, Approved, JoinedDate, Batch
  Passages     — PassageCode, PassageName, Category, Speed, Passage, TotalWords, Active, AudioLink
  Attempts     — AttemptID, StudentID, PassageCode, TestID, TimeTaken, TypedWords, WPM,
                 FullMistakes, HalfMistakes, Omissions, ExtraWords, Capitalization, FullStop,
                 TotalErrors, ErrorPercent, Mode, Date, HighlightedPassage, AdminNote, Corrected
  Tests        — TestID, PassageCode, AudioLink, CreatedBy, CreatedAt, ExpiresAt, Active,
                 AllowedStudents, TimeLimitMinutes, Notes
  Settings     — Key, Value
"""
import gspread
from google.oauth2.service_account import Credentials
import uuid, hashlib, os
from datetime import datetime

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def _get_client():
    import json
    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    if google_creds:
        # Running on Render — credentials stored as env var
        info = json.loads(google_creds)
        creds = Credentials.from_service_account_info(info, scopes=SCOPE)
    else:
        # Running locally — credentials in file
        creds = Credentials.from_service_account_file(
            "service_account.json", scopes=SCOPE)
    return gspread.authorize(creds)

def _open_sheet():
    client = _get_client()
    return client.open("DT-STENO_DB")

# ── lazy worksheet cache ──────────────────────────────────────────────────────
_ws = {}

def _ws_get(name):
    if name not in _ws:
        _ws[name] = _open_sheet().worksheet(name)
    return _ws[name]

def _students():  return _ws_get("Students")
def _passages():  return _ws_get("Passages")
def _attempts():  return _ws_get("Attempts")
def _tests():     return _ws_get("Tests")
def _settings():  return _ws_get("Settings")

# ── helpers ───────────────────────────────────────────────────────────────────
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_password(pw, hashed):
    return hash_password(pw) == hashed

def new_id(prefix=""):
    return prefix + str(uuid.uuid4())[:8].upper()

# ── STUDENTS ──────────────────────────────────────────────────────────────────
def get_all_students():
    return _students().get_all_records()

def get_student_by_id(student_id):
    for r in _students().get_all_records():
        if str(r.get("StudentID","")).strip() == str(student_id).strip():
            return r
    return None

def get_student_by_mobile(mobile):
    for r in _students().get_all_records():
        if str(r.get("Mobile","")).strip() == str(mobile).strip():
            return r
    return None


def register_student(name, mobile, password, class_code):
    """Register new student — pending admin approval. Mobile is login ID."""
    # Validate mobile
    mobile = str(mobile).strip().replace(' ','').replace('-','')
    sid = new_id("STU")
    _students().append_row([
        sid, name, mobile,
        hash_password(password),
        class_code.upper().strip(),
        "PENDING",
        datetime.now().strftime("%Y-%m-%d"),
        "",  # Batch
    ])
    return sid

def approve_student(student_id):
    data = _students().get_all_values()
    for i, row in enumerate(data):
        if row and str(row[0]).strip() == str(student_id).strip():
            _students().update_cell(i+1, 7, "YES")
            return True
    return False

def reject_student(student_id):
    data = _students().get_all_values()
    for i, row in enumerate(data):
        if row and str(row[0]).strip() == str(student_id).strip():
            _students().update_cell(i+1, 7, "NO")
            return True
    return False

def authenticate_student(mobile, password):
    """Returns student dict if mobile+password valid and approved."""
    mobile = str(mobile).strip().replace(' ','').replace('-','')
    s = get_student_by_mobile(mobile)
    if not s:
        return None, "Mobile number not registered."
    if str(s.get("Approved","")).upper() == "PENDING":
        return None, "Account pending approval. Your instructor will activate it shortly."
    if str(s.get("Approved","")).upper() == "NO":
        return None, "Account not approved. Contact your instructor."
    if not check_password(password, str(s.get("Password",""))):
        return None, "Incorrect password."
    return s, None

def update_student_batch(student_id, batch):
    data = _students().get_all_values()
    for i, row in enumerate(data):
        if row and str(row[0]).strip() == str(student_id).strip():
            _students().update_cell(i+1, 9, batch)
            return True
    return False

def admin_create_student(name, mobile, password, batch=""):
    """Admin directly creates an approved student account."""
    mobile = str(mobile).strip().replace(' ','').replace('-','')
    sid = new_id("STU")
    _students().append_row([
        sid, name, mobile,
        hash_password(password),
        "ADMIN",
        "YES",
        datetime.now().strftime("%Y-%m-%d"),
        batch,
    ])
    return sid

# ── PASSAGES ──────────────────────────────────────────────────────────────────
def get_all_passages():
    return _passages().get_all_records()

def get_passage(code):
    for r in _passages().get_all_records():
        if str(r.get("PassageCode","")).strip().lower() == str(code).strip().lower():
            return r
    return None

def get_active_passages():
    return [p for p in get_all_passages()
            if str(p.get("Active","")).lower() == "true"]

def get_passages_by_category(category):
    return [p for p in get_active_passages()
            if str(p.get("Category","")).strip() == category]

def add_passage(code, name, category, speed, text, audio_link="", active=True):
    words = len(text.split())
    _passages().append_row([
        code, name, category, speed, text, words,
        "TRUE" if active else "FALSE",
        audio_link,
    ])
    return words

def toggle_passage(code, active):
    data = _passages().get_all_values()
    header = data[0] if data else []
    try:
        active_col = header.index("Active") + 1
    except ValueError:
        active_col = 7
    for i, row in enumerate(data):
        if i == 0: continue
        if row and str(row[0]).strip().lower() == str(code).strip().lower():
            _passages().update_cell(i+1, active_col, "TRUE" if active else "FALSE")
            return True
    return False

# ── TESTS ─────────────────────────────────────────────────────────────────────
def get_all_tests():
    return _tests().get_all_records()

def get_test(test_id):
    for r in _tests().get_all_records():
        if str(r.get("TestID","")).strip() == str(test_id).strip():
            return r
    return None

def get_active_tests():
    return [t for t in get_all_tests()
            if str(t.get("Active","")).lower() == "true"]

def create_test(passage_code, audio_link, created_by, expires_at,
                allowed_students="ALL", time_limit=30, notes=""):
    test_id = new_id("TST")
    _tests().append_row([
        test_id, passage_code, audio_link, created_by,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        expires_at, "TRUE",
        allowed_students, time_limit, notes,
    ])
    return test_id

def deactivate_test(test_id):
    data = _tests().get_all_values()
    for i, row in enumerate(data):
        if row and str(row[0]).strip() == str(test_id).strip():
            _tests().update_cell(i+1, 7, "FALSE")
            return True
    return False

# ── ATTEMPTS ──────────────────────────────────────────────────────────────────
def save_attempt(student_id, passage_code, result, time_taken, typed_words,
                 highlighted, test_id="", mode="Practice"):
    attempt_id = new_id("ATT")
    _attempts().append_row([
        attempt_id, student_id, passage_code, test_id,
        time_taken, typed_words,
        result.get("wpm", 0),
        result.get("full", 0),
        result.get("half", 0),
        result.get("omission", 0),
        result.get("extra", 0),
        result.get("capitalization", 0),
        result.get("fullstop", 0),
        result.get("total_errors", 0),
        result.get("error_percent", 0),
        mode,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        highlighted,
        "",     # AdminNote
        "NO",   # Corrected
    ])
    return attempt_id

def get_attempts_by_student(student_id):
    return [r for r in _attempts().get_all_records()
            if str(r.get("StudentID","")).strip() == str(student_id).strip()]

def get_attempt(attempt_id):
    for r in _attempts().get_all_records():
        if str(r.get("AttemptID","")).strip() == str(attempt_id).strip():
            return r
    return None

def get_all_attempts():
    return _attempts().get_all_records()

def get_attempts_by_test(test_id):
    return [r for r in _attempts().get_all_records()
            if str(r.get("TestID","")).strip() == str(test_id).strip()]

def update_attempt_correction(attempt_id, full, half, omission, extra,
                               cap, fs, note, word_count):
    data = _attempts().get_all_values()
    total = full + half + omission + extra + cap + fs
    pct   = round(total / max(word_count, 1) * 100, 2)
    # Column indices (1-based): 8=Full,9=Half,10=Omissions,11=Extra,12=Cap,13=FS,14=Total,15=ErrPct,19=Note,20=Corrected
    for i, row in enumerate(data):
        if row and str(row[0]).strip() == str(attempt_id).strip():
            r = i + 1
            _attempts().update_cell(r,  8, full)
            _attempts().update_cell(r,  9, half)
            _attempts().update_cell(r, 10, omission)
            _attempts().update_cell(r, 11, extra)
            _attempts().update_cell(r, 12, cap)
            _attempts().update_cell(r, 13, fs)
            _attempts().update_cell(r, 14, total)
            _attempts().update_cell(r, 15, pct)
            _attempts().update_cell(r, 19, note)
            _attempts().update_cell(r, 20, "YES")
            return True, total, pct
    return False, 0, 0

# ── SETTINGS ──────────────────────────────────────────────────────────────────
def get_setting(key, default=""):
    for r in _settings().get_all_records():
        if str(r.get("Key","")).strip() == key:
            return str(r.get("Value",""))
    return default

def set_setting(key, value):
    data = _settings().get_all_records()
    for i, r in enumerate(data):
        if str(r.get("Key","")).strip() == key:
            _settings().update_cell(i+2, 2, str(value))
            return
    _settings().append_row([key, str(value)])

def get_class_code():
    return get_setting("CLASS_CODE", "STENO2024")
