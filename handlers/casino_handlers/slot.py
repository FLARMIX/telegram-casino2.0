import re

from aiogram import Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from config import Bot_username
from database.methods import check_user_in, get_user_by_tguserid, update_user, get_user_stat
from handlers.init_router import router
from scripts.loggers import log

from scripts.scripts import Scripts


@router.message(F.text.regexp(f'^/?(автомат|слот|слоты|slot|slot@{Bot_username})(\s|$)', flags=re.IGNORECASE))
@log("Slot is used - I'm logged!")
async def slot_machine(message: Message, bot: Bot, session: AsyncSession, state: FSMContext):
    scr = Scripts()

    user_id = message.from_user.id
    user_channel_status = await scr.check_channel_subscription(bot, user_id)
    message_text = message.text.lower().split()
    if len(message_text) < 2:
        await message.answer('Неверный формат команды! Пример:\n\n/slot 9000\nслоты 100к', reply_to_message_id=message.message_id)
        return
    else:
        amount = message_text[1]

    if not user_channel_status:
        await message.answer('Вы не подписаны на канал, подпишитесь на канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться.',
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

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Крутить!', callback_data='repeat_slot_bet')]
        ])

        await update_user(session, 'balance_main', balance_main - int_amount, user_id)

        dice = await message.answer_dice(emoji='🎰', reply_to_message_id=message.message_id)
        dice_value = dice.dice.value

        if dice_value == 64:
            await update_user(session, 'balance_main', balance_main + int_amount * 30, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')

            current_777_count = user.slot_777_count
            await update_user(session, 'slot_777_count', current_777_count + 1, user_id)

            await message.answer(f'{formated_username}, 777?? Ставка 🤑x30🤑!!! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 30))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True, reply_markup=keyboard)
        elif dice_value == 43:
            await update_user(session, 'balance_main', balance_main + int_amount * 15, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Ставка x15🤑! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 15))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True, reply_markup=keyboard)
        elif dice_value == 22:
            await update_user(session, 'balance_main', balance_main + int_amount * 10, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Ставка x10! Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 10))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True, reply_markup=keyboard)
        elif dice_value == 1:
            await update_user(session, 'balance_main', balance_main + int_amount * 5, user_id)
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Ставка x5. Вы выиграли '
                                 f'{scr.amount_changer(str(int_amount * 5))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True, reply_markup=keyboard)
        else:
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f'{formated_username}, Вы проиграли '
                                 f'{scr.amount_changer(str(int_amount))}$!\n'
                                 f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                                 reply_to_message_id=message.message_id, disable_web_page_preview=True, reply_markup=keyboard)

        await state.update_data(int_amount=int_amount, user_id=user_id)

@router.callback_query(F.data == "repeat_slot_bet")
async def repeat_slot_bet(callback: CallbackQuery, session: AsyncSession, state: FSMContext):

    user_id = callback.from_user.id
    user = await get_user_by_tguserid(session, user_id)
    scr = Scripts()

    data = await state.get_data()
    if "user_id" not in data or data["user_id"] != user_id:
        await callback.answer("Это не ваша кнопка!", show_alert=True)
        return

    int_amount = data["int_amount"]
    tg_username = user.tgusername
    tg_username = tg_username[1:]
    balance_main = user.balance_main
    is_hidden = user.is_hidden
    username = user.username

    if balance_main < int_amount:
        await callback.answer(f"У вас недостаточно средств! Ваш баланс: {scr.amount_changer(balance_main)}\n"
                              f"Сумма ставки: {scr.amount_changer(int_amount)}", show_alert=True)
        return

    if is_hidden:
        formated_username = username
    else:
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Крутить!', callback_data='repeat_slot_bet')]
    ])

    await update_user(session, 'balance_main', balance_main - int_amount, user_id)

    dice = await callback.message.answer_dice(emoji='🎰', reply_to_message_id=callback.message.message_id)
    dice_value = dice.dice.value

    if dice_value == 64:
        await update_user(session, 'balance_main', balance_main + int_amount * 30, user_id)
        current_balance = await get_user_stat(session, user_id, 'balance_main')

        current_777_count = user.slot_777_count
        await update_user(session, 'slot_777_count', current_777_count + 1, user_id)

        await callback.message.answer(f'{formated_username}, 777?? Ставка 🤑x30🤑!!! Вы выиграли '
                             f'{scr.amount_changer(str(int_amount * 30))}$!\n'
                             f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                             reply_to_message_id=callback.message.message_id, disable_web_page_preview=True,
                             reply_markup=keyboard)
    elif dice_value == 43:
        await update_user(session, 'balance_main', balance_main + int_amount * 15, user_id)
        current_balance = await get_user_stat(session, user_id, 'balance_main')
        await callback.message.answer(f'{formated_username}, Ставка x15🤑! Вы выиграли '
                             f'{scr.amount_changer(str(int_amount * 15))}$!\n'
                             f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                             reply_to_message_id=callback.message.message_id, disable_web_page_preview=True,
                             reply_markup=keyboard)
    elif dice_value == 22:
        await update_user(session, 'balance_main', balance_main + int_amount * 10, user_id)
        current_balance = await get_user_stat(session, user_id, 'balance_main')
        await callback.message.answer(f'{formated_username}, Ставка x10! Вы выиграли '
                             f'{scr.amount_changer(str(int_amount * 10))}$!\n'
                             f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                             reply_to_message_id=callback.message.message_id, disable_web_page_preview=True,
                             reply_markup=keyboard)
    elif dice_value == 1:
        await update_user(session, 'balance_main', balance_main + int_amount * 5, user_id)
        current_balance = await get_user_stat(session, user_id, 'balance_main')
        await callback.message.answer(f'{formated_username}, Ставка x5. Вы выиграли '
                             f'{scr.amount_changer(str(int_amount * 5))}$!\n'
                             f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                             reply_to_message_id=callback.message.message_id, disable_web_page_preview=True,
                             reply_markup=keyboard)
    else:
        current_balance = await get_user_stat(session, user_id, 'balance_main')
        await callback.message.answer(f'{formated_username}, Вы проиграли '
                             f'{scr.amount_changer(str(int_amount))}$!\n'
                             f'Ваш баланс: {scr.amount_changer(str(current_balance))}$',
                             reply_to_message_id=callback.message.message_id, disable_web_page_preview=True,
                             reply_markup=keyboard)

    await state.update_data(int_amount=int_amount, user_id=user_id)

