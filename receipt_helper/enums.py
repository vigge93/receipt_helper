from enum import Enum, IntFlag, unique, auto


@unique
class ClearanceEnum(IntFlag):
    User = auto()
    Admin = auto()
    CFO = auto()

@unique
class ReceiptStatusEnum(Enum):
    Pending = 10
    Approved = 20
    Paid = 30
    Rejected = 90
