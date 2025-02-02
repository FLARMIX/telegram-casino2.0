from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


@router.message(Command('передать'))
@router.message(Command('pay'))
async def pay(message: Message):
    db = Database()
    scr = Scripts()

    user_id = message.from_user.id
    balance_main = db.get_user_stat(user_id, 'balance_main')
    command, target_username, amount = message.text.split()

    if not db.check_user_in(user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register',
                             reply_to_message_id=message.message_id)
        return

    if amount.lower() in ['всё', 'все']:
        int_amount = balance_main
    int_amount = scr.unformat_number(scr.amount_changer(amount))

    if int_amount <= 0:
        await message.answer('Сумма перевода должна быть больше 0!',
                             reply_to_message_id=message.message_id)
        return

    try:
        target_id = db.get_user_id_by_tgusername(target_username)
    except TypeError:
        await message.answer(f'Пользователь с юзом "{target_username}" не найден.',
                             reply_to_message_id=message.message_id)
        return

    target_balance = db.get_user_stat(target_id, 'balance_main')
    tg_username = db.get_user_stat(target_id, "tgusername")[1:]
    username = db.get_user_stat(target_id, "username")
    formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

    if balance_main < int_amount:
        await message.answer(f'У вас недостаточно средств. Ваш текущий баланс: {scr.amount_changer(balance_main)}',
                             reply_to_message_id=message.message_id)
        return

    db.update_user('balance_main', balance_main - int_amount, user_id)
    db.update_user('balance_main', target_balance + int_amount, target_id)

    await message.answer(f'Вы передали {scr.amount_changer(amount)}$ пользователю {formated_username}',
                         reply_to_message_id=message.message_id)
