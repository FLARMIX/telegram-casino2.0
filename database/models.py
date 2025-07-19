from enum import Enum


class ItemType(str, Enum):
    AVATAR = "avatar"
    PHONE = "phone"
    HOUSE = "house"
    OTHER = "other"

class TradeStatus(str, Enum):
    pending = "pending"
    completed = "completed"
