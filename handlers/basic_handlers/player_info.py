from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, check_user_in, get_user_by_tgusername, get_user_avatar, \
    get_item_by_name, get_dict_user_items
from database.models import ItemType

from handlers.init_router import router

from scripts.loggers import log
from scripts.media_cache import file_cache_original
from scripts.scripts import Scripts

from aiogram.utils.markdown import hlink


@router.message(F.text.lower().startswith(('инфо', 'info', '/инфо', '/info')))
@log("Info command logging...")
async def info(message: Message, session: AsyncSession):
    scr = Scripts()
    user = await get_user_by_tguserid(session, message.from_user.id)

    command, target_username = message.text.split()

    if not await check_user_in(session, user.tguserid):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register',
                             reply_to_message_id=message.message_id)
        return


    target = await get_user_by_tgusername(session, target_username)
    if not target:
        await message.answer(f'Пользователь с юзом "{target_username}" не найден.',
                             reply_to_message_id=message.message_id)


    if await check_user_in(session, target.tguserid):
        tg_username = target.tgusername
        tg_username = tg_username[1:]

        is_hidden = target.is_hidden
        username = target.username

        if is_hidden:
            formated_username = username
        else:
            formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

        balance_main = str(target.balance_main)
        balance_alt = str(target.balance_alt)
        bonus_count = str(target.bonus_count)
        mini_bonus_count = str(target.mini_bonus_count)
        roulette_zero_count = str(target.roulette_zero_count)
        slot_777_count = str(target.slot_777_count)
        rank = str(target.rank)

        avatar_item = await get_user_avatar(session, target.tguserid)
        item_obj = await get_item_by_name(session, avatar_item)
        avatar_path = str(item_obj.item_path)

        # Получаем список предметов
        items = await get_dict_user_items(session, target.tguserid)
        avatar_items = dict()
        property_items = dict()

        for item, count in items.items():
            item_obj = await get_item_by_name(session, item)
            if item_obj.item_type == ItemType.AVATAR:
                avatar_items[item] = count

        for item, count in items.items():
            item_obj = await get_item_by_name(session, item)
            if item_obj.item_type != ItemType.AVATAR:  # TODO: != ItemType.AVATAR <- костыль, нужно исправить в будущем.
                property_items[item] = count

        # Формируем текст профиля
        profile_text = (
            f'🎮 Кликуха: {formated_username}\n'
            f'💰 Баланс: {scr.amount_changer(balance_main)}$\n'
            f'💦 Конча: {scr.amount_changer(balance_alt)}\n'
            f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
            f'✨ Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}\n'
            f'🎯 Кол-во "0" в рулетке: {scr.amount_changer(roulette_zero_count)}\n'
            f'🎰 Кол-во "777" в слотах: {scr.amount_changer(slot_777_count)}\n'
            f'🖼️ Аватар: {avatar_item}\n'
            f'🎒 Витринные предметы: {", ".join([f"{item} (x{count})" for item, count in avatar_items.items()])}\n'
            f'📦 Имущество: {", ".join([f"{item} (x{count})" for item, count in property_items.items()])}\n'
            f'💻 Ранг: {rank}'
        )

        input_file = file_cache_original.get(avatar_path)

        # Отправляем фото аватара и текст профиля
        if avatar_path:
            await message.answer_photo(
                photo=input_file,
                caption=profile_text,
                reply_to_message_id=message.message_id
            )
        else:
            await message.answer(profile_text, reply_to_message_id=message.message_id)
