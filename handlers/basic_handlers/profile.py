from aiogram import F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import Bot_username
from database.SQLmodels import Rank
from database.methods import get_user_by_tguserid, update_user, get_item_by_name, get_user_avatar, get_dict_user_items, \
    get_items_by_names, get_user_rank
from database.models import ItemType

from handlers.init_router import router

from scripts.loggers import log
from scripts.media_cache import file_cache_original
from scripts.scripts import Scripts

from aiogram.utils.markdown import hlink


@router.message(F.text.lower().in_(['я', 'me', '/я', '/me', f'/me@{Bot_username}']))
@log('Logging the ME command...')
async def me(message: Message, session: AsyncSession):
    scr = Scripts()
    user_id = message.from_user.id
    username = message.from_user.username

    if not await get_user_by_tguserid(session, user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register')
        return

    user = await get_user_by_tguserid(session, message.from_user.id)
    is_username = user.tgusername
    if not is_username[1:] == username:
        await update_user(session, 'tgusername', '@' + username, user.tguserid)

    tg_username = user.tgusername
    tg_username = tg_username[1:]

    is_hidden = user.is_hidden
    username = user.username

    if is_hidden:
        formated_username = username
    else:
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

    balance_main = str(user.balance_main)
    balance_alt = str(user.balance_alt)
    bonus_count = str(user.bonus_count)
    mini_bonus_count = str(user.mini_bonus_count)
    roulette_zero_count = str(user.roulette_zero_count)
    slot_777_count = str(user.slot_777_count)
    rank = await get_user_rank(session, user_id)

    if isinstance(rank, Rank):
        rank_name = rank.rank_name
    else:
        rank_name = rank

    # Получаем аватар игрока
    avatar_item_name = await get_user_avatar(session, user.tguserid)
    avatar_item = await get_item_by_name(session, avatar_item_name)
    avatar_path = avatar_item.item_path if avatar_item else None

    # Предметы
    user_items = await get_dict_user_items(session, user.tguserid)
    all_item_names = list(user_items.keys())
    item_objects = await get_items_by_names(session, all_item_names)
    item_map = {item.item_name: item for item in item_objects}

    avatar_items = {}
    property_items = {}
    for name, count in user_items.items():
        obj = item_map.get(name)
        if not obj:
            continue
        (avatar_items if obj.item_type == ItemType.AVATAR else property_items)[name] = count

    # Формируем текст профиля
    profile_text = (
        f'🎮 Ваша кликуха: {formated_username}\n'
        f'💰 Баланс: {scr.amount_changer(balance_main)}$\n'
        f'💦 Конча: {scr.amount_changer(balance_alt)}\n'
        f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
        f'✨ Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}\n'
        f'🎯 Кол-во "0" в рулетке: {scr.amount_changer(roulette_zero_count)}\n'
        f'🎰 Кол-во "777" в слотах: {scr.amount_changer(slot_777_count)}\n'
        f'🖼 Аватар: {avatar_item.item_name}\n'
        f'🎒 Витринные предметы: {", ".join([f"{item} (x{count})" for item, count in avatar_items.items()])}\n'
        f'📦 Имущество: {", ".join([f"{item} (x{count})" for item, count in property_items.items()])}\n'
        f'💻 Ранг: {rank_name}'
    )

    input_file = file_cache_original.get(avatar_path) if avatar_path else None

    # Отправляем фото аватара и текст профиля
    if input_file:
        await message.answer_photo(
            photo=input_file,
            caption=profile_text,
            reply_to_message_id=message.message_id,
        )
    else:
        await message.answer(profile_text, reply_to_message_id=message.message_id, disable_web_page_preview=True)
