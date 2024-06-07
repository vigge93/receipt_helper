import datetime
import os
import tempfile
from shutil import make_archive, move

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from receipt_helper import database
from receipt_helper.auth import cfo_required, login_required
from receipt_helper.database import change_receipt_status, get_all_receipts, get_receipt
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
    receipts = get_all_receipts()
    return render_template("cfo/view_receipts.html", receipts=receipts)


@bp.route("/view_archived_receipts")
@login_required
@cfo_required
def view_archived_receipts():
    receipts = get_all_receipts(archived=True)

    return render_template("cfo/view_archive.html", receipts=receipts)


@bp.route("/get_receipts")
@login_required
@cfo_required
def get_receipts():
    file = tempfile.NamedTemporaryFile("w+b", suffix=".zip")
    make_archive(
        file.name.removesuffix(".zip"),
        "zip",
        current_app.config["RECEIPTS_STORAGE_PATH"]
    )
    file.seek(0)
    return send_file(file, download_name="kvitton.zip") # type: ignore


@bp.route("/<int:id>/archive")
@login_required
@cfo_required
def archive_receipt(id: int):
    if not database.archive_receipt(id):
        flash("Kvitto hittades ej!")
        return redirect(url_for("cfo.view_receipts"))
    return redirect(url_for("cfo.view_receipts"))


@bp.route("/<int:id>/approve")
@login_required
@cfo_required
def approve_receipt(id: int):
    receipt = get_receipt(id)

    if not receipt:
        flash("Kvitto hittades ej!")
        return redirect(url_for("cfo.view_receipts"))

    if not pre_approve_hook(receipt):
        return redirect(url_for("cfo.view_receipts"))

    if not change_receipt_status(id, ReceiptStatusEnum.Handled):
        flash("Kvitto hittades ej!")
        return redirect(url_for("cfo.view_receipts"))

    move_file(receipt.file, "approved", receipt.submit_date.date())

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

    receipt = get_receipt(id)

    if not receipt:
        flash("Kvitto hittades ej!")
        return redirect(url_for("cfo.view_receipts"))

    if not pre_reject_hook(receipt):
        return redirect(url_for("cfo.view_receipts"))
    
    if not change_receipt_status(id, ReceiptStatusEnum.Rejected, reason):
        flash("Kvitto hittades ej!")
        return redirect(url_for("cfo.view_receipts"))

    move_file(receipt.file, "rejected", receipt.submit_date.date())

    post_reject_hook(receipt)

    return redirect(url_for("cfo.view_receipts"))


@bp.route("/<int:id>/submitted")
@login_required
@cfo_required
def move_receipt_to_submitted(id: int):
    receipt = get_receipt(id)

    if not receipt or not change_receipt_status(id, ReceiptStatusEnum.Pending):
        flash("Kvitto hittades ej!")
        return redirect(url_for("cfo.view_receipts"))

    move_file(receipt.file, "submitted", receipt.submit_date.date())

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
