from functools import reduce
from itertools import combinations_with_replacement
from receipt_helper.enums import ClearanceEnum, ReceiptStatusEnum
from receipt_helper.model.user import User
from receipt_helper.model.usertype import UserType
from receipt_helper.model.receipt import Receipt, ReceiptStatus

from werkzeug.security import generate_password_hash


def init_db(app, db):
    with app.app_context():
        db.create_all()
        clearances = combinations_with_replacement(ClearanceEnum, len(ClearanceEnum))
        clearances = [reduce(lambda curr, next: curr | next, clearance) for clearance in clearances]
        clearances = set(clearances)
        for clearance in clearances:
            db.session.add(UserType(id=clearance.value, name=clearance.name))
        for clearance in ReceiptStatusEnum:
            db.session.add(
                ReceiptStatus(id=clearance.value, displayName=clearance.name)
            )
        db.session.add(
            User(email="a@b.c", name="Kalle Kula", password=generate_password_hash("123"), userTypeId=ClearanceEnum.User.value, needs_password_change=False)
        )
        db.session.commit()
