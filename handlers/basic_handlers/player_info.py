from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


@router.message(Command('инфо'))
@router.message(Command('info'))
async def info(message: Message):
    db = Database()
    scr = Scripts()
    user_id = message.from_user.id

    command, target_username = message.text.split()

    if not db.check_user_in(user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register',
                             reply_to_message_id=message.message_id)
        return

    try:
        target_id = db.get_user_id_by_tgusername(target_username)
    except TypeError:
        await message.answer(f'Пользователь с юзом "{target_username}" не найден.',
                             reply_to_message_id=message.message_id)
        return

    if db.check_user_in(target_id):
        tg_username = db.get_user_stat(target_id, "tgusername")[1:]
        username = db.get_user_stat(target_id, "username")
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')
        balance_main = str(db.get_user_stat(target_id, 'balance_main'))
        balance_alt = str(db.get_user_stat(target_id, 'balance_alt'))
        bonus_count = str(db.get_user_stat(target_id, 'bonus_count'))
        mini_bonus_count = str(db.get_user_stat(target_id, 'mini_bonus_count'))

        await message.answer(f'🎮 Кликуха игрока: {formated_username}\n'
                             f'💰 Его баланс: {scr.amount_changer(balance_main)}$\n'
                             f'💰 Его "Word Of Alternative Balance": {scr.amount_changer(balance_alt)}\n'
                             f'🎁 Кол-во его бонусов: {scr.amount_changer(bonus_count)}\n'
                             f'🤶🏻 Кол-во его мини-бонусов: {scr.amount_changer(mini_bonus_count)}',
                             reply_to_message_id=message.message_id, disable_web_page_preview=True)
