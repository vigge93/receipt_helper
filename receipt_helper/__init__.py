import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from werkzeug.exceptions import HTTPException

from receipt_helper.model.model import BaseModel

# from flask_cors import CORS


db = SQLAlchemy(engine_options={"pool_pre_ping": True}, model_class=BaseModel)


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI"),
        RECEIPTS_STORAGE_PATH=os.getenv(
            "RECEIPTS_STORAGE_PATH", os.path.join(app.instance_path, "receipts")
        ),
        RECEIPTS_EMAIL_RECEIPT_RECIPIENT=os.getenv("RECEIPTS_EMAIL_RECEIPT_RECIPIENT"),
        RECEIPTS_EMAIL_SENDER=os.getenv("RECEIPTS_EMAIL_SENDER"),
        RECEIPTS_SMTP_HOST=os.getenv("RECEIPTS_SMTP_HOST"),
        RECEIPTS_SMTP_USERNAME=os.getenv("RECEIPTS_SMTP_USERNAME"),
        RECEIPTS_SMTP_PASSWORD=os.getenv("RECEIPTS_SMTP_PASSWORD"),
        RECEIPTS_ADMIN_USER_EMAIL=os.getenv("RECEIPTS_ADMIN_USER_EMAIL"),
        RECEIPTS_ADMIN_USER_NAME=os.getenv("RECEIPTS_ADMIN_USER_NAME"),
        RECEIPTS_ADMIN_USER_PASSWORD=os.getenv("RECEIPTS_ADMIN_USER_PASSWORD")
    )

    app.config.from_pyfile("config.py", silent=True)

    os.makedirs(app.config["RECEIPTS_STORAGE_PATH"], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    
    from . import data
    data.init_db(app, db)

    from . import auth

    app.register_blueprint(auth.bp)
    app.context_processor(auth.context_passer)

    from . import main

    app.register_blueprint(main.bp)
    app.add_url_rule("/", endpoint="index")

    from . import admin

    app.register_blueprint(admin.bp)

    from . import cfo

    app.register_blueprint(cfo.bp)

    app.register_error_handler(HTTPException, error_page)

    @app.route("/healthz")
    def healthz() -> dict[str, int]:
        return {"status": 1}

    # csp = {
    #     "default-src": [
    #         "'self'",
    #         "*.icons8.com",
    #         "*.fontawesome.com",
    #         "'unsafe-inline'",
    #         "*.googleapis.com",
    #         "*.blob.core.windows.net",
    #         "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css",
    #         "data:",
    #     ],
    #     "script-src": [
    #         "code.jquery.com",
    #         "'unsafe-inline'",
    #         "'self'",
    #         "cdn.jsdelivr.net",
    #         "unpkg.com",
    #         "cdnjs.cloudflare.com",
    #     ],
    #     "worker-src": ["'self'", "blob:"],
    #     "font-src": ["'self'", "*.fontawesome.com"],
    # }
    # Talisman(app, content_security_policy=csp)
    # CORS(app)
    return app


def error_page(e):
    return render_template("error_page.html", e=e), e.code
