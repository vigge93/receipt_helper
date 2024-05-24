import csv
import os
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

from receipt_helper import db
from receipt_helper.auth import admin_required, login_required
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
    users = db.session.execute(db.select(User).where(User.id > 0)).scalars().all()
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

    db.session.commit()

    return redirect(url_for("admin.index"))


def add_user(name: str, email: str):
    temp_password = str(uuid4())

    user = User(
        email=email.lower(),
        name=name,
        password=generate_password_hash(temp_password),
        userTypeId=ClearanceEnum.User.value,
    )

    db.session.add(user)

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
            add_user(name, email)
            added_users += 1
    if added_users > 0:
        db.session.commit()
    flash(f"Lade till {added_users} användare!")
    return redirect(url_for("admin.index"))

@bp.route("/<int:id>/reset_password")
@login_required
@admin_required
def reset_password(id: int):
    validate_user_id(id)
    user = db.session.get(User, id)
    email = user.email

    temp_password = str(uuid4())

    user.password = generate_password_hash(temp_password)
    user.needs_password_change = True
    db.session.commit()

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
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/make_admin")
@login_required
@admin_required
def make_admin(id: int):
    validate_user_id(id)
    user = db.session.get(User, id)
    user.userTypeId = user.userTypeId | ClearanceEnum.Admin
    db.session.commit()
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/make_cfo")
@login_required
@admin_required
def make_cfo(id: int):
    validate_user_id(id)
    user = db.session.get(User, id)
    user.userTypeId = user.userTypeId | ClearanceEnum.CFO
    db.session.commit()
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/remove_admin")
@login_required
@admin_required
def remove_admin(id: int):
    validate_user_id(id)
    if id == g.user.id:
        flash("You can't demote yourself!")
        return redirect(url_for("admin.list_users"))
    user = db.session.get(User, id)
    user.userTypeId = user.userTypeId & ~ClearanceEnum.Admin
    db.session.commit()
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/remove_cfo")
@login_required
@admin_required
def remove_cfo(id: int):
    validate_user_id(id)
    user = db.session.get(User, id)
    user.userTypeId = user.userTypeId & ~ClearanceEnum.CFO
    db.session.commit()
    return redirect(url_for("admin.list_users"))

@bp.route("/<int:id>/delete_user")
@login_required
@admin_required
def delete_user(id: int):
    validate_user_id(id)
    if id == g.user.id:
        flash("You can't delete yourself!")
        return redirect(url_for("admin.list_users"))

    user = db.session.get(User, id)
    db.session.execute(
        db.update(Receipt)
        .where(Receipt.userId == user.id)
        .values(userId=0)
    )
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("admin.list_users"))

def validate_user_id(id: int):
    is_protected_user = id < 1
    if is_protected_user:
        return abort(403)
