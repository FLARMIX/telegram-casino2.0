from io import BytesIO

from PIL import Image
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDs
from database.methods import get_user_by_tguserid, check_user_in, get_user_by_tgusername, get_user_avatar, \
    get_item_by_name, get_user_items
from database.models import ItemType
from handlers.init_router import router
from scripts.scripts import Scripts
from aiogram.utils.markdown import hlink


@router.message(Command('инфо'))
@router.message(Command('info'))
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
        rank = str(target.rank)

        avatar_item = await get_user_avatar(session, target.tguserid)
        item_obj = await get_item_by_name(session, avatar_item)
        avatar_path = str(item_obj.item_path)

        # Получаем список предметов
        items = await get_user_items(session, target.tguserid)
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
            f'🎮 Ваша кликуха: {formated_username}\n'
            f'💰 Баланс: {scr.amount_changer(balance_main)}$\n'
            f'💰 "Word Of Alternative Balance": {scr.amount_changer(balance_alt)}\n'
            f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
            f'🤶🏻 Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}\n'
            f'🖼️ Аватар: {avatar_item}\n'
            f'🎒 Витринные предметы: {", ".join([f"{item} (x{count})" for item, count in avatar_items.items()])}\n'
            f'📦 Имущество: {", ".join([f"{item} (x{count})" for item, count in property_items.items()])}\n'
            f'💻 Ранг: {rank}'
        )

        image = Image.new('RGB', (250, 250), (255, 255, 255))

        item_img = Image.open(avatar_path).resize((250, 250))
        image.paste(item_img, (0, 0))

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # Получаем байты из BytesIO
        image_bytes = img_byte_arr.getvalue()

        # Создаем BufferedInputFile из байтов
        input_file = BufferedInputFile(image_bytes, filename="avatars.png")

        # Отправляем фото аватара и текст профиля
        if avatar_path:
            await message.answer_photo(
                photo=input_file,
                caption=profile_text,
                reply_to_message_id=message.message_id
            )
        else:
            await message.answer(profile_text, reply_to_message_id=message.message_id)
