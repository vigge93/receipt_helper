from enum import Enum, IntFlag, unique, auto


@unique
class ClearanceEnum(IntFlag):
    User = auto()
    Admin = auto()
    CFO = auto()


@unique
class ReceiptStatusEnum(Enum):
    Pending = 10
    Handled = 80
    Rejected = 90
