from flask import Flask, session, redirect, url_for
from .database import close_db, init_db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = 'vu-query-system-secret-2025'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    app.teardown_appcontext(close_db)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        init_db()

    return app
