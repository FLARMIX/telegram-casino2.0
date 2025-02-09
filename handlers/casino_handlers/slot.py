from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


@router.message(Command('slot'))
@router.message(Command('автомат'))
async def slot_machine(message: Message, bot: Bot):
    db = Database()
    scr = Scripts()

    user_id = message.from_user.id
    balance_main = db.get_user_stat(user_id, 'balance_main')
    username = db.get_user_stat(user_id, "username")
    tg_username = db.get_user_stat(user_id, "tgusername")[1:]
    formated_name = hlink(f'{username}', f'https://t.me/{tg_username}')
    user_channel_status = scr.check_channel_subscription(bot, user_id)
    command, amount = message.text.lower().split() if len(message.text.split()) > 1 else (message.text.split()[0], '50к')

    if not user_channel_status:
        await message.answer('Вы не подписаны на канал, подпишитесь на мой канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться на мой канал.',
                             reply_to_message_id=message.message_id)
        return

    if not db.check_user_in(user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register',
                             reply_to_message_id=message.message_id)
        return

    else:

        if amount in ['все', 'всё']:
            amount = str(balance_main)
        int_amount = scr.unformat_number(scr.amount_changer(amount))

        if int_amount <= 0:
            await message.answer("Сумма ставки должна быть больше 0!",
                                 reply_to_message_id=message.message_id)
            return

        if balance_main < int_amount:
            await message.answer(f'У вас недостаточно средств!\nВаш баланс {scr.amount_changer(balance_main)}',
                                 reply_to_message_id=message.message_id)
            return

        db.update_user('balance_main', balance_main - int_amount, user_id)

        dice = await message.answer_dice(emoji='🎰', reply_to_message_id=message.message_id)
        dice_value = dice.dice.value

        if dice_value == 64:
            db.update_user('balance_main', balance_main + int_amount * 35, user_id)
            current_balance = db.get_user_stat(user_id, 'balance_main')
            await message.answer(f'{formated_name}, 777?? Ставка 🤑x35🤑!!! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 35))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        elif dice_value == 43:
            db.update_user('balance_main', balance_main + int_amount * 15, user_id)
            current_balance = db.get_user_stat(user_id, 'balance_main')
            await message.answer(f'{formated_name}, Ставка x15🤑! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 15))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        elif dice_value == 22:
            db.update_user('balance_main', balance_main + int_amount * 10, user_id)
            current_balance = db.get_user_stat(user_id, 'balance_main')
            await message.answer(f'{formated_name}, Ставка x10! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 10))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        elif dice_value == 1:
            db.update_user('balance_main', balance_main + int_amount * 5, user_id)
            current_balance = db.get_user_stat(user_id, 'balance_main')
            await message.answer(f'{formated_name}, Ставка x5. Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 5))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        else:
            current_balance = db.get_user_stat(user_id, 'balance_main')
            await message.answer(f'{formated_name}, Вы проиграли '
                                 f'{scr.amount_changer(str(int_amount))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
