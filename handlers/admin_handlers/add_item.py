from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


@router.message(Command("add_item"))
async def add_item(message: Message):
    db = Database()
    user_id = message.from_user.id

    # Проверка, является ли пользователь администратором
    if not db.get_user_stat(user_id, "is_admin"):
        await message.answer("Вы не являетесь администратором.", reply_to_message_id=message.message_id)
        return

    # Разбор команды
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Использование: /add_item @username предмет [количество]",
                             reply_to_message_id=message.message_id)
        return

    target_username = args[1]
    item = args[2]
    quantity = int(args[3]) if len(args) > 3 else 1  # По умолчанию количество = 1

    # Получаем ID целевого пользователя
    try:
        target_id = db.get_user_id_by_tgusername(target_username)
    except TypeError:
        await message.answer(f"Пользователь с ником '{target_username}' не найден.",
                             reply_to_message_id=message.message_id)
        return

    # Добавляем предметы
    try:
        for _ in range(quantity):
            db.add_item_to_user(target_id, item)
    except ValueError as e:
        await message.answer(str(e), reply_to_message_id=message.message_id)
        return

    # Получаем обновленный список предметов пользователя
    users_items = db.get_user_items(target_id)

    # Форматируем имя пользователя
    tg_username = db.get_user_stat(target_id, "tgusername")[1:]
    username = db.get_user_stat(target_id, "username")
    formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

    # Отправляем сообщение об успешной выдаче
    await message.answer(
        f"Предмет '{item}' (x{quantity}) успешно добавлен к пользователю {formated_username}.\n"
        f"Теперь у него {users_items.get(item, 0)} предметов '{item}'.",
        reply_to_message_id=message.message_id,
        disable_web_page_preview=True
    )
