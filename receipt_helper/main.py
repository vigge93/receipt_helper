import datetime
import os

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from receipt_helper import database
from receipt_helper.auth import login_required
from receipt_helper.enums import ClearanceEnum
from receipt_helper.forms.receipt_forms import SubmitReceiptForm
from receipt_helper.hooks import post_submit_hook, pre_submit_hook
from receipt_helper.model.receipt import File, Receipt
from receipt_helper.database import get_receipt, get_user_receipts, insert_receipt

bp = Blueprint("main", __name__, url_prefix="/")


@bp.route("/")
@login_required
def index():
    receipts = get_user_receipts(g.user.id)
    
    return render_template("main/index.html", receipts=receipts)


@bp.route("/add", methods=("GET", "POST"))
@login_required
def add_receipt():
    form = SubmitReceiptForm()
    if request.method != "POST" or not form.validate_on_submit():
        return render_template("main/submit.html", form=form)

    if not pre_submit_hook(form):
        flash("Något gick fel, försök igen eller kontakta en administratör för hjälp.")
        return redirect(url_for("main.add_receipt"))

    receipt_date = form.receipt_date.data
    activity = form.activity.data
    amount = int(form.amount.data * 100)
    submit_date = datetime.date.today()
    submit_date_str = submit_date.isoformat()
    file = form.file.data

    os.makedirs(
        os.path.join(
            current_app.config["RECEIPTS_STORAGE_PATH"], "submitted", submit_date_str
        ),
        exist_ok=True,
    )

    filename = secure_filename(
        f"{submit_date_str}_{g.user.name}{os.path.splitext(file.filename)[-1]}"
    )
    filename = os.path.join(
        current_app.config["RECEIPTS_STORAGE_PATH"],
        "submitted",
        submit_date_str,
        filename,
    )
    filename = uniquify(filename)
    file.save(filename)

    path, filename = os.path.split(filename)
    receipt_file = File(filename=filename, path=path) # type: ignore
    receipt = Receipt(
        userId=g.user.id,
        receipt_date=receipt_date,
        submit_date=submit_date,
        activity=activity,
        amount=amount,
        file=receipt_file,
    ) # type: ignore

    insert_receipt(receipt)
    if not post_submit_hook(receipt):
        pass
    return redirect(url_for("index"))


def uniquify(path: str):
    filename, extension = os.path.splitext(path)
    counter = 1

    while (
        os.path.exists(path)
        or database.get_file(os.path.split(path)[1])
    ):
        path = f"{filename}_{counter}{extension}"
        counter += 1

    return path


@bp.route("/receipt/<int:id>")
@login_required
def view_receipt(id: int):
    receipt = get_receipt(id)
    if not receipt:
        abort(404, "Kvitto hittades ej!")

    owns_receipt = receipt.userId == g.user.id
    is_cfo = ClearanceEnum.CFO in ClearanceEnum(g.user.userTypeId)
    authorized = owns_receipt or is_cfo
    if receipt is None or not authorized:
        abort(404, "Kvitto hittades ej!")

    return render_template("main/view_receipt.html", receipt=receipt)


@bp.route("/receipt/<int:id>/receipt")
@login_required
def get_receipt_document(id: int):
    receipt = get_receipt(id)
    if not receipt:
        return abort(404, "Kvitto hittades ej!")

    owns_receipt = receipt.userId == g.user.id
    is_cfo = ClearanceEnum.CFO in ClearanceEnum(g.user.userTypeId)
    authorized = owns_receipt or is_cfo
    if receipt is None or not authorized:
        abort(404, "Kvitto hittades ej!")

    return send_from_directory(receipt.file.path, receipt.file.filename)

