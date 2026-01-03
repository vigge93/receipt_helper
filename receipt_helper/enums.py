from enum import Enum, IntEnum, IntFlag, auto, unique


@unique
class ClearanceEnum(IntFlag):
    User = 1
    Admin = 2
    CFO = 4


@unique
class ReceiptStatusEnum(IntEnum):
    Pending = 10
    Handled = 80
    Rejected = 90


@unique
class LogTypeEnum(IntEnum):
    User = 10
    Admin = 20
    CFO = 30


STATUS_COLOR_MAP = {
    ReceiptStatusEnum.Pending: "yellow",
    ReceiptStatusEnum.Handled: "lightgreen",
    ReceiptStatusEnum.Rejected: "red",
}
