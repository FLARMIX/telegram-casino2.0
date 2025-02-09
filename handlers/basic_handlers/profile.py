from io import BytesIO

from PIL import Image
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from handlers.init_router import router
from database.database import Database
from scripts.scripts import Scripts
from aiogram.utils.markdown import hlink


@router.message(Command('я'))
@router.message(Command('me'))
async def me(message: Message):
    db = Database()
    scr = Scripts()
    user_id = message.from_user.id
    username = message.from_user.username

    if not db.get_user_by_tgid(user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register')
        return

    if not db.get_user_stat(user_id, 'tgusername')[1:] == username:
        db.update_user('tgusername', '@' + username, user_id)

    tg_username = db.get_user_stat(user_id, "tgusername")[1:]
    username = db.get_user_stat(user_id, "username")
    formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')
    balance_main = str(db.get_user_stat(user_id, 'balance_main'))
    balance_alt = str(db.get_user_stat(user_id, 'balance_alt'))
    bonus_count = str(db.get_user_stat(user_id, 'bonus_count'))
    mini_bonus_count = str(db.get_user_stat(user_id, 'mini_bonus_count'))

    # Получаем аватар игрока
    avatar_item = db.get_user_avatar(user_id)
    avatar_path = db.get_item_path(avatar_item)

    # Получаем список предметов
    items = db.get_user_items(user_id)
    avatar_items = {item: count for item, count in items.items() if db.get_item_type(item) == "avatar"}
    property_items = {item: count for item, count in items.items() if db.get_item_type(item) != "avatar"}

    # Формируем текст профиля
    profile_text = (
        f'🎮 Ваша кликуха: {formated_username}\n'
        f'💰 Баланс: {scr.amount_changer(balance_main)}$\n'
        f'💰 "Word Of Alternative Balance": {scr.amount_changer(balance_alt)}\n'
        f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
        f'🤶🏻 Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}\n'
        f'🖼️ Аватар: {avatar_item}\n'
        f'🎒 Витринные предметы: {", ".join([f"{item} (x{count})" for item, count in avatar_items.items()])}\n'
        f'📦 Имущество: {", ".join([f"{item} (x{count})" for item, count in property_items.items()])}'
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
