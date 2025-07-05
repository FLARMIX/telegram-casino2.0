from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Boolean


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rank: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String)
    balance_main: Mapped[int] = mapped_column(Integer)
    balance_alt: Mapped[int] = mapped_column(Integer)
    last_bonus_time: Mapped[str] = mapped_column(DateTime)
    last_mini_bonus_time: Mapped[str] = mapped_column(DateTime)
    mini_bonus_count: Mapped[int] = mapped_column(Integer)
    bonus_count: Mapped[int] = mapped_column(Integer)
    your_owner: Mapped[str] = mapped_column(String)
    your_slave: Mapped[str] = mapped_column(String)
    is_immune: Mapped[bool] = mapped_column(Boolean)
    is_admin: Mapped[bool] = mapped_column(Boolean)
    is_hidden: Mapped[bool] = mapped_column(Boolean)
    is_worker: Mapped[bool] = mapped_column(Boolean)
    work_name: Mapped[str] = mapped_column(String)
    tgusername: Mapped[str] = mapped_column(String)
    tguserid: Mapped[int] = mapped_column(Integer)

class Item(Base):
    __tablename__ = "Items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(String)
    item_path: Mapped[str] = mapped_column(String)
    item_type: Mapped[str] = mapped_column(String)
    item_buy_price: Mapped[int] = mapped_column(Integer)
    item_sell_price: Mapped[int] = mapped_column(Integer)

class UserItems(Base):
    __tablename__ = "UserItems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    items_list: Mapped[str] = mapped_column(String)
    avatar_item: Mapped[str] = mapped_column(String)
    tguserid: Mapped[int] = mapped_column(Integer)

class Slavery(Base):
    __tablename__ = "Slavery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tguserid: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[int] = mapped_column(Integer)
    slave_id: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[str] = mapped_column(DateTime)
    last_payout_time: Mapped[str] = mapped_column(DateTime)
    piggy_bank: Mapped[int] = mapped_column(Integer)
    last_withdrawal_time: Mapped[str] = mapped_column(DateTime)

