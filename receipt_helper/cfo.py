import datetime
import os
import tempfile
from shutil import make_archive, move

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from receipt_helper import db
from receipt_helper.auth import cfo_required, login_required
from receipt_helper.enums import ReceiptStatusEnum
from receipt_helper.forms.receipt_forms import RejectReceiptForm
from receipt_helper.hooks import (
    post_approve_hook,
    post_reject_hook,
    pre_approve_hook,
    pre_reject_hook,
)
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
            db.select(Receipt)
            .filter_by(archived=False)
            .order_by(Receipt.statusId, Receipt.submit_date, Receipt.receipt_date)
        )
        .scalars()
        .all()
    )

    return render_template("cfo/view_receipts.html", receipts=receipts)


@bp.route("/view_archived_receipts")
@login_required
@cfo_required
def view_archived_receipts():
    receipts = (
        db.session.execute(
            db.select(Receipt)
            .filter_by(archived=True)
            .order_by(Receipt.statusId, Receipt.submit_date, Receipt.receipt_date)
        )
        .scalars()
        .all()
    )

    return render_template("cfo/view_archive.html", receipts=receipts)


@bp.route("/get_receipts")
@login_required
@cfo_required
def get_receipts():
    file = tempfile.TemporaryFile("w+b", suffix=".zip", delete=False)
    print(current_app.config["RECEIPTS_STORAGE_PATH"])
    make_archive(
        file.name.removesuffix(".zip"),
        "zip",
        current_app.config["RECEIPTS_STORAGE_PATH"]
    )
    file.seek(0)
    return send_file(file, download_name="kvitton.zip")


@bp.route("/<int:id>/archive")
@login_required
@cfo_required
def archive_receipt(id: int):
    receipt = db.session.get(Receipt, id)
    receipt.archived = True
    db.session.commit()
    return redirect(url_for("cfo.view_receipts"))


@bp.route("/<int:id>/approve")
@login_required
@cfo_required
def approve_receipt(id: int):
    receipt = db.session.get(Receipt, id)

    pre_approve_hook(receipt)

    receipt.statusId = ReceiptStatusEnum.Handled.value

    move_file(receipt.file, "approved", receipt.submit_date.date())

    db.session.commit()

    post_approve_hook(receipt)
    return redirect(url_for("cfo.view_receipts"))


@bp.route("/<int:id>/reject", methods=("GET", "POST"))
@login_required
@cfo_required
def reject_receipt(id: int):
    form = RejectReceiptForm()
    if request.method != "POST" or not form.validate_on_submit():
        return render_template("cfo/reject_receipt.html", form=form)

    reason = form.reason.data

    receipt = db.session.get(Receipt, id)

    pre_reject_hook(receipt)
    receipt.statusId = ReceiptStatusEnum.Rejected.value
    receipt.statusComment = reason

    move_file(receipt.file, "rejected", receipt.submit_date.date())

    db.session.commit()
    post_reject_hook(receipt)

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
    path = os.path.join(
        current_app.config["RECEIPTS_STORAGE_PATH"], dest, date.isoformat()
    )
    os.makedirs(
        path,
        exist_ok=True,
    )

    filename = file.filename
    dest_path = os.path.join(path, filename)

    move(os.path.join(file.path, filename), dest_path)
    file.path = path
