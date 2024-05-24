from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from receipt_helper import db
from receipt_helper.enums import ReceiptStatusEnum
from receipt_helper.model.user import User


class ReceiptStatus(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    displayName: Mapped[str]
    displayColor: Mapped[str]


class File(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str]
    filename: Mapped[str] = mapped_column(unique=True)


class Receipt(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    userId: Mapped[int] = mapped_column(db.ForeignKey(User.id))
    receipt_date: Mapped[datetime]
    submit_date: Mapped[datetime]
    activity: Mapped[str]
    amount: Mapped[int]
    """Pennies"""
    statusId: Mapped[int] = mapped_column(
        db.ForeignKey(ReceiptStatus.id), default=ReceiptStatusEnum.Pending.value
    )
    statusComment: Mapped[str | None]
    fileId: Mapped[int] = mapped_column(db.ForeignKey(File.id))
    archived: Mapped[bool] = mapped_column(default=False)

    user: Mapped[User] = relationship()
    status: Mapped[ReceiptStatus] = relationship()
    file: Mapped[File] = relationship()
