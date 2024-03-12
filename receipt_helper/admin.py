from flask import Blueprint, render_template

from receipt_helper import db
from receipt_helper.auth import admin_required, login_required
from receipt_helper.model.user import User


bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
def index():
    return render_template('admin/index.html')

@bp.route("/list_users")
@login_required
@admin_required
def list_users():
    users = db.session.execute(db.select(User)).scalars().all()
    return render_template('admin/list_users.html', users=users)
    