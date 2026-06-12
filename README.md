# VU Query Management System
**CS619 Final Project — Full Stack Web Application**

A complete student–instructor query management platform built with Python (Flask) + SQLite/MySQL + modern HTML/CSS/JS.

---

## Features

### Student
- Register and select enrolled courses (from 7 VU courses)
- Submit queries for enrolled courses
- View own queries with expandable answers inline
- Filter queries by status (open / answered / closed)

### Instructor
- Register and select courses they teach
- See all student queries for their courses
- Answer queries directly from dashboard (inline or full view)
- Close resolved queries

### Admin
- Full system overview: users, queries, courses
- Block / unblock users
- Delete users
- View all queries across all courses

---

## Courses Available
| Code   | Title                          |
|--------|-------------------------------|
| CS101  | Introduction to Computing     |
| CS304  | Object Oriented Programming   |
| CS403  | Database Management Systems   |
| PHY101 | Physics                       |
| CS601  | Data Communication            |
| MGT301 | Principles of Marketing       |
| MTH202 | Discrete Mathematics          |

---

## Quick Start (SQLite — zero config)

```bash
pip install flask werkzeug
python run.py
```
Open: http://127.0.0.1:5000

### Demo Accounts
| Role       | Email                    | Password   |
|------------|--------------------------|------------|
| Admin      | admin@vu.edu.pk          | Admin@123  |
| Instructor | instructor@vu.edu.pk     | Inst@123   |
| Student    | student@vu.edu.pk        | Stud@123   |

---

## Switch to MySQL (Production)

1. Install MySQL driver:
   ```bash
   pip install mysql-connector-python
   ```

2. In `app/database.py`, replace `get_db()` with:
   ```python
   import mysql.connector

   def get_db():
       if 'db' not in g:
           g.db = mysql.connector.connect(
               host='localhost',
               user='your_user',
               password='your_password',
               database='vuquery'
           )
       return g.db
   ```

3. Create the MySQL database:
   ```sql
   CREATE DATABASE vuquery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

4. The SCHEMA_SQL in `database.py` is MySQL-compatible (replace `INTEGER PRIMARY KEY AUTOINCREMENT` with `INT AUTO_INCREMENT PRIMARY KEY` and `datetime('now')` with `NOW()`).

---

## Project Structure
```
vuquery/
├── run.py                    # Entry point
├── requirements.txt
├── instance/
│   └── vuquery.db            # SQLite database (auto-created)
└── app/
    ├── __init__.py           # Flask app factory
    ├── database.py           # DB schema + all queries
    ├── routes.py             # All routes (auth, student, instructor, admin)
    ├── templates/
    │   ├── base.html
    │   ├── login.html
    │   ├── register.html
    │   ├── student_dashboard.html
    │   ├── student_courses.html
    │   ├── new_query.html
    │   ├── view_query.html
    │   ├── instructor_dashboard.html
    │   ├── instructor_courses.html
    │   └── admin_dashboard.html
    └── static/
        ├── css/main.css
        └── js/main.js
```
