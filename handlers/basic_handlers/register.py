from aiogram.types import Message
from aiogram.filters import Command
from handlers.init_router import router
from database.database import Database


@router.message(Command('регистрация'))
@router.message(Command('register'))
async def register(message: Message):
    db = Database()
    user_id = message.from_user.id
    username = message.from_user.username
    if db.check_user_in(user_id):
        await message.answer('Вы уже зарегистрированы, приятной игры!'
                             '\nДля ознакомления с доступными коммандами введите /help',
                             reply_to_message_id=message.message_id)
    else:
        db.register_user(tguserid=user_id, username=username)
        await message.answer('Регистрация успешно пройдена, добро пожаловать!'
                             '\nДля получения помощи по командам введите /help',
                             reply_to_message_id=message.message_id)
