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
from werkzeug.security import check_password_hash, generate_password_hash

from receipt_helper.database import (
    get_user,
    get_user_by_email,
    update_user_last_login,
    update_user_password,
)
from receipt_helper.enums import ClearanceEnum, ReceiptStatusEnum
from receipt_helper.forms.auth_forms import ChangePasswordForm, LoginForm
from receipt_helper.model.user import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


def context_passer():
    return dict(ClearanceEnum=ClearanceEnum, ReceiptStatusEnum=ReceiptStatusEnum)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user.needs_password_change and request.path != url_for(
            "auth.change_password"
        ):
            return redirect(url_for("auth.change_password"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user and (g.user.userTypeId & ClearanceEnum.Admin) != 0:
            return view(**kwargs)

        return logout()

    return wrapped_view


def cfo_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user and (g.user.userTypeId & ClearanceEnum.CFO) != 0:
            return view(**kwargs)

        return logout()

    return wrapped_view


@bp.route("/login", methods=("GET", "POST"))
def login():
    form: LoginForm = LoginForm()
    if request.method != "POST" or not form.validate_on_submit():
        if g.user is not None:
            return redirect(url_for("index"))
        return render_template("auth/login.html", form=form)
    email = form.email.data.lower()  # type: ignore
    password = form.password.data
    error = None
    user: User | None = get_user_by_email(email)

    if user is None or not check_password_hash(user.password, password):  # type: ignore
        error = "Felaktigt användarnamn eller lösenord."

    if error is not None:
        flash(error)
        if g.user is not None:
            return redirect(url_for("index"))
        return render_template("auth/login.html", form=form)

    session.clear()
    session["user_id"] = user.id  # type: ignore
    update_user_last_login(user.id)  # type: ignore
    session.permanent = True
    return redirect(url_for("index"))


@bp.route("/change_password", methods=("GET", "POST"))
@login_required
def change_password():
    form = ChangePasswordForm()
    if request.method != "POST" or not form.validate_on_submit():
        return render_template("auth/new_password.html", form=form)
    old_password = form.old_password.data
    new_password = form.new_password.data

    error = None
    user = get_user(g.user.id)

    if not user or not check_password_hash(user.password, old_password):
        error = "Felaktigt lösenord."

    if error is not None:
        flash(error)
        return render_template("auth/new_password.html", form=form)

    if not update_user_password(g.user.id, generate_password_hash(new_password)):
        abort(404, "Användare hittades ej.")
    return redirect(url_for("index"))


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
        g.user = get_user(user_id)
        if g.user is None:
            return
