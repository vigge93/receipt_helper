from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from receipt_helper import db
from receipt_helper.model.receipt import Receipt
from receipt_helper.model.user import User


class LogType(db.Model):
    __tablename__ = "Logtype"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class Log(db.Model):
    __tablename__ = "Log"
    id: Mapped[int] = mapped_column(primary_key=True)
    datetime: Mapped[datetime]
    logTypeId: Mapped[int] = mapped_column(db.ForeignKey(LogType.id))
    actionBy: Mapped[int] = mapped_column(db.ForeignKey(User.id))
    receiptId: Mapped[int | None] = mapped_column(db.ForeignKey(Receipt.id))
    userId: Mapped[int | None] = mapped_column(db.ForeignKey(User.id))
    action: Mapped[str]

    actionByUser: Mapped[User] = relationship(foreign_keys=[actionBy])
    user: Mapped[User] = relationship(foreign_keys=[userId], back_populates="logs")
    receipt: Mapped[Receipt] = relationship(back_populates="logs")
    logType: Mapped[LogType] = relationship()
