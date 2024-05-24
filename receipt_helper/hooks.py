from flask import current_app, url_for

from receipt_helper.forms.receipt_forms import SubmitReceiptForm
from receipt_helper.model.receipt import Receipt
from receipt_helper.util import send_email


def pre_submit_hook(form: SubmitReceiptForm):
    """Called after form validation, but before form processing."""
    pass


def post_submit_hook(receipt: Receipt):
    """Called after receipt has been committed to database."""
    send_email(
        current_app.config["RECEIPTS_EMAIL_RECEIPT_RECIPIENT"],
        "Ny kvittoredovisning",
        f"""Hej,

Det har inkommit en ny kvittoredovisning från {receipt.user.name}:

{url_for('main.view_receipt', id=receipt.id, _external=True)}

""",
    )


def pre_approve_hook(receipt: Receipt):
    pass


def post_approve_hook(receipt: Receipt):
    pass


def pre_reject_hook(receipt: Receipt):
    pass


def post_reject_hook(receipt: Receipt):
    send_email(
        receipt.user.email,
        "Kvittoredovisning nekad",
        f"""Hej,

En av dina kvittoredovisningar har blivit nekad. För mer detaljer, se {url_for('main.view_receipt', id=receipt.id, _external=True)}.
""",
    )
