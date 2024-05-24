from enum import Enum, IntFlag, auto, unique


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


STATUS_COLOR_MAP = {
    ReceiptStatusEnum.Pending: "yellow",
    ReceiptStatusEnum.Handled: "lightgreen",
    ReceiptStatusEnum.Rejected: "red",
}
