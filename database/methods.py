import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Sequence, List

from sqlalchemy import select, ChunkedIteratorResult, update, delete
from sqlalchemy.orm import Mapped

from config import ADMIN_IDs
from .SQLmodels import Base, Slavery, User, UserItems, Item, Trade, Rank, Dice
from database.session import engine, AsyncSessionLocal


logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Инициализирует базу данных.
    :return:
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_user_by_tguserid(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> Optional[User]:
    """
    Возвращает пользователя по его ID.
    :param tguserid: ID пользователя
    :param session: Сессия БД
    :return: User
    """
    stmt = select(User).where(User.tguserid == tguserid)
    result: ChunkedIteratorResult[User] = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_tgusername(session: AsyncSessionLocal, tgusername: str) -> Optional[User]:
    """
    Возвращает пользоввателя по его username.
    :param tgusername: username пользователя
    :param session: Сессия БД
    :return: User
    """
    stmt = select(User).where(User.tgusername == tgusername)
    result: ChunkedIteratorResult[User] = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSessionLocal) -> Sequence[Any]:
    """
    Возвращает всех пользователей.
    :return: Sequence[User]
    """
    stmt = select(User)
    result: ChunkedIteratorResult[User] = await session.execute(stmt)
    return result.scalars().all()


async def get_user_by_id(session: AsyncSessionLocal, id: int) -> Optional[User]:
    stmt = select(User).where(User.id == id)
    result: ChunkedIteratorResult[User] = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_stat(session: AsyncSessionLocal, tguserid: int | Mapped[int], stat_name: str):
    stmt = select(User).where(User.tguserid == tguserid)
    result: ChunkedIteratorResult[User] = await session.execute(stmt)
    return getattr(result.scalar_one_or_none(), stat_name)


async def get_dict_user_items(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> dict:
    stmt = select(UserItems.items_list).where(UserItems.tguserid == tguserid)
    pre_result = await session.execute(stmt)
    result = pre_result.scalar_one_or_none()
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {}
    else:
        return {}

async def get_user_items(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> List[Item] | None:
    stmt = select(UserItems.items_list).where(UserItems.tguserid == tguserid)
    pre_result = await session.execute(stmt)
    result = pre_result.scalar_one_or_none()
    if result:
        loaded_items = json.loads(result)
        item_list = []
        for item, _ in loaded_items.items():
            item = await get_item_by_name(session, item)
            item_list.append(item)

        return item_list
    else:
        return None


async def create_trade(
                        session: AsyncSessionLocal,
                        first_user_id: int | Mapped[int],
                        second_user_id: int | Mapped[int],

                        first_user_offer_type: str,
                        second_user_offer_type: str,

                        first_user_offer: str,
                        second_user_offer: str,

                        status: str,
                        created_at: datetime,

                        first_user_message_id: int | Mapped[int] = -1,
                        second_user_message_id: int | Mapped[int] = -1,

                        first_user_confirm: bool = False,
                        second_user_confirm: bool = False,

                        first_user_post_confirm: bool = False,
                        second_user_post_confirm: bool = False,
                    ) -> Trade:
    trade = Trade(
        first_user_id=first_user_id,
        second_user_id=second_user_id,

        first_user_offer_type=first_user_offer_type,
        second_user_offer_type=second_user_offer_type,

        first_user_offer=first_user_offer,
        second_user_offer=second_user_offer,

        first_user_confirm=first_user_confirm,
        second_user_confirm=second_user_confirm,

        first_user_post_confirm=first_user_post_confirm,
        second_user_post_confirm=second_user_post_confirm,

        status=status,
        created_at=created_at,

        first_user_message_id=first_user_message_id,
        second_user_message_id=second_user_message_id
    )

    session.add(trade)
    await session.commit()
    return trade


async def create_dice_game(
                        session: AsyncSessionLocal,
                        first_user_id: int | Mapped[int],
                        second_user_id: int | Mapped[int],
                        bet_amount: int | Mapped[int]
                    ) -> Dice:
    dice = Dice(
        first_user_id=first_user_id,
        second_user_id=second_user_id,
        bet_amount=bet_amount
    )

    session.add(dice)
    await session.commit()
    return dice


async def get_item_by_name(session: AsyncSessionLocal, item_name: str) -> Optional[Item]:
    stmt = select(Item).where(Item.item_name == item_name)
    result: ChunkedIteratorResult[Item] = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_item_by_id(session: AsyncSessionLocal, item_id: int) -> Optional[Item]:
    stmt = select(Item).where(Item.id == item_id)
    result: ChunkedIteratorResult[Item] = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_avatar(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> str:
    stmt = select(UserItems.avatar_item).where(UserItems.tguserid == tguserid)
    pre_result = await session.execute(stmt)
    result = pre_result.scalar_one_or_none()

    return result if result is not None else "черви"


async def get_trade_status(session: AsyncSessionLocal, trade_id: int | Mapped[int]) -> str:
    stmt = select(Trade).where(Trade.id == trade_id)
    pre_result: ChunkedIteratorResult[Trade] = await session.execute(stmt)
    result: Trade = pre_result.scalar_one_or_none()
    return result.status


async def get_trade_by_trade_id(session: AsyncSessionLocal, trade_id: int | Mapped[int]) -> Optional[Trade]:
    stmt = select(Trade).where(Trade.id == trade_id)
    pre_result: ChunkedIteratorResult[Trade] = await session.execute(stmt)
    result: Trade = pre_result.scalar_one_or_none()
    return result


async def get_dice_game_by_id(session: AsyncSessionLocal, dice_id: int | Mapped[int]) -> Optional[Dice]:
    stmt = select(Dice).where(Dice.id == dice_id)
    pre_result: ChunkedIteratorResult[Dice] = await session.execute(stmt)
    result: Dice = pre_result.scalar_one_or_none()
    return result


async def add_rank_to_user(session: AsyncSessionLocal, rank: str, tguserid: int | Mapped[int]) -> bool:
    user_ranks = await get_user_ranks_string_list(session, tguserid)
    rank = await get_rank_by_name(session, rank)
    rank_id = str(rank.id)

    if rank_id not in user_ranks:
        new_ranks = ','.join(user_ranks + [rank_id + ','])
        stmt = update(UserItems).where(UserItems.tguserid == tguserid).values(ranks_list=new_ranks)
        await session.execute(stmt)
        await session.commit()
        return True

    else:
        print('000')
        return False


async def get_user_ranks(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> List[Rank] | None:
    stmt = select(UserItems.ranks_list).where(UserItems.tguserid == tguserid)
    pre_result: ChunkedIteratorResult[UserItems] = await session.execute(stmt)
    result = pre_result.scalar_one_or_none()
    if result:
        temp_list = []
        for rank in result.split(",")[:-1]:
            rank_object = await get_rank_by_id(session, int(rank))
            temp_list.append(rank_object)
        return temp_list

    return []


async def get_user_ranks_string_list(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> List[str] | None:
    stmt = select(UserItems.ranks_list).where(UserItems.tguserid == tguserid)
    pre_result: ChunkedIteratorResult[UserItems] = await session.execute(stmt)
    result = pre_result.scalar_one_or_none()
    if result:
        temp_list = []
        for rank in result.split(",")[:-1]:
            rank_object = await get_rank_by_id(session, int(rank))
            temp_list.append(str(rank_object.id))
        return temp_list

    return []


async def get_user_rank(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> Rank:
    stmt = select(UserItems.current_rank).where(UserItems.tguserid == tguserid)
    pre_result: ChunkedIteratorResult[UserItems] = await session.execute(stmt)
    result: str = pre_result.scalars().first()

    if result.isdigit():
        rank = await get_rank_by_id(session, int(result))
    else:
        rank = result

    return rank


async def get_rank_by_id(session: AsyncSessionLocal, rank_id: int | Mapped[int]) -> Optional[Rank]:
    stmt = select(Rank).where(Rank.id == rank_id)
    pre_result: ChunkedIteratorResult[Rank] = await session.execute(stmt)
    result: Rank = pre_result.scalar_one_or_none()
    return result

async def get_rank_by_name(session: AsyncSessionLocal, rank_name: str | Mapped[str]) -> Optional[Rank]:
    stmt = select(Rank).where(Rank.rank_name == rank_name)
    pre_result: ChunkedIteratorResult[Rank] = await session.execute(stmt)
    result: Rank = pre_result.scalar_one_or_none()
    return result


async def register_user(session: AsyncSessionLocal, username: str, tguserid: int) -> bool:
    tgusername = '@' + username
    if await get_user_by_tguserid(session, tguserid) is not None:
        return False

    date = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    date = date - timedelta(days=1)
    date = date.strftime('%Y-%m-%d %H:%M:%S')
    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

    user = User(
        # Main Stats
        # rank="Игрок",
        username=username,
        balance_main=25_000,
        balance_alt=0,
        last_bonus_time=date,
        last_mini_bonus_time=date,
        mini_bonus_count=0,
        bonus_count=0,
        roulette_zero_count=0,
        slot_777_count=0,
        is_admin=False,
        is_hidden=False,

        # Slavery
        your_owner="",
        your_slave="",
        is_immune=False,

        # Trades
        cur_trade_id=-1,
        is_in_trade=False,

        # Dices
        cur_dice_game_id=-1,

        # For the future
        is_worker=False,
        work_name="",

        # Tecnical stats
        tgusername=tgusername,
        tguserid=tguserid,
    )

    user_items = UserItems(
        items_list="{}",
        avatar_item="черви",

        ranks_list="1,",
        current_rank="1",

        tguserid=tguserid,
    )

    user_slavery = Slavery(
        owner_id=-1,
        slave_id=-1,
        start_time=date,
        last_payout_time=date,
        piggy_bank=0,
        last_withdrawal_time=date,
        tguserid=tguserid,
    )

    session.add(user)
    session.add(user_items)
    session.add(user_slavery)

    if str(tguserid) in ADMIN_IDs:
        user.is_admin = True
        if str(tguserid) == ADMIN_IDs[0]:
            await add_rank_to_user(session, "Владелец", tguserid)
            user_items.current_rank = '2'
        else:
            await add_rank_to_user(session, "Администратор", tguserid)
            user_items.current_rank = '3'


    await session.commit()
    return True


async def update_user(session: AsyncSessionLocal, stat_name: str, value: Any, tguserid: int | Mapped[int]) -> None:
    stmt = select(User).where(User.tguserid == tguserid)
    result: ChunkedIteratorResult[User] = await session.execute(stmt)
    user = result.scalar_one_or_none()
    try:
        if stat_name not in user.__dict__.keys():
            raise ValueError(f"{stat_name} is not a valid stat name")
        else:
            setattr(user, stat_name, value)
            await session.commit()
    except ValueError as e:
        print(f'Ошибка: {e}\n\nПроблема: {stat_name}')
        return


async def update_username(session: AsyncSessionLocal, username: str, tguserid: int | Mapped[int]) -> None:
    await update_user(session, "username", username, tguserid)


async def update_bonus(session: AsyncSessionLocal, tguserid: int, current_time: datetime) -> None:
    user = await get_user_by_id(session, tguserid)
    await update_user(session, "bonus_count", user.bonus_count + 1, tguserid)
    await update_user(session, "last_bonus_time", current_time, tguserid)


async def add_item(session: AsyncSessionLocal, item_name: str, item_type: str, path: str = None,
                       item_buy_price: int = None, item_sell_price: int = None) -> None:
    item = Item(
        item_name=item_name,
        item_path=path,
        item_type=item_type,
        item_buy_price=item_buy_price,
        item_sell_price=item_sell_price
    )

    session.add(item)
    await session.commit()


async def add_rank(session: AsyncSessionLocal, rank_name: str, rank_buy_price: int, rank_sell_price: int) -> None:
    rank = Rank(
        rank_name=rank_name,
        rank_buy_price=rank_buy_price,
        rank_sell_price=rank_sell_price
    )

    session.add(rank)
    await session.commit()


async def change_rank_console(session: AsyncSessionLocal, rank: str, tguserid: int | Mapped[int]) -> None:
    stmt = select(UserItems).where(UserItems.tguserid == tguserid)
    pre_result: ChunkedIteratorResult[UserItems] = await session.execute(stmt)
    result: UserItems = pre_result.scalar_one_or_none()

    result.current_rank = rank
    await session.commit()


async def change_rank(session: AsyncSessionLocal, rank: Rank, tguserid: int | Mapped[int]) -> None:
    stmt = select(UserItems).where(UserItems.tguserid == tguserid)
    pre_result: ChunkedIteratorResult[UserItems] = await session.execute(stmt)
    result: UserItems = pre_result.scalar_one_or_none()

    result.current_rank = str(rank.id)
    await session.commit()


async def get_existing_items_names(session: AsyncSessionLocal) -> list:
    stmt = select(Item.item_name)
    result: ChunkedIteratorResult[Item] = await session.execute(stmt)
    items = [item for item in result.scalars().all()]
    return items


async def get_items_by_names(session: AsyncSessionLocal, item_names: list[str]) -> list[Item]:
    stmt = select(Item).where(Item.item_name.in_(item_names))
    result: ChunkedIteratorResult[Item] = await session.execute(stmt)
    items = [item for item in result.scalars().all()]
    return items


async def add_item_to_user(session: AsyncSessionLocal, tguserid: int | Mapped[int], item_id: int | Mapped[int], count: int = 1) -> None:
    item = await get_item_by_id(session, item_id)

    if not item:
        raise ValueError(f'Item {item.id} does not exist in the database')

    user_items = await get_dict_user_items(session, tguserid)

    if item.item_name in user_items:
        user_items[item.item_name] += count
    else:
        user_items[item.item_name] = count

    stmt = update(UserItems).where(UserItems.tguserid == tguserid).values(items_list=json.dumps(user_items))
    await session.execute(stmt)
    await session.commit()


async def remove_item_from_user(session: AsyncSessionLocal, item_id: int | Mapped[int], tguserid: int | Mapped[int], count: int = 1) -> bool:
    item = await get_item_by_id(session, item_id)

    if not item:
        raise ValueError(f'Item {item.id} does not exist in the database')

    user_items = await get_dict_user_items(session, tguserid)
    item_name = item.item_name

    if item_name in user_items:
        # Проверяем, хватает ли предметов для удаления
        if user_items[item_name] >= count:
            user_items[item_name] -= count
            # Если количество стало 0, удаляем предмет из словаря
            if user_items[item_name] == 0:
                del user_items[item_name]
        else:
            logger.info(f'У пользователя {tguserid} недостаточно предметов "{item_name}"')
            return False
    else:
        logger.info(f'У пользователя {tguserid} нет предмета "{item_name}"')
        return False

    stmt = update(UserItems).where(UserItems.tguserid == tguserid).values(items_list=json.dumps(user_items))
    await session.execute(stmt)
    await session.commit()
    return True

async def update_items(session: AsyncSessionLocal, json_data: dict) -> None:
    stmt = delete(Item)
    await session.execute(stmt)
    await session.commit()

    for item_name, item_data in json_data.items():
        await add_item(
            session=session,
            item_name=item_name,
            item_type=item_data['type'],
            path=item_data.get('path'),
            item_buy_price=item_data.get('buy_price'),
            item_sell_price=item_data.get('sell_price')
        )

    await session.commit()

async def update_ranks(session: AsyncSessionLocal, json_data: dict) -> None:
    stmt = delete(Rank)
    await session.execute(stmt)
    await session.commit()

    for rank_name, rank_data in json_data.items():
        await add_rank(
            session=session,
            rank_name=rank_name,
            rank_buy_price=rank_data['buy_price'],
            rank_sell_price=rank_data.get('sell_price')
        )

    await session.commit()


async def make_admin(session: AsyncSessionLocal, tguserid: int) -> None:
    user = await get_user_by_tguserid(session, tguserid)
    user.is_admin = True
    await session.commit()


async def remove_admin(session: AsyncSessionLocal, tguserid: int) -> None:
    if tguserid in ADMIN_IDs:
        return

    user = await get_user_by_tguserid(session, tguserid)
    user.is_admin = False
    await session.commit()


async def delete_user(session: AsyncSessionLocal, tguserid: int) -> None:
    stmt = delete(User).where(User.tguserid == tguserid)
    await session.execute(stmt)
    stmt = delete(UserItems).where(UserItems.tguserid == tguserid)
    await session.execute(stmt)
    stmt = delete(Slavery).where(Slavery.tguserid == tguserid)
    await session.execute(stmt)

    await session.commit()


async def check_user_in(session: AsyncSessionLocal, tguserid: int | Mapped[int]) -> bool:
    stmt = select(User).where(User.tguserid == tguserid)
    result: ChunkedIteratorResult[User] = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def update_dice_game(session: AsyncSessionLocal, stat_name: str, value: Any, dice_id: int | Mapped[int]):
    stmt = select(Dice).where(Dice.id == dice_id)
    result: ChunkedIteratorResult[Dice] = await session.execute(stmt)
    dice = result.scalar_one_or_none()

    try:
        if stat_name not in dice.__dict__.keys():
            raise ValueError(f"{stat_name} is not a valid stat name")
        else:
            setattr(dice, stat_name, value)
            await session.commit()
    except ValueError as e:
        print(f'Ошибка: {e}\n\nПроблема: {stat_name}')
        return


async def delete_dice_game(session: AsyncSessionLocal, dice_id: int | Mapped[int]):
    stmt = delete(Dice).where(Dice.id == dice_id)
    await session.execute(stmt)
    await session.commit()


async def update_trade(session: AsyncSessionLocal, stat_name: str, value: Any, trade_id: int | Mapped[int]) -> None:
    stmt = select(Trade).where(Trade.id == trade_id)
    result: ChunkedIteratorResult[Trade] = await session.execute(stmt)
    trade = result.scalar_one_or_none()
    try:
        if stat_name not in trade.__dict__.keys():
            raise ValueError(f"{stat_name} is not a valid stat name")
        else:
            setattr(trade, stat_name, value)
            await session.commit()
    except ValueError as e:
        print(f'Ошибка: {e}\n\nПроблема: {stat_name}')
        return


async def delete_trade(session: AsyncSessionLocal, trade_id: int | Mapped[int]) -> None:
    stmt = delete(Trade).where(Trade.id == trade_id)
    await session.execute(stmt)
    await session.commit()


async def update_avatar(session: AsyncSessionLocal, tguserid: int | Mapped[int], avatar_item: str) -> None:
    stmt = update(UserItems).where(UserItems.tguserid == tguserid).values(avatar_item=avatar_item)
    await session.execute(stmt)
    await session.commit()
