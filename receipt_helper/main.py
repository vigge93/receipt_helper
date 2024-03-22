import datetime
import os
import tempfile

from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from pypdf import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

from receipt_helper import db
from receipt_helper.auth import login_required
from receipt_helper.enums import ClearanceEnum
from receipt_helper.forms.receipt_forms import SubmitReceiptForm
from receipt_helper.hooks import post_submit_hook, pre_submit_hook
from receipt_helper.model.receipt import File, Receipt

bp = Blueprint("main", __name__, url_prefix="/")


@bp.route("/")
@login_required
def index():
    receipts = (
        db.session.execute(
            db.select(Receipt)
            .filter_by(userId=g.user.id)
            .order_by(Receipt.statusId, Receipt.submit_date, Receipt.receipt_date)
        )
        .scalars()
        .all()
    )
    return render_template("main/index.html", receipts=receipts)


@bp.route("/add", methods=("GET", "POST"))
@login_required
def add_receipt():
    form = SubmitReceiptForm()
    if request.method != "POST" or not form.validate_on_submit():
        return render_template("main/submit.html", form=form)

    pre_submit_hook(form)
    receipt_date = form.receipt_date.data
    body = form.body.data
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
        f"{submit_date_str}_{body}{os.path.splitext(file.filename)[-1]}"
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
    receipt_file = File(filename=filename, path=path)
    receipt = Receipt(
        userId=g.user.id,
        receipt_date=receipt_date,
        submit_date=submit_date,
        body=body,
        activity=activity,
        amount=amount,
        file=receipt_file,
    )

    db.session.add(receipt)
    db.session.commit()
    post_submit_hook(receipt)
    return redirect(url_for("index"))


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while (
        os.path.exists(path)
        or db.session.execute(
            db.select(File).filter_by(filename=os.path.split(path)[1])
        ).scalar()
    ):
        path = f"{filename}_{counter}{extension}"
        counter += 1

    return path


@bp.route("/receipt/<int:id>")
@login_required
def view_receipt(id: int):
    receipt = db.session.get(Receipt, id)

    owns_receipt = receipt.userId == g.user.id
    is_cfo = ClearanceEnum.CFO in ClearanceEnum(g.user.userTypeId)
    authorized = owns_receipt or is_cfo
    if receipt is None or not authorized:
        abort(404)

    return render_template("main/view_receipt.html", receipt=receipt)


@bp.route("/receipt/<int:id>/receipt")
@login_required
def get_receipt_document(id: int):
    receipt = db.session.get(Receipt, id)

    owns_receipt = receipt.userId == g.user.id
    is_cfo = ClearanceEnum.CFO in ClearanceEnum(g.user.userTypeId)
    authorized = owns_receipt or is_cfo
    if receipt is None or not authorized:
        abort(404)

    return send_from_directory(receipt.file.path, receipt.file.filename)


@bp.route("/receipt/<int:id>/document")
@login_required
def get_document(id: int):
    receipt = db.session.get(Receipt, id)

    owns_receipt = receipt.userId == g.user.id
    is_cfo = ClearanceEnum.CFO in ClearanceEnum(g.user.userTypeId)
    authorized = owns_receipt or is_cfo
    if receipt is None or not authorized:
        abort(404)

    reader = PdfReader(
        os.path.join(
            current_app.root_path, current_app.template_folder, "kvittoredovisning.pdf"
        )
    )
    writer = PdfWriter()

    writer.append(reader)

    writer.update_page_form_field_values(
        writer.pages[0],
        {
            "Datum_kvittot": receipt.receipt_date.date().isoformat(),
            "Datum_idag": receipt.submit_date.date().isoformat(),
            "organ": receipt.body,
            "Kortinnehavare": receipt.user.name,
            "aktivitet": receipt.activity,
            "summa": receipt.amount / 100,
        },
    )

    file = tempfile.TemporaryFile("w+b", suffix=".pdf")
    writer.write(file)
    file.seek(0)
    return send_file(file, download_name=f"kvittoredovisning.pdf")
