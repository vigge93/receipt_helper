import os
from uuid import uuid4
import csv
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from receipt_helper import db
from receipt_helper.auth import admin_required, login_required
from receipt_helper.enums import ClearanceEnum
from receipt_helper.forms.user_forms import AddManyUsersForm, AddSingleUserForm
from receipt_helper.model.user import User

from werkzeug.security import generate_password_hash
from werkzeug.datastructures import MultiDict

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
    users = db.session.execute(db.select(User)).scalars().all()
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


def add_user(name, email):
    temp_password = str(uuid4())

    user = User(
        email=email,
        name=name,
        password=generate_password_hash(temp_password),
        userTypeId=ClearanceEnum.User.value,
    )

    db.session.add(user)

    # TODO: Send email with temp password!
    print(email, temp_password, sep=": ")


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
