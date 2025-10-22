from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, Enum, ARRAY

from database.models import TradeStatus



class Base(DeclarativeBase):
    pass



class User(Base):
    __tablename__ = "Users"

    # Main stats
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # rank: Mapped[str] = mapped_column(String)                       # Player rank (Moder, Admin, Player)
    username: Mapped[str] = mapped_column(String)                   # User's nickname
    balance_main: Mapped[int] = mapped_column(Integer)              # User's balance in $
    balance_alt: Mapped[int] = mapped_column(Integer)               # User's alternative balance
    last_bonus_time: Mapped[str] = mapped_column(DateTime)          # User's last get bonus time
    last_mini_bonus_time: Mapped[str] = mapped_column(DateTime)     # User's last get mini bonus time
    mini_bonus_count: Mapped[int] = mapped_column(Integer)          # User's mini bonus count
    bonus_count: Mapped[int] = mapped_column(Integer)               # User's bonus count
    roulette_zero_count: Mapped[int] = mapped_column(Integer)       # User's roulette zero count
    slot_777_count: Mapped[int] = mapped_column(Integer)            # User's slot 777 count
    is_admin: Mapped[bool] = mapped_column(Boolean)                 # User is admin
    is_hidden: Mapped[bool] = mapped_column(Boolean)

    # Slavery
    your_owner: Mapped[str] = mapped_column(String)                 # User's owner (Slavery)
    your_slave: Mapped[str] = mapped_column(String)                 # User's slave (Slavery)
    is_immune: Mapped[bool] = mapped_column(Boolean)                # User's immunity (Slavery)

    # Trades
    cur_trade_id: Mapped[int] = mapped_column(Integer)              # Trade id (Trades)
    is_in_trade: Mapped[bool] = mapped_column(Boolean)              # User's trade (Trades)

    # Dices
    cur_dice_game_id: Mapped[int] = mapped_column(Integer)          # Dice game id (Dices)

    # Blackjack
    cur_blackjack_game_id: Mapped[int] = mapped_column(Integer)
    is_in_blackjack: Mapped[bool] = mapped_column(Boolean)

    # For the future
    work_name: Mapped[str] = mapped_column(String)
    is_worker: Mapped[bool] = mapped_column(Boolean)

    # Tecnical stats
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


class Rank(Base):
    __tablename__ = "Ranks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rank_name: Mapped[str] = mapped_column(String)
    rank_buy_price: Mapped[int] = mapped_column(Integer)
    rank_sell_price: Mapped[int] = mapped_column(Integer)


class UserItems(Base):
    __tablename__ = "UserItems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Base items
    items_list: Mapped[str] = mapped_column(String)
    avatar_item: Mapped[str] = mapped_column(String)

    # TODO: Сделать инвентарь рангов!
    # User ranks
    ranks_list: Mapped[str] = mapped_column(String)
    current_rank: Mapped[str] = mapped_column(String)

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


class Trade(Base):
    __tablename__ = "Trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_user_id: Mapped[int] = mapped_column(Integer)
    second_user_id: Mapped[int] = mapped_column(Integer)

    first_user_offer_type: Mapped[str] = mapped_column(String)
    second_user_offer_type: Mapped[str] = mapped_column(String)

    first_user_offer: Mapped[str] = mapped_column(String)
    second_user_offer: Mapped[str] = mapped_column(String)

    first_user_confirm: Mapped[bool] = mapped_column(Boolean)
    second_user_confirm: Mapped[bool] = mapped_column(Boolean)

    first_user_post_confirm: Mapped[bool] = mapped_column(Boolean)
    second_user_post_confirm: Mapped[bool] = mapped_column(Boolean)

    status: Mapped[str] = mapped_column(Enum(TradeStatus))

    created_at: Mapped[str] = mapped_column(DateTime)

    first_user_message_id: Mapped[int] = mapped_column(Integer)
    second_user_message_id: Mapped[int] = mapped_column(Integer)


class Dice(Base):
    __tablename__ = "Dices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_user_id: Mapped[int] = mapped_column(Integer)
    second_user_id: Mapped[int] = mapped_column(Integer)

    bet_amount: Mapped[int] = mapped_column(Integer)


class BlackjackGame(Base):
    __tablename__ = "BlackjackGames"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    first_user_id: Mapped[int] = mapped_column(Integer)
    second_user_id: Mapped[int] = mapped_column(Integer)

    bet_amount: Mapped[int] = mapped_column(Integer)

    bank: Mapped[int] = mapped_column(Integer)

    last_action_first_user: Mapped[str] = mapped_column(DateTime)
    last_action_second_user: Mapped[str] = mapped_column(DateTime)

    first_user_cards: Mapped[list[str]] = mapped_column(String)
    second_user_cards: Mapped[list[str]] = mapped_column(String)

    first_user_cards_sum: Mapped[int] = mapped_column(Integer)
    second_user_cards_sum: Mapped[int] = mapped_column(Integer)

    deck: Mapped[list[str]] = mapped_column(String)

    current_turn_user_id: Mapped[int] = mapped_column(Integer)

    first_user_message_id: Mapped[int] = mapped_column(Integer)
    second_user_message_id: Mapped[int] = mapped_column(Integer)
