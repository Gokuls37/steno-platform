import sqlite3, os
from flask import g

DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "steno.db")

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db

def init_db():
    from flask import current_app
    with current_app.app_context():
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.executescript("""
            CREATE TABLE IF NOT EXISTS batches (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS students (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                mobile        TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                batch_id      INTEGER NOT NULL REFERENCES batches(id),
                status        TEXT NOT NULL DEFAULT 'pending',
                created_at    TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS passages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                category   TEXT NOT NULL DEFAULT 'General',
                batch_id   INTEGER NOT NULL REFERENCES batches(id),
                audio_url  TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS results (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id   INTEGER NOT NULL REFERENCES students(id),
                passage_id   INTEGER NOT NULL REFERENCES passages(id),
                typed_text   TEXT,
                full_errors  INTEGER DEFAULT 0,
                half_errors  INTEGER DEFAULT 0,
                omit_errors  INTEGER DEFAULT 0,
                extra_errors INTEGER DEFAULT 0,
                error_pct    REAL DEFAULT 0,
                wpm          INTEGER DEFAULT 0,
                verdict      TEXT DEFAULT 'FAIL',
                override_by  TEXT DEFAULT NULL,
                submitted_at TEXT DEFAULT (datetime('now'))
            );

            -- Seed a default batch so registration works immediately
            INSERT OR IGNORE INTO batches (name, code) VALUES ('Default Batch', 'DT2024');
        """)
        db.commit()
        db.close()
