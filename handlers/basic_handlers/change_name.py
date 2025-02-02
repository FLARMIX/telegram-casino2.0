from aiogram.types import Message
from aiogram.filters import Command

from handlers.init_router import router

from database.database import Database


@router.message(Command('ник'))
@router.message(Command('nickname'))
async def nickname(message: Message):
    db = Database()

    user_id = message.from_user.id

    if len(message.text.split()) <= 2:
        command, username = message.text.split()
    else:
        username = ' '.join(message.text.split()[1:])

    if len(username) > 20:
        await message.answer("Имя не может быть длиннее 20 символов!")
        return

    db.update_user("username", username, user_id)
    await message.answer(f"Вы успешно установили имя {username}!")
