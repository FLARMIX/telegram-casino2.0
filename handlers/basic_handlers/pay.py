from aiogram import Bot, F
from aiogram.types import Message
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, check_user_in, get_user_by_tgusername, update_user
from handlers.init_router import router
from scripts.loggers import log

from scripts.scripts import Scripts


@router.message(F.text.lower().startswith(('передать', 'pay', '/передать', '/pay')))
@log("I doubt that there is a mistake here. (pay)")
async def pay(message: Message, bot: Bot, session: AsyncSession):
    scr = Scripts()

    user = await get_user_by_tguserid(session, message.from_user.id)
    balance_main = user.balance_main
    command, target_username, amount = message.text.split()

    if not await check_user_in(session, user.tguserid):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register',
                             reply_to_message_id=message.message_id)
        return

    if amount.lower() in ['всё', 'все']:
        int_amount = balance_main
    int_amount = int(scr.unformat_number(scr.amount_changer(amount)))

    if int_amount <= 0:
        await message.answer('Сумма перевода должна быть больше 0!',
                             reply_to_message_id=message.message_id)
        return

    try:
        target = await get_user_by_tgusername(session, target_username)
    except TypeError:
        await message.answer(f'Пользователь с юзом "{target_username}" не найден.',
                             reply_to_message_id=message.message_id)
        return

    if target.tguserid == user.tguserid:
        await message.answer('Вы не можете передать средства самому себе!',
                             reply_to_message_id=message.message_id)
        return

    tg_username = target.tgusername
    tg_username = tg_username[1:]

    user_is_hidden = user.is_hidden
    username = user.username

    target_is_hidden = target.is_hidden
    target_username = target.username

    if target_is_hidden:
        target_formated_username = target_username
    else:
        target_formated_username = hlink(f'{target.username}', f'https://t.me/{tg_username}')


    if user_is_hidden:
        user_formated_username = username
    else:
        user_formated_username = hlink(f'{user.username}', f'https://t.me/{user.tgusername[1:]}')

    target_balance = target.balance_main

    if balance_main < int_amount:
        await message.answer(f'У вас недостаточно средств. Ваш текущий баланс: {scr.amount_changer(str(balance_main))}',
                             reply_to_message_id=message.message_id)
        return

    await update_user(session, 'balance_main', balance_main - int_amount, user.tguserid)
    await update_user(session, 'balance_main', target_balance + int_amount, target.tguserid)

    text_for_user = f'Вы передали {scr.amount_changer(amount)}$ пользователю {target_formated_username}'
    text_for_target = f'Пользователь {user_formated_username} передал вам {scr.amount_changer(amount)}$'

    await message.answer(text_for_user, reply_to_message_id=message.message_id, disable_web_page_preview=True)

    await bot.send_message(int(str(target.tguserid)), text_for_target, disable_web_page_preview=True)
