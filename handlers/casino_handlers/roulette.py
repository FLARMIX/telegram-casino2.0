from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, get_user_stat, check_user_in, update_user
from handlers.init_router import router

from scripts.scripts import Scripts


@router.message(Command("рулетка"))
@router.message(Command("roulette"))
async def roulette(message: Message, bot: Bot, session: AsyncSession):
    scr = Scripts()

    command, stack, amount = message.text.lower().split()
    user = await get_user_by_tguserid(session, message.from_user.id)
    user_id = user.tguserid

    tg_username = await get_user_stat(session, user_id, "tgusername")
    tg_username = tg_username[1:]

    balance_main = user.balance_main
    is_hidden = user.is_hidden
    username = user.username

    if is_hidden:
        formated_username = username
    else:
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

    user_channel_status = await scr.check_channel_subscription(bot, user_id)

    if not user_channel_status:
        await message.answer('Вы не подписаны на канал, подпишитесь на мой канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться на мой канал.',
                             reply_to_message_id=message.message_id)
        return

    if not await check_user_in(session, user_id):
        await message.answer("Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register",
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
            await message.answer(f"У вас недостаточно средств!\nВаш баланс {scr.amount_changer(str(balance_main))}",
                                 reply_to_message_id=message.message_id)
            return

        await update_user(session, "balance_main", balance_main - int_amount, user_id)

        if stack in ['черное', 'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт']:
            status, number = scr.roulette_randomizer(stack)
            current_stack = scr.pic_color(number)
            print(status, number, current_stack)
            if status:
                before_balance = await get_user_stat(session, user_id, "balance_main")
                await update_user(session, 'balance_main', before_balance + int_amount * 2, user_id)
                current_balance = await get_user_stat(session, user_id, "balance_main")

                await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Ставка x2 "
                                     f"{scr.randomize_emoji(win=True)}, вы выиграли "
                                     f"{scr.amount_changer(str(int_amount * 2))}$"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
                await update_user(session, "balance_main", balance_main + int_amount, user_id)
            else:
                current_balance = await get_user_stat(session, user_id, 'balance_main')
                await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Вы проиграли "
                                     f"{scr.amount_changer(str(int_amount))}$ {scr.randomize_emoji(win=False) * 2}"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
        elif stack in ['зеро']:
            status, number = scr.roulette_randomizer(stack)
            current_stack = scr.pic_color(number)
            print(status, number, current_stack)
            if status:
                before_balance = await get_user_stat(session, user_id, "balance_main")
                await update_user(session, 'balance_main', before_balance + int_amount * 36, user_id)
                current_balance = await get_user_stat(session, user_id, "balance_main")

                await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Ставка x36🤑!!! "
                                     f"вы выиграли "
                                     f"{scr.amount_changer(str(int_amount * 36))}$"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
            else:
                current_balance = await get_user_stat(session, user_id, 'balance_main')
                await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Вы проиграли "
                                     f"{scr.amount_changer(str(int_amount))}$ {scr.randomize_emoji(win=False) * 2}"
                                     f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                     disable_web_page_preview=True, reply_to_message_id=message.message_id)
        else:
            await message.answer(f"Ошибка! Неправильно указан стек. Вы можете использовать 'черное', "
                                 f"'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт' или 'зеро'.",
                                 reply_to_message_id=message.message_id)
