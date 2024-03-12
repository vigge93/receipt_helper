import os

from flask import Flask, redirect, render_template, url_for
from werkzeug.exceptions import HTTPException

from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
# from flask_cors import CORS

from receipt_helper.model.model import BaseModel

from werkzeug.security import generate_password_hash

db = SQLAlchemy(engine_options={"pool_pre_ping": True}, model_class=BaseModel)


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "123"),
        # SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite://"),
        SQLALCHEMY_DATABASE_URI="sqlite:///C:\\Users\\Victor\\Desktop\\receipt_helper\\kvitto.db", echo=True
    )

    app.config.from_pyfile("config.py", silent=True)

    os.makedirs(os.path.join(app.instance_path, "receipts"), exist_ok=True)

    db.init_app(app)

    from . import data

    # data.init_db(app, db)

    from . import auth

    app.register_blueprint(auth.bp)
    app.context_processor(auth.context_passer)

    from . import main

    app.register_blueprint(main.bp)
    app.add_url_rule("/", endpoint="index")
    
    from . import admin
    app.register_blueprint(admin.bp)

    app.register_error_handler(HTTPException, error_page)

    @app.route("/healthz")
    def healthz() -> dict[str, int]:
        return {"status": 1}
    csp = {
        "default-src": [
            "'self'",
            "*.icons8.com",
            "*.fontawesome.com",
            "'unsafe-inline'",
            "*.googleapis.com",
            "*.blob.core.windows.net",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
            "data:",
        ],
        "script-src": [
            "code.jquery.com",
            "'unsafe-inline'",
            "'self'",
            "cdn.jsdelivr.net",
            "unpkg.com",
            "cdnjs.cloudflare.com"
        ],
        "worker-src": ["'self'", "blob:"],
        "font-src": ["'self'", "*.fontawesome.com"],
    }
    Talisman(app, content_security_policy=csp)
    # CORS(app)
    return app


def error_page(e):
    return render_template("error_page.html", e=e), e.code
