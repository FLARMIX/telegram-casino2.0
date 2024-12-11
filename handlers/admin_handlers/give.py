from aiogram.types import Message
from aiogram.filters import Command
from handlers.init_router import router
from database.database import Database
from scripts.scripts import Scripts


@router.message(Command('give'))
async def balance_command(message: Message):
    db = Database()
    scr = Scripts()
    user_id = message.from_user.id
    if db.get_user_stat(user_id, "is_admin"):
        command, which_balance, target_username, amount = message.text.split()
        amount = scr.unformat_number(scr.amount_changer(amount))
        target_user_id = db.get_user_id_by_tgusername(target_username)
        if which_balance == "m":
            balance_type = "balance_main"
            msg = "$"
        elif which_balance == "a":
            balance_type = "balance_alt"
            msg = ' "Word Of Alternative Balance"'
        else:
            await message.answer("Используйте /give m для основного баланса или /give a для альтернативного.")
            return

        if target_user_id:
            current_balance = db.get_user_stat(target_user_id, balance_type)
            db.update_user(balance_type, current_balance + int(amount), target_user_id)
            await message.answer(f"Выдано {scr.amount_changer(str(amount))}{msg} пользователю {target_username}")
