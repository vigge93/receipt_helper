import csv
import os
import smtplib
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.datastructures import MultiDict
from werkzeug.security import generate_password_hash

from receipt_helper import database
from receipt_helper.auth import admin_required, login_required
from receipt_helper.database import add_user_role, get_user, get_users, remove_user_role, reset_user_password
from receipt_helper.enums import ClearanceEnum
from receipt_helper.forms.user_forms import AddManyUsersForm, AddSingleUserForm
from receipt_helper.model.receipt import Receipt
from receipt_helper.model.user import User
from receipt_helper.util import send_email

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@login_required
@admin_required
def index():
    return render_template("admin/index.html")


@bp.route("/list_users")
@login_required
@admin_required
def list_users():
    users = get_users()
    return render_template("admin/list_users.html", users=users)


@bp.route("/add_single_user", methods=("GET", "POST"))
@login_required
@admin_required
def add_single_user():
    form = AddSingleUserForm()
    if request.method != "POST" or not form.validate_on_submit():
        return render_template("admin/add_single_user.html", form=form)

    name = form.name.data
    email = form.email.data

    add_user(name, email)

    return redirect(url_for("admin.index"))


def add_user(name: str, email: str) -> bool:
    temp_password = str(uuid4())

    user = User(
        email=email.lower(),
        name=name,
        password=generate_password_hash(temp_password),
        userTypeId=ClearanceEnum.User.value,
    ) # type: ignore

    if not database.add_user(user):
        flash(f"Fel vid skapandet av konto för {name}!")
        return False

    try:
        send_email(
            email,
            "Konto för kvittoredovisning skapat!",
            f"""Hej

Det har skapats ett konto åt dig för att kunna hantera kvittoredovisningar. Inloggningsuppgifter står nedan.

Länk: {url_for('main.index', _external=True)}
Användarnamn: {email}
Lösenord: {temp_password}

Ovanstående lösenord är temporärt och vid första inloggning kommer du behöva byta ditt lösenord.
""",
        )
    except smtplib.SMTPException:
        flash(f"Fel vid skickande av email till {name}, nollställ användarens lösenord för att skicka ett nytt mejl.")
        return False
    return True

@bp.route("/add_many_users", methods=("GET", "POST"))
@login_required
@admin_required
def add_many_users():
    form = AddManyUsersForm()
    if request.method != "POST" or not form.validate_on_submit():
        return render_template("admin/add_many_users.html", form=form)

    file = form.file.data
    filepath = os.path.join(current_app.instance_path, "import.csv")
    file.save(filepath)
    with open(filepath) as fd:
        reader = csv.DictReader(fd, fieldnames=["name", "email"])

        added_users = 0
        for row in reader:
            m_dict_row = MultiDict(row)
            user_form = AddSingleUserForm(m_dict_row, meta={"csrf": False})
            if not user_form.validate():
                for error in user_form.errors:
                    flash(f"Felaktig data för användare {row}: {error}")
                continue
            name = user_form.name.data
            email = user_form.email.data
            if add_user(name, email):
                added_users += 1
    flash(f"Lade till {added_users} användare!")
    return redirect(url_for("admin.index"))

@bp.route("/<int:id>/reset_password")
@login_required
@admin_required
def reset_password(id: int):
    validate_user_id(id)
    user = get_user(id)

    temp_password = str(uuid4())

    if not user or not reset_user_password(id, generate_password_hash(temp_password)):
        flash("Användare hittades inte!")
        return redirect(url_for('admin.list_users'))
    
    email = user.email

    try:
        send_email(
            email,
        "Lösenord för kvittoredovisning nollställt!",
        f"""Hej
            
Ditt lösenord för kvittoredovisningar har nollställts. Ditt temporära lösenord anges nedan.

Lösenord: {temp_password}
Länk: {url_for('main.index', _external=True)}

Ovanstående lösenord är temporärt och vid första inloggning kommer du behöva byta ditt lösenord.
""")
        flash(f"Lösenord nollställt för {user.name}")
    except smtplib.SMTPException:
        flash(f"Fel vid skickande av email till {user.name}, nollställ användarens lösenord för att skicka ett nytt mejl, eller kontakta en administratör.")
        return redirect(url_for("admin.list_users"))
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/make_admin")
@login_required
@admin_required
def make_admin(id: int):
    validate_user_id(id)
    if not add_user_role(id, ClearanceEnum.Admin):
        flash("Användare hittades inte!")
        return redirect(url_for('admin.list_users'))
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/make_cfo")
@login_required
@admin_required
def make_cfo(id: int):
    validate_user_id(id)
    if not add_user_role(id, ClearanceEnum.CFO):
        flash("Användare hittades inte!")
        return redirect(url_for('admin.list_users'))
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/remove_admin")
@login_required
@admin_required
def remove_admin(id: int):
    validate_user_id(id)
    if id == g.user.id:
        flash("Du kan inte plocka bort admin från dig själv!")
        return redirect(url_for("admin.list_users"))
    if not remove_user_role(id, ClearanceEnum.Admin):
        flash("Användare hittades inte!")
        return redirect(url_for('admin.list_users'))
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/remove_cfo")
@login_required
@admin_required
def remove_cfo(id: int):
    validate_user_id(id)
    if not remove_user_role(id, ClearanceEnum.CFO):
        flash("Användare hittades inte!")
        return redirect(url_for('admin.list_users'))
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/delete_user")
@login_required
@admin_required
def delete_user(id: int):
    validate_user_id(id)
    if id == g.user.id:
        flash("Du kan inte radera dig själv!")
        return redirect(url_for("admin.list_users"))

    if not database.delete_user(id):
        flash("Användare hittades inte!")
        return redirect(url_for('admin.list_users'))
    return redirect(url_for("admin.list_users"))

def validate_user_id(id: int):
    is_protected_user = id < 1
    if is_protected_user:
        return abort(403)
