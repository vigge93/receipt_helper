from functools import reduce
from itertools import combinations_with_replacement

from werkzeug.security import generate_password_hash

from receipt_helper.enums import STATUS_COLOR_MAP, ClearanceEnum, ReceiptStatusEnum
from receipt_helper.model.receipt import Receipt, ReceiptStatus
from receipt_helper.model.user import User
from receipt_helper.model.usertype import UserType


def init_db(app, db):
    try:
        with app.app_context():
            db.create_all()
            clearances = combinations_with_replacement(ClearanceEnum, len(ClearanceEnum))
            clearances = [
                reduce(lambda curr, next: curr | next, clearance)
                for clearance in clearances
            ]
            clearances = set(clearances)
            for clearance in clearances:
                db.session.add(UserType(id=clearance.value, name=clearance.name))
            for status in ReceiptStatusEnum:
                db.session.add(
                    ReceiptStatus(
                        id=status.value,
                        displayName=status.name,
                        displayColor=STATUS_COLOR_MAP[status],
                    )
                )
            db.session.add(
                User(id=0, email="DELETED", name="DELETED", password='a')
            )
            db.session.add(
                User(
                    email=app.config["RECEIPTS_ADMIN_USER_EMAIL"],
                    name=app.config["RECEIPTS_ADMIN_USER_NAME"],
                    password=generate_password_hash(app.config["RECEIPTS_ADMIN_USER_PASSWORD"]),
                    userTypeId=(ClearanceEnum.User|ClearanceEnum.Admin)
                )
            )
            db.session.commit()
            
    except Exception as ex:
        print(ex)