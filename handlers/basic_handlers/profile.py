from aiogram.types import Message
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
    if not db.get_user_by_tgid(user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register')
        return

    tg_username = db.get_user_stat(user_id, "tgusername")[1:]
    username = db.get_user_stat(user_id, "username")
    formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')
    balance_main = str(db.get_user_stat(user_id, 'balance_main'))
    balance_alt = str(db.get_user_stat(user_id, 'balance_alt'))
    bonus_count = str(db.get_user_stat(user_id, 'bonus_count'))
    mini_bonus_count = str(db.get_user_stat(user_id, 'mini_bonus_count'))

    await message.answer(f'🎮 Ваша кликуха: {formated_username}\n'
                         f'💰 Баланс: {scr.amount_changer(balance_main)}$\n'
                         f'💰 "Word Of Alternative Balance": {scr.amount_changer(balance_alt)}\n'
                         f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
                         f'🤶🏻 Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}',
                         reply_to_message_id=message.message_id, disable_web_page_preview=True)
