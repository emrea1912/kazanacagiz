import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        session_token TEXT,
        role TEXT DEFAULT 'user',
        is_premium BOOLEAN DEFAULT 0,
        premium_until TEXT,
        selected_exam_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migration safe column checks
    cursor.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in cursor.fetchall()]
    if "session_token" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN session_token TEXT")
    if "premium_until" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN premium_until TEXT")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS license_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_code TEXT UNIQUE NOT NULL,
        is_used BOOLEAN DEFAULT 0,
        used_by_user_id INTEGER,
        duration_days INTEGER DEFAULT 30,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (used_by_user_id) REFERENCES users (id)
    );
    """)

    # Exams Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        is_approved BOOLEAN DEFAULT 1,
        created_by_user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        subject TEXT DEFAULT 'Genel',
        topic TEXT DEFAULT 'Genel',
        image_url TEXT NOT NULL,
        digital_question_text TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        option_e TEXT,
        correct_answer TEXT NOT NULL,
        next_review_date TEXT NOT NULL,
        consecutive_correct INTEGER DEFAULT 0,
        total_reviews INTEGER DEFAULT 0,
        mastered BOOLEAN DEFAULT 0,
        is_public_pool BOOLEAN DEFAULT 1,
        source_type TEXT DEFAULT 'user_upload',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (exam_id) REFERENCES exams (id)
    );
    """)

    # Review Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS review_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        given_answer TEXT NOT NULL,
        is_correct BOOLEAN NOT NULL,
        reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # Reminders Log (10:00 & 15:00)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reminder_type TEXT NOT NULL,
        reminder_date TEXT NOT NULL,
        status TEXT DEFAULT 'sent',
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # Pre-seed Standard ÖSYM Exams
    default_exams = [
        ("YKS (TYT - AYT)", "YKS"),
        ("KPSS (Lisans)", "KPSS_LISANS"),
        ("KPSS (Ön Lisans)", "KPSS_ONLISANS"),
        ("KPSS (Ortaöğretim)", "KPSS_ORTA"),
        ("AGS (Akademi Giriş Sınavı)", "AGS"),
        ("ALES", "ALES"),
        ("DGS", "DGS"),
        ("MSÜ", "MSU"),
        ("YDS / YÖKDİL", "YDS"),
        ("LGS", "LGS")
    ]

    for name, code in default_exams:
        cursor.execute("""
        INSERT OR IGNORE INTO exams (name, code, is_approved, created_by_user_id)
        VALUES (?, ?, 1, NULL)
        """, (name, code))

    # Pre-seed Demo Admin & Standard User
    # Demo admin: admin / admin123
    # Demo user: ogrenci / ogrenci123
    cursor.execute("""
    INSERT OR IGNORE INTO users (id, username, password_hash, role, is_premium, selected_exam_id)
    VALUES (1, 'admin', 'admin123', 'admin', 1, 1)
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO users (id, username, password_hash, role, is_premium, selected_exam_id)
    VALUES (2, 'ogrenci', 'ogrenci123', 'user', 0, 1)
    """)

    # Pre-seed sample License Keys
    default_keys = [
        ("KAZAN-PRO-2026", 30),
        ("DERECE-VIP-30", 30),
        ("OGRENCI-HEDIYE-60", 60),
        ("YILLIK-SAMPIYON-365", 365)
    ]
    for key, days in default_keys:
        cursor.execute("""
        INSERT OR IGNORE INTO license_keys (key_code, is_used, duration_days)
        VALUES (?, 0, ?)
        """, (key, days))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
