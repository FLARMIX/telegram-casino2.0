from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


@router.message(Command("рулетка"))
@router.message(Command("roulette"))
async def roulette(message: Message):
    db = Database()
    scr = Scripts()

    command, stack, amount = message.text.lower().split()

    user_id = message.from_user.id
    balance_main = db.get_user_stat(user_id, "balance_main")
    username = db.get_user_stat(user_id, "username")
    tg_username = db.get_user_stat(user_id, "tgusername")[1:]
    formated_name = hlink(f'{username}', f'https://t.me/{tg_username}')

    if not db.check_user_in(user_id):
        await message.answer("Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register",
                             reply_to_message_id=message.message_id)
        return
    else:

        if amount in ['все', 'всё']:
            amount = str(balance_main)

        int_amount = scr.unformat_number(scr.amount_changer(amount))

        if balance_main < int_amount:
            await message.answer("У вас недостаточно средств!")
            return

        db.update_user("balance_main", balance_main - int_amount, user_id)

        if stack in ['черное', 'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт']:
            status, number = scr.roulette_randomizer(stack)
            current_stack = scr.pic_color(number)
            print(status, number, current_stack)
            if status:
                before_balance = db.get_user_stat(user_id, "balance_main")
                db.update_user('balance_main', before_balance + int_amount * 2, user_id)
                current_balance = db.get_user_stat(user_id, "balance_main")

                await message.answer(f"{formated_name}, {number} - {current_stack.capitalize()}! Ставка x2 "
                                     f"{scr.randomize_emoji(win=True)}, вы выиграли "
                                     f"{scr.amount_changer(str(int_amount * 2))}$"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
                db.update_user("balance_main", balance_main + int_amount, user_id)
            else:
                current_balance = db.get_user_stat(user_id, 'balance_main')
                await message.answer(f"{formated_name}, {number} - {current_stack.capitalize()}! Вы проиграли "
                                     f"{scr.amount_changer(str(int_amount))}$ {scr.randomize_emoji(win=False) * 2}"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
        elif stack in ['зеро']:
            status, number = scr.roulette_randomizer(stack)
            current_stack = scr.pic_color(number)
            print(status, number, current_stack)
            if status:
                before_balance = db.get_user_stat(user_id, "balance_main")
                db.update_user('balance_main', before_balance + int_amount * 36, user_id)
                current_balance = db.get_user_stat(user_id, "balance_main")

                await message.answer(f"{formated_name}, {number} - {current_stack.capitalize()}! Ставка x36🤑!!! "
                                     f"вы выиграли "
                                     f"{scr.amount_changer(str(int_amount * 36))}$"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
            else:
                current_balance = db.get_user_stat(user_id, 'balance_main')
                await message.answer(f"{formated_name}, {number} - {current_stack.capitalize()}! Вы проиграли "
                                     f"{scr.amount_changer(str(int_amount))}$ {scr.randomize_emoji(win=False) * 2}"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
        else:
            await message.answer(f"Ошибка! Неправильно указан стек. Вы можете использовать 'черное', "
                                 f"'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт' или 'зеро'.",
                                 reply_to_message_id=message.message_id)
