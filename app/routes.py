"""
VU Query Management System — Routes
"""

from functools import wraps
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from werkzeug.security import check_password_hash, generate_password_hash
from .database import *
from .database import update_user_full, add_course, update_course, delete_course

bp = Blueprint('main', __name__)


# ─── Auth decorators ────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('main.login'))
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ─── Auth routes ────────────────────────────────────────────────────────────

@bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            if user['status'] != 'active':
                flash('Your account has been suspended.', 'danger')
                return render_template('login.html')
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    courses = get_all_courses()
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        role = request.form.get('role', 'student')
        selected_courses = request.form.getlist('courses')

        if role not in ('student', 'instructor'):
            role = 'student'
        errors = []
        if len(full_name) < 3:
            errors.append('Full name must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Valid email is required.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if get_user_by_email(email):
            errors.append('Email already registered.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', courses=courses)

        create_user(full_name, email, password, role)
        user = get_user_by_email(email)
        for cid in selected_courses:
            try:
                enroll_user(user['id'], int(cid))
            except Exception:
                pass
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', courses=courses)

@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.login'))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@bp.route('/dashboard')
@login_required
def dashboard():
    role = session['role']
    uid = session['user_id']
    if role == 'admin':
        return redirect(url_for('main.admin_dashboard'))
    elif role == 'instructor':
        return redirect(url_for('main.instructor_dashboard'))
    else:
        return redirect(url_for('main.student_dashboard'))


# ─── Student Dashboard ───────────────────────────────────────────────────────

@bp.route('/student')
@role_required('student')
def student_dashboard():
    uid = session['user_id']
    my_courses = get_user_courses(uid)
    my_queries = get_queries_for_student(uid)
    return render_template('student_dashboard.html',
                           courses=my_courses, queries=my_queries)

@bp.route('/student/courses', methods=['GET', 'POST'])
@role_required('student')
def student_courses():
    uid = session['user_id']
    all_courses = get_all_courses()
    my_courses = get_user_courses(uid)
    my_course_ids = [c['id'] for c in my_courses]
    if request.method == 'POST':
        selected = request.form.getlist('courses')
        # Unenroll from removed
        for c in my_courses:
            if str(c['id']) not in selected:
                unenroll_user(uid, c['id'])
        # Enroll in new
        for cid in selected:
            enroll_user(uid, int(cid))
        flash('Courses updated!', 'success')
        return redirect(url_for('main.student_courses'))
    return render_template('student_courses.html',
                           all_courses=all_courses, my_course_ids=my_course_ids)

@bp.route('/student/query/new', methods=['GET', 'POST'])
@role_required('student')
def new_query():
    uid = session['user_id']
    my_courses = get_user_courses(uid)
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        title = request.form.get('title', '').strip()
        body = request.form.get('body', '').strip()
        if not course_id or not title or not body:
            flash('All fields are required.', 'danger')
            return render_template('new_query.html', courses=my_courses)
        create_query(uid, int(course_id), title, body)
        flash('Query submitted successfully!', 'success')
        return redirect(url_for('main.student_dashboard'))
    return render_template('new_query.html', courses=my_courses)

@bp.route('/query/<int:qid>')
@login_required
def view_query(qid):
    query = get_query_by_id(qid)
    if not query:
        flash('Query not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    # Access control
    uid = session['user_id']
    role = session['role']
    if role == 'student' and query['student_id'] != uid:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    answers = get_answers_for_query(qid)
    my_courses = get_user_courses(uid) if role == 'instructor' else []
    return render_template('view_query.html', query=query, answers=answers,
                           my_courses=my_courses)

@bp.route('/query/<int:qid>/answer', methods=['POST'])
@role_required('instructor', 'admin')
def post_answer_route(qid):
    uid = session['user_id']
    body = request.form.get('answer', '').strip()
    if not body:
        flash('Answer cannot be empty.', 'danger')
        return redirect(url_for('main.view_query', qid=qid))
    post_answer(qid, uid, body)
    flash('Answer posted!', 'success')
    return redirect(url_for('main.view_query', qid=qid))

@bp.route('/query/<int:qid>/close', methods=['POST'])
@role_required('instructor', 'admin')
def close_query_route(qid):
    close_query(qid)
    flash('Query marked as closed.', 'info')
    return redirect(url_for('main.view_query', qid=qid))


# ─── Instructor Dashboard ─────────────────────────────────────────────────────

@bp.route('/instructor')
@role_required('instructor')
def instructor_dashboard():
    uid = session['user_id']
    my_courses = get_user_courses(uid)
    queries = get_queries_for_instructor(uid)
    return render_template('instructor_dashboard.html',
                           courses=my_courses, queries=queries)

@bp.route('/instructor/courses', methods=['GET', 'POST'])
@role_required('instructor')
def instructor_courses():
    uid = session['user_id']
    all_courses = get_all_courses()
    my_courses = get_user_courses(uid)
    my_course_ids = [c['id'] for c in my_courses]
    if request.method == 'POST':
        selected = request.form.getlist('courses')
        for c in my_courses:
            if str(c['id']) not in selected:
                unenroll_user(uid, c['id'])
        for cid in selected:
            enroll_user(uid, int(cid))
        flash('Courses updated!', 'success')
        return redirect(url_for('main.instructor_courses'))
    return render_template('instructor_courses.html',
                           all_courses=all_courses, my_course_ids=my_course_ids)


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@bp.route('/admin')
@role_required('admin')
def admin_dashboard():
    stats = get_stats()
    users = get_all_users()
    queries = get_all_queries()
    courses = get_all_courses()
    user_courses = {u['id']: get_user_courses(u['id']) for u in users}
    return render_template('admin_dashboard.html',
                           stats=stats, users=users, queries=queries,
                           courses=courses, user_courses=user_courses)

@bp.route('/admin/user/<int:uid>/toggle', methods=['POST'])
@role_required('admin')
def toggle_user(uid):
    user = get_user_by_id(uid)
    if user:
        new_status = 'blocked' if user['status'] == 'active' else 'active'
        update_user_status(uid, new_status)
        flash(f"User {'blocked' if new_status=='blocked' else 'unblocked'}.", 'info')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/user/<int:uid>/delete', methods=['POST'])
@role_required('admin')
def delete_user(uid):
    if uid == session['user_id']:
        flash('Cannot delete your own account.', 'danger')
    else:
        delete_user_by_id(uid)
        flash('User deleted.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/admin/user/add', methods=['POST'])
@role_required('admin')
def add_user():
    full_name = request.form.get('full_name', '').strip()
    email     = request.form.get('email', '').strip().lower()
    password  = request.form.get('password', '')
    role      = request.form.get('role', 'student')
    selected_courses = request.form.getlist('courses')

    errors = []
    if len(full_name) < 3:
        errors.append('Full name must be at least 3 characters.')
    if not email or '@' not in email:
        errors.append('Valid email is required.')
    if len(password) < 6:
        errors.append('Password must be at least 6 characters.')
    if role not in ('student', 'instructor', 'admin'):
        errors.append('Invalid role.')
    if get_user_by_email(email):
        errors.append('Email already registered.')

    if errors:
        for e in errors:
            flash(e, 'danger')
    else:
        create_user(full_name, email, password, role)
        new_user = get_user_by_email(email)
        for cid in selected_courses:
            try:
                enroll_user(new_user['id'], int(cid))
            except Exception:
                pass
        flash(f'User "{full_name}" created successfully.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/user/<int:uid>/edit', methods=['POST'])
@role_required('admin')
def edit_user(uid):
    user = get_user_by_id(uid)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    full_name = request.form.get('full_name', '').strip()
    email     = request.form.get('email', '').strip().lower()
    role      = request.form.get('role', user['role'])
    status    = request.form.get('status', user['status'])
    new_pw    = request.form.get('new_password', '').strip()
    selected_courses = request.form.getlist('courses')

    errors = []
    if len(full_name) < 3:
        errors.append('Full name must be at least 3 characters.')
    if not email or '@' not in email:
        errors.append('Valid email is required.')
    existing = get_user_by_email(email)
    if existing and existing['id'] != uid:
        errors.append('Email already used by another account.')
    if new_pw and len(new_pw) < 6:
        errors.append('New password must be at least 6 characters.')

    if errors:
        for e in errors:
            flash(e, 'danger')
    else:
        update_user_full(uid, full_name, email, role, status, new_pw if new_pw else None)
        all_courses = get_all_courses()
        for c in all_courses:
            if str(c['id']) in selected_courses:
                enroll_user(uid, c['id'])
            else:
                unenroll_user(uid, c['id'])
        flash(f'User "{full_name}" updated successfully.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@bp.route('/admin/queries')
@role_required('admin')
def admin_queries():
    queries = get_all_queries()
    return render_template('admin_queries.html', queries=queries)

# ─── Admin Course Management ──────────────────────────────────────────────────

@bp.route('/admin/course/add', methods=['POST'])
@role_required('admin')
def add_course_route():
    code  = request.form.get('code', '').strip().upper()
    title = request.form.get('title', '').strip()
    if not code or not title:
        flash('Course code and title are required.', 'danger')
    elif len(code) > 10:
        flash('Course code must be 10 characters or fewer.', 'danger')
    else:
        try:
            add_course(code, title)
            flash(f'Course "{code} — {title}" added successfully.', 'success')
        except Exception as e:
            flash(f'Error: Course code "{code}" may already exist.', 'danger')
    return redirect(url_for('main.admin_dashboard') + '#tab-courses')

@bp.route('/admin/course/<int:cid>/edit', methods=['POST'])
@role_required('admin')
def edit_course_route(cid):
    code  = request.form.get('code', '').strip().upper()
    title = request.form.get('title', '').strip()
    if not code or not title:
        flash('Course code and title are required.', 'danger')
    else:
        try:
            update_course(cid, code, title)
            flash(f'Course updated successfully.', 'success')
        except Exception:
            flash('Error updating course. Code may already be in use.', 'danger')
    return redirect(url_for('main.admin_dashboard') + '#tab-courses')

@bp.route('/admin/course/<int:cid>/delete', methods=['POST'])
@role_required('admin')
def delete_course_route(cid):
    try:
        delete_course(cid)
        flash('Course deleted successfully.', 'success')
    except Exception:
        flash('Cannot delete course — it may have active queries.', 'danger')
    return redirect(url_for('main.admin_dashboard') + '#tab-courses')


# API endpoint for query details (AJAX)
@bp.route('/api/query/<int:qid>')
@login_required
def api_query(qid):
    query = get_query_by_id(qid)
    if not query:
        return jsonify({'error': 'Not found'}), 404
    answers = get_answers_for_query(qid)
    return jsonify({
        'id': query['id'],
        'title': query['title'],
        'body': query['body'],
        'course': f"{query['code']} - {query['course_title']}",
        'student': query['student_name'],
        'status': query['status'],
        'created_at': query['created_at'],
        'answers': [{'body': a['body'], 'instructor': a['instructor_name'],
                     'created_at': a['created_at']} for a in answers]
    })
