from datetime import datetime
from enum import IntEnum, unique
import functools

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from receipt_helper.enums import ClearanceEnum
from receipt_helper.forms.auth_forms import ChangePasswordForm, LoginForm

from receipt_helper import db
from werkzeug.security import check_password_hash, generate_password_hash

from receipt_helper.model.user import User

bp = Blueprint("auth", __name__, url_prefix="/auth")

def context_passer():
    return dict(ClearanceEnum=ClearanceEnum)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user.needs_password_change:
            return redirect(url_for("auth.change_password"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if (g.user.userTypeId & ClearanceEnum.Admin) != 0:
            return view(**kwargs)

        return logout()

    return wrapped_view

def cfo_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if (g.user.userTypeId & ClearanceEnum.CFO) != 0:
            return view(**kwargs)

        return logout()

    return wrapped_view

@bp.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()
    if request.method != "POST" or not form.validate_on_submit():
        if g.user is not None:
            return redirect(url_for("index"))
        return render_template("auth/login.html", form=form)
    email = form.email.data
    password = form.password.data
    error = None
    user: User | None = (
        db.session.execute(db.select(User).filter_by(email=email)).scalars().first()
    )

    if user is None or not check_password_hash(user.password, password):
        error = "Felaktigt användarnamn eller lösenord."

    if error is not None:
        flash(error)
        if g.user is not None:
            return redirect(url_for("index"))
        return render_template("auth/login.html", form=form)

    session.clear()
    session["user_id"] = user.id
    user.lastLogin = datetime.utcnow()
    db.session.commit()
    session.permanent = True
    return redirect(url_for("index"))


@bp.route("/change_password", methods=("GET", "POST"))
def change_password():
    form = ChangePasswordForm()
    if request.method != "POST" or not form.validate_on_submit():
        return render_template("auth/new_password.html", form=form)
    old_password = form.old_password.data
    new_password = form.new_password.data
    
    error = None
    user = db.session.get(User, g.user.id)
    
    if not check_password_hash(user.password, old_password):
        error = "Felaktigt lösenord."
    
    if error is not None:
        flash(error)
        return render_template("auth/new_password.html", form=form)

    user.password = generate_password_hash(new_password)
    user.needs_password_change = False
    db.session.commit()
    return redirect(url_for('index'))

@bp.route("/logout")
def logout():
    session.clear()
    g.user = None
    return redirect(url_for("auth.login"))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)
        if g.user is None:
            return
