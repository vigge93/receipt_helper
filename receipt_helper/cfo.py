import datetime
import os
from shutil import make_archive, move

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)

from receipt_helper.auth import cfo_required, login_required
from receipt_helper import db
from receipt_helper.enums import ReceiptStatusEnum
from receipt_helper.model.receipt import File, Receipt

bp = Blueprint("cfo", __name__, url_prefix="/cfo")


@bp.route("/")
@login_required
@cfo_required
def index():
    return render_template("cfo/index.html")


@bp.route("/view_receipts")
@login_required
@cfo_required
def view_receipts():
    receipts = (
        db.session.execute(
            db.select(Receipt).order_by(
                Receipt.statusId, Receipt.submit_date, Receipt.receipt_date
            )
        )
        .scalars()
        .all()
    )

    return render_template("cfo/view_receipts.html", receipts=receipts)


@bp.route("/get_receipts")
@login_required
@cfo_required
def get_receipts():
    make_archive(
        os.path.join(current_app.instance_path, "receipts"),
        "zip",
        os.path.join(current_app.instance_path, "receipts"),
    )
    return send_from_directory(current_app.instance_path, "receipts.zip")


@bp.route("/<int:id>/approve")
@login_required
@cfo_required
def approve_receipt(id: int):
    receipt = db.session.get(Receipt, id)

    receipt.statusId = ReceiptStatusEnum.Handled.value

    move_file(receipt.file, "approved", receipt.submit_date.date())

    db.session.commit()
    return redirect(url_for("cfo.view_receipts"))


@bp.route("/<int:id>/reject")
@login_required
@cfo_required
def reject_receipt(id: int):
    receipt = db.session.get(Receipt, id)

    receipt.statusId = ReceiptStatusEnum.Rejected.value

    move_file(receipt.file, "rejected", receipt.submit_date.date())

    db.session.commit()
    return redirect(url_for("cfo.view_receipts"))


@bp.route("/<int:id>/submitted")
@login_required
@cfo_required
def move_receipt_to_submitted(id: int):
    receipt = db.session.get(Receipt, id)

    receipt.statusId = ReceiptStatusEnum.Pending.value

    move_file(receipt.file, "submitted", receipt.submit_date.date())

    db.session.commit()
    return redirect(url_for("cfo.view_receipts"))


def move_file(file: File, dest: str, date: datetime.date):
    path = os.path.join(current_app.instance_path, "receipts", dest, date.isoformat())
    os.makedirs(
        path,
        exist_ok=True,
    )

    filename = file.filename
    dest_path = os.path.join(path, filename)

    move(os.path.join(file.path, filename), dest_path)
    file.path = path
