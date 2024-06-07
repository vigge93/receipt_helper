import logging
import os

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException
from flask_sqlalchemy import SQLAlchemy

from receipt_helper.model.model import BaseModel

from logging.config import dictConfig
from logging.handlers import SMTPHandler


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

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

    if not app.config["TESTING"]:  # pragma: no cover
        mail_handler = SMTPHandler(
            mailhost=app.config["RECEIPTS_SMTP_HOST"],
            fromaddr=app.config["RECEIPTS_EMAIL_SENDER"],
            toaddrs=app.config["RECEIPTS_ADMIN_USER_EMAIL"],
            subject='Receipt helper: Application Error',
            credentials=(app.config["RECEIPTS_SMTP_USERNAME"], app.config["RECEIPTS_SMTP_PASSWORD"])
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))

        app.logger.addHandler(mail_handler)
        app.logger.setLevel(int(os.getenv("LOGGING_LEVEL", logging.INFO)))


        app.logger.info(f"Web app started!\t{__name__}")
    return app


def error_page(e):
    return render_template("error_page.html", e=e), e.code
