from aiogram.types import Message
from aiogram.filters import Command
from handlers.init_router import router
from database.database import Database
from scripts.scripts import Scripts


@router.message(Command('set'))
@router.message(Command('сет'))
async def set(message: Message):
    db = Database()
    scr = Scripts()
    user_id = message.from_user.id
    is_you = False
    if db.get_user_stat(user_id, 'is_admin'):
        command, which_balance, target_username, amount = message.text.split()
        amount = scr.unformat_number(scr.amount_changer(amount))
        if target_username.lower() == 'я':
            target_user_id = user_id
            is_you = True
        else:
            target_user_id = db.get_user_id_by_tgusername(target_username)
            if not target_user_id:
                await message.answer(f"Пользователь с ником '{target_username}' не найден.",
                                     reply_to_message_id=message.message_id)
                return

        if which_balance == "m":
            balance_type = "balance_main"
            msg = "$"
        elif which_balance == "a":
            balance_type = "balance_alt"
            msg = ' "Word Of Alternative Balance"'
        else:
            await message.answer("Используйте /set m для основного баланса или /set a для альтернативного.",
                                 reply_to_message_id=message.message_id)
            return

        if target_user_id:
            db.update_user(balance_type, int(amount), target_user_id)
            if is_you:
                await message.answer(f"Вы установили себе {scr.amount_changer((str(amount)))}{msg}")
            else:
                await message.answer(f"Вы установили {scr.amount_changer((str(amount)))}{msg} пользователю "
                                     f"{target_username}",
                                     reply_to_message_id=message.message_id)
