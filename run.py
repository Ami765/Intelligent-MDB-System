"""
VU Query Management System — Server Entry Point
Run: python run.py
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  VU Query Management System")
    print("  CS619 Final Project")
    print("="*60)
    print("  URL        : http://127.0.0.1:5000")
    print()
    print("  Demo Accounts:")
    print("  Admin      : admin@vu.edu.pk       / Admin@123")
    print("  Instructor : instructor@vu.edu.pk  / Inst@123")
    print("  Student    : student@vu.edu.pk     / Stud@123")
    print()
    print("  Courses available:")
    print("  CS101 · CS304 · CS403 · PHY101 · CS601 · MGT301 · MTH202")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
