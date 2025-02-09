from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command
from handlers.init_router import router
from database.database import Database
from scripts.scripts import Scripts


@router.message(Command('регистрация'))
@router.message(Command('register'))
async def register(message: Message, bot: Bot):
    db = Database()
    scr = Scripts()
    user_id = message.from_user.id
    username = message.from_user.username
    user_channel_status = scr.check_channel_subscription(bot, user_id)

    if not user_channel_status:
        await message.answer('Вы не подписаны на канал, подпишитесь на мой канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться на мой канал.',
                             reply_to_message_id=message.message_id)
        return

    if db.check_user_in(user_id):
        await message.answer('Вы уже зарегистрированы, приятной игры!'
                             '\nДля ознакомления с доступными коммандами введите /help',
                             reply_to_message_id=message.message_id)
    else:
        db.register_user(tguserid=user_id, username=username)
        await message.answer('Регистрация успешно пройдена, добро пожаловать!'
                             '\nДля получения помощи по командам введите /help',
                             reply_to_message_id=message.message_id)
