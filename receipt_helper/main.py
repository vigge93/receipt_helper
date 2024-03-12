import datetime
import os
from flask import (
    Blueprint,
    abort,
    current_app,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

from receipt_helper.auth import login_required

from receipt_helper import db
from receipt_helper.forms.receipt_forms import SubmitReceiptForm
from receipt_helper.hooks import post_submit_hook, pre_submit_hook
from receipt_helper.model.receipt import File, Receipt

bp = Blueprint("main", __name__, url_prefix="/")


@bp.route("/")
@login_required
def index():
    receipts = (
        db.session.execute(db.select(Receipt).filter_by(userId=g.user.id).order_by(Receipt.statusId, Receipt.submit_date, Receipt.receipt_date))
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
    external = form.external.data
    submit_date = datetime.date.today()
    submit_date_str = submit_date.isoformat()
    file = form.file.data

    os.makedirs(
        os.path.join(current_app.instance_path, "receipts", submit_date_str),
        exist_ok=True,
    )

    filename = secure_filename(file.filename)
    sec_body = secure_filename(body)
    filename = f"{submit_date_str}_{sec_body}{os.path.splitext(filename)[-1]}"
    filename = os.path.join(
        current_app.instance_path, "receipts", submit_date_str, filename
    )
    filename = uniquify(filename)
    file.save(filename)

    receipt_file = File(filename=filename)
    receipt = Receipt(
        userId=g.user.id,
        receipt_date=receipt_date,
        submit_date=submit_date,
        body=body,
        activity=activity,
        amount=amount,
        external=external,
        file=receipt_file,
    )

    db.session.add(receipt)
    db.session.commit()
    post_submit_hook(receipt)
    return redirect(url_for("index"))


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = f"{filename}_{counter}{extension}"
        counter += 1

    return path


@bp.route('/receipt/<int:id>')
@login_required
def view_receipt(id: int):
    receipt = db.session.get(Receipt, id)
    if receipt is None or receipt.userId != g.user.id:
        abort(404)
    
    return render_template('main/view_receipt.html', receipt=receipt)

@bp.route('/receipt/<int:id>/document')
@login_required
def get_receipt_document(id: int):
    receipt = db.session.get(Receipt, id)
    if receipt is None or receipt.userId != g.user.id:
        abort(404)
    
    return send_from_directory(*os.path.split(receipt.file.filename))
