
import datetime
from typing import Sequence
from receipt_helper.enums import ClearanceEnum, ReceiptStatusEnum
from receipt_helper.model.receipt import File, Receipt
from receipt_helper import db
from receipt_helper.model.user import User
from sqlalchemy import exc

def get_user_receipts(user_id: int) -> Sequence[Receipt]:
    receipts = (
        db.session.execute(
            db.select(Receipt)
            .filter_by(userId=user_id)
            .order_by(Receipt.statusId, Receipt.submit_date, Receipt.receipt_date)
        )
        .scalars()
        .all()
    )
    return receipts

def get_all_receipts(archived:bool|None=False) -> Sequence[Receipt]:
    receipts = (
        db.session.execute(
            db.select(Receipt)
            .filter_by(archived=archived)
            .order_by(Receipt.statusId, Receipt.submit_date, Receipt.receipt_date)
        )
        .scalars()
        .all()
    )
    return receipts

def insert_receipt(receipt: Receipt) -> None:
    db.session.add(receipt)
    db.session.commit()

def get_file(filename: str) -> File | None:
    file = db.session.execute(
        db.select(File).filter_by(filename=filename)
    ).scalar()
    return file

def get_receipt(id: int) -> Receipt | None:
    return db.session.get(Receipt, id)

def archive_receipt(id: int) -> bool:
    receipt = db.session.get(Receipt, id)
    if not receipt:
        return False
    receipt.archived = True
    db.session.commit()
    return True

def change_receipt_status(id: int, status: ReceiptStatusEnum, reason=None) -> bool:
    receipt = db.session.get(Receipt, id)
    if not receipt:
        return False
    receipt.statusId = status.value
    receipt.statusComment = reason
    db.session.commit()
    return True

def get_user(id: int) -> User | None:
    return db.session.get(User, id)

def get_users() -> Sequence[User]:
    users = db.session.execute(db.select(User).where(User.id > 0)).scalars().all()
    return users

def get_user_by_email(email: str) -> User | None:
    return db.session.execute(db.select(User).filter_by(email=email)).scalars().first()

def update_user_last_login(id: int) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.lastLogin = datetime.datetime.now(datetime.UTC)
    db.session.commit()
    return True

def update_user_password(id: int, hashed_password: str) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.password = hashed_password
    user.needs_password_change = False
    db.session.commit()
    return True

def add_user(user: User) -> bool:
    try:
        db.session.add(user)
        db.session.commit()
        return True
    except exc.SQLAlchemyError:
        db.session.rollback()
        return False

def reset_user_password(id: int, hashed_temp_password: str) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.password = hashed_temp_password
    user.needs_password_change = True
    db.session.commit()
    return True

def add_user_role(id: int, new_role: ClearanceEnum) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.userTypeId = user.userTypeId | new_role
    db.session.commit()
    return True

def remove_user_role(id: int, role: ClearanceEnum) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    user.userTypeId = user.userTypeId & ~role
    db.session.commit()
    return True

def delete_user(id: int) -> bool:
    user = db.session.get(User, id)
    if not user:
        return False
    db.session.execute(
        db.update(Receipt)
        .where(Receipt.userId == user.id)
        .values(userId=0)
    )
    db.session.delete(user)
    db.session.commit()
    return True