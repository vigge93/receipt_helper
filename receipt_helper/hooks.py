from receipt_helper.forms.receipt_forms import SubmitReceiptForm
from receipt_helper.model.receipt import Receipt


def pre_submit_hook(form: SubmitReceiptForm):
    """Called after form validation, but before form processing."""
    pass

def post_submit_hook(receipt: Receipt):
    """Called after receipt has been committed to database."""
    pass

def pre_approve_hook():
    pass

def post_approve_hook():
    pass

def pre_reject_hook():
    pass

def post_reject_hook():
    pass