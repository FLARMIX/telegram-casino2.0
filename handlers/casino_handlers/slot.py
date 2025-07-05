from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import check_user_in, get_user_by_tguserid, update_user, get_user_stat
from handlers.init_router import router

from scripts.scripts import Scripts


@router.message(Command('slot'))
@router.message(Command('автомат'))
async def slot_machine(message: Message, bot: Bot, session: AsyncSession):
    scr = Scripts()

    user_id = message.from_user.id
    user_channel_status = await scr.check_channel_subscription(bot, user_id)
    command, amount = message.text.lower().split() if len(message.text.split()) > 1 else (message.text.split()[0], '50к')

    if not user_channel_status:
        await message.answer('Вы не подписаны на канал, подпишитесь на мой канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться на мой канал.',
                             reply_to_message_id=message.message_id)
        return

    if not await check_user_in(session, user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register',
                             reply_to_message_id=message.message_id)
        return

    else:
        user = await get_user_by_tguserid(session, user_id)
        tg_username = user.tgusername
        tg_username = tg_username[1:]
        balance_main = user.balance_main
        is_hidden = user.is_hidden
        username = user.username

        if is_hidden:
            formated_username = username
        else:
            formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

        if amount in ['все', 'всё']:
            amount = str(balance_main)
        int_amount = scr.unformat_number(scr.amount_changer(amount))

        if int_amount <= 0:
            await message.answer("Сумма ставки должна быть больше 0!",
                                 reply_to_message_id=message.message_id)
            return

        if balance_main < int_amount:
            await message.answer(f'У вас недостаточно средств!\nВаш баланс {scr.amount_changer(str(balance_main))}',
                                 reply_to_message_id=message.message_id)
            return

        await update_user(session, 'balance_main', balance_main - int_amount, user_id)

        dice = await message.answer_dice(emoji='🎰', reply_to_message_id=message.message_id)
        dice_value = dice.dice.value

        if dice_value == 64:
            await update_user(session, 'balance_main', balance_main + int_amount * 35, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, 777?? Ставка 🤑x35🤑!!! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 35))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        elif dice_value == 43:
            await update_user(session, 'balance_main', balance_main + int_amount * 15, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Ставка x15🤑! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 15))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        elif dice_value == 22:
            await update_user(session, 'balance_main', balance_main + int_amount * 10, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Ставка x10! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 10))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        elif dice_value == 1:
            await update_user(session, 'balance_main', balance_main + int_amount * 5, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Ставка x5. Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 5))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
        else:
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Вы проиграли '
                                 f'{scr.amount_changer(str(int_amount))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True)
