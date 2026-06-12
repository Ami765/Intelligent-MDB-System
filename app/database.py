"""
VU Query Management System — Database Module
MySQL-compatible schema, using SQLite for portability.
Replace get_db() with mysql.connector for production MySQL.
"""

import sqlite3
import os
from flask import g, current_app
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'vuquery.db')

COURSES = [
    ('CS101', 'Introduction to Computing'),
    ('CS304', 'Object Oriented Programming'),
    ('CS403', 'Database Management Systems'),
    ('PHY101', 'Physics'),
    ('CS601', 'Data Communication'),
    ('MGT301', 'Principles of Marketing'),
    ('MTH202', 'Discrete Mathematics'),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password    TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student','instructor','admin')),
    status      TEXT NOT NULL DEFAULT 'active',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    title       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    course_id   INTEGER NOT NULL,
    enrolled_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, course_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(course_id) REFERENCES courses(id)
);

CREATE TABLE IF NOT EXISTS queries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   INTEGER NOT NULL,
    course_id    INTEGER NOT NULL,
    title        TEXT NOT NULL,
    body         TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','answered','closed')),
    created_at   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(student_id) REFERENCES users(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
);

CREATE TABLE IF NOT EXISTS answers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id     INTEGER NOT NULL,
    instructor_id INTEGER NOT NULL,
    body         TEXT NOT NULL,
    created_at   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(query_id) REFERENCES queries(id) ON DELETE CASCADE,
    FOREIGN KEY(instructor_id) REFERENCES users(id)
);
"""


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    db.commit()

    # Seed courses
    for code, title in COURSES:
        db.execute("INSERT OR IGNORE INTO courses (code, title) VALUES (?,?)", (code, title))

    # Seed admin
    row = db.execute("SELECT id FROM users WHERE role='admin'").fetchone()
    if not row:
        db.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (?,?,?,?)",
            ('Administrator', 'admin@vu.edu.pk', generate_password_hash('Admin@123'), 'admin')
        )
        # Seed demo instructor
        db.execute(
            "INSERT OR IGNORE INTO users (full_name, email, password, role) VALUES (?,?,?,?)",
            ('Dr. Ahmed Khan', 'instructor@vu.edu.pk', generate_password_hash('Inst@123'), 'instructor')
        )
        # Seed demo student
        db.execute(
            "INSERT OR IGNORE INTO users (full_name, email, password, role) VALUES (?,?,?,?)",
            ('Ali Hassan', 'student@vu.edu.pk', generate_password_hash('Stud@123'), 'student')
        )
    db.commit()

    # Enroll demo users in courses
    db.row_factory = sqlite3.Row
    student = db.execute("SELECT id FROM users WHERE email='student@vu.edu.pk'").fetchone()
    inst    = db.execute("SELECT id FROM users WHERE email='instructor@vu.edu.pk'").fetchone()
    if student:
        for code in ('CS101', 'CS304', 'CS403', 'PHY101'):
            course = db.execute("SELECT id FROM courses WHERE code=?", (code,)).fetchone()
            if course:
                db.execute("INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?,?)",
                           (student['id'], course['id']))
    if inst:
        for code in ('CS101', 'CS304', 'CS403', 'CS601', 'MTH202'):
            course = db.execute("SELECT id FROM courses WHERE code=?", (code,)).fetchone()
            if course:
                db.execute("INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?,?)",
                           (inst['id'], course['id']))
    db.commit()

    db.close()


# ─── User helpers ───────────────────────────────────────────────────────────

def get_user_by_email(email):
    return get_db().execute("SELECT * FROM users WHERE email=? COLLATE NOCASE", (email,)).fetchone()

def get_user_by_id(uid):
    return get_db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def create_user(full_name, email, password, role):
    db = get_db()
    db.execute("INSERT INTO users (full_name, email, password, role) VALUES (?,?,?,?)",
               (full_name, email.lower(), generate_password_hash(password), role))
    db.commit()

def get_all_users():
    return get_db().execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()

def update_user_status(uid, status):
    db = get_db()
    db.execute("UPDATE users SET status=? WHERE id=?", (status, uid))
    db.commit()

def delete_user_by_id(uid):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    db.commit()


# ─── Course helpers ─────────────────────────────────────────────────────────

def get_all_courses():
    return get_db().execute("SELECT * FROM courses ORDER BY code").fetchall()

def get_course_by_id(cid):
    return get_db().execute("SELECT * FROM courses WHERE id=?", (cid,)).fetchone()

def get_user_courses(uid):
    return get_db().execute("""
        SELECT c.* FROM courses c
        JOIN enrollments e ON e.course_id = c.id
        WHERE e.user_id = ? ORDER BY c.code
    """, (uid,)).fetchall()

def enroll_user(uid, course_id):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?,?)", (uid, course_id))
    db.commit()

def unenroll_user(uid, course_id):
    db = get_db()
    db.execute("DELETE FROM enrollments WHERE user_id=? AND course_id=?", (uid, course_id))
    db.commit()


# ─── Query helpers ─────────────────────────────────────────────────────────

def create_query(student_id, course_id, title, body):
    db = get_db()
    db.execute("INSERT INTO queries (student_id, course_id, title, body) VALUES (?,?,?,?)",
               (student_id, course_id, title, body))
    db.commit()

def get_queries_for_student(student_id):
    return get_db().execute("""
        SELECT q.*, c.code, c.title as course_title,
               u.full_name as student_name,
               (SELECT COUNT(*) FROM answers a WHERE a.query_id=q.id) as answer_count
        FROM queries q
        JOIN courses c ON c.id = q.course_id
        JOIN users u ON u.id = q.student_id
        WHERE q.student_id = ?
        ORDER BY q.created_at DESC
    """, (student_id,)).fetchall()

def get_queries_for_instructor(instructor_id):
    """Return queries for courses the instructor is enrolled in."""
    return get_db().execute("""
        SELECT q.*, c.code, c.title as course_title,
               u.full_name as student_name,
               (SELECT COUNT(*) FROM answers a WHERE a.query_id=q.id) as answer_count
        FROM queries q
        JOIN courses c ON c.id = q.course_id
        JOIN users u ON u.id = q.student_id
        WHERE c.id IN (
            SELECT course_id FROM enrollments WHERE user_id=?
        )
        ORDER BY q.status ASC, q.created_at DESC
    """, (instructor_id,)).fetchall()

def get_all_queries():
    return get_db().execute("""
        SELECT q.*, c.code, c.title as course_title,
               u.full_name as student_name,
               (SELECT COUNT(*) FROM answers a WHERE a.query_id=q.id) as answer_count
        FROM queries q
        JOIN courses c ON c.id = q.course_id
        JOIN users u ON u.id = q.student_id
        ORDER BY q.created_at DESC
    """).fetchall()

def get_query_by_id(qid):
    return get_db().execute("""
        SELECT q.*, c.code, c.title as course_title, u.full_name as student_name
        FROM queries q
        JOIN courses c ON c.id = q.course_id
        JOIN users u ON u.id = q.student_id
        WHERE q.id=?
    """, (qid,)).fetchone()

def get_answers_for_query(qid):
    return get_db().execute("""
        SELECT a.*, u.full_name as instructor_name
        FROM answers a
        JOIN users u ON u.id = a.instructor_id
        WHERE a.query_id=?
        ORDER BY a.created_at ASC
    """, (qid,)).fetchall()

def post_answer(query_id, instructor_id, body):
    db = get_db()
    db.execute("INSERT INTO answers (query_id, instructor_id, body) VALUES (?,?,?)",
               (query_id, instructor_id, body))
    db.execute("UPDATE queries SET status='answered' WHERE id=?", (query_id,))
    db.commit()

def close_query(qid):
    db = get_db()
    db.execute("UPDATE queries SET status='closed' WHERE id=?", (qid,))
    db.commit()

def get_stats():
    db = get_db()
    return {
        'students': db.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
        'instructors': db.execute("SELECT COUNT(*) FROM users WHERE role='instructor'").fetchone()[0],
        'open_queries': db.execute("SELECT COUNT(*) FROM queries WHERE status='open'").fetchone()[0],
        'answered_queries': db.execute("SELECT COUNT(*) FROM queries WHERE status='answered'").fetchone()[0],
        'total_queries': db.execute("SELECT COUNT(*) FROM queries").fetchone()[0],
        'courses': db.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
    }


def update_user_full(uid, full_name, email, role, status, new_password=None):
    from werkzeug.security import generate_password_hash
    db = get_db()
    if new_password:
        db.execute(
            "UPDATE users SET full_name=?, email=?, role=?, status=?, password=? WHERE id=?",
            (full_name, email.lower(), role, status, generate_password_hash(new_password), uid)
        )
    else:
        db.execute(
            "UPDATE users SET full_name=?, email=?, role=?, status=? WHERE id=?",
            (full_name, email.lower(), role, status, uid)
        )
    db.commit()


def add_course(code, title):
    db = get_db()
    db.execute("INSERT INTO courses (code, title) VALUES (?, ?)", (code.strip().upper(), title.strip()))
    db.commit()

def update_course(cid, code, title):
    db = get_db()
    db.execute("UPDATE courses SET code=?, title=? WHERE id=?", (code.strip().upper(), title.strip(), cid))
    db.commit()

def delete_course(cid):
    db = get_db()
    db.execute("DELETE FROM courses WHERE id=?", (cid,))
    db.commit()

def get_course_by_id_admin(cid):
    return get_db().execute("SELECT * FROM courses WHERE id=?", (cid,)).fetchone()
