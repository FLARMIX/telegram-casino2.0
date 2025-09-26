import logging
from datetime import datetime, timedelta

from aiogram import Bot, F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from database.SQLmodels import User, Trade, Item
from database.methods import get_user_by_tguserid, get_user_by_tgusername, create_trade, update_user, \
    delete_trade, update_trade, get_trade_by_trade_id, get_user_items, get_item_by_id
from database.models import TradeStatus
from handlers.init_router import router

from scripts.scripts import Scripts
from scripts.loggers import log


logger = logging.getLogger(__name__)



class TradeStates(StatesGroup):
    entering_quantity_of_money = State()
    entering_quantity_of_items = State()

    waiting_confirmation = State()


class PaginationCallback(CallbackData, prefix="pagination"):
    action: str
    page: int

def create_pagination_keyboard(items: list[Item], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    start_index = page * items_per_page
    end_index = start_index + items_per_page
    current_items = items[start_index:end_index]

    for item in current_items:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=item.item_name, callback_data=f"item_{item.id}")])

    navigation_buttons = []
    total_pages = (len(items) + items_per_page - 1) // items_per_page

    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=PaginationCallback(action="trade_command_previous", page=page - 1).pack()
            )
        )

    if page < total_pages - 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=PaginationCallback(action="trade_command_next", page=page + 1).pack()
            )
        )


    if navigation_buttons:
        keyboard.inline_keyboard.append(navigation_buttons)

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data="trade_back_to_offer_type")])

    return keyboard


def format_offer_text(user, other_user, trade, is_first_user, scr, is_symbol: bool = True):
    if is_first_user:
        own_offer = trade.first_user_offer
        own_confirm = trade.first_user_confirm
        own_offer_type = trade.first_user_offer_type
        other_offer = trade.second_user_offer
        other_confirm = trade.second_user_confirm
    else:
        own_offer = trade.second_user_offer
        own_confirm = trade.second_user_confirm
        own_offer_type = trade.second_user_offer_type
        other_offer = trade.first_user_offer
        other_confirm = trade.first_user_confirm



    if is_symbol:
        own_symbol = '✅' if own_confirm else '❌'
        other_symbol = '✅' if other_confirm else '❌'
    else:
        own_symbol = ''
        other_symbol = ''

    other_username = hlink(other_user.username, f'https://t.me/{other_user.tgusername[1:]}')

    if own_offer_type == 'money':
        base_text = f"{own_symbol}Твоё предложение:\n•{scr.amount_changer(str(own_offer))}$\n\n{other_symbol}Предложение {other_username}:\n"
    elif own_offer_type == 'empty':
        base_text = f"{own_symbol}Твоё предложение:\n•(<i>пусто</i>)\n\n{other_symbol}Предложение {other_username}:\n"
    elif own_offer_type == 'items':
        base_text = f"{own_symbol}Твоё предложение:\n•{own_offer}\n\n{other_symbol}Предложение {other_username}:\n"

    if other_offer == 'none':
        second_part = '•(<i>пусто</i>)'
    else:
        offer_type = trade.second_user_offer_type if is_first_user else trade.first_user_offer_type
        if offer_type == 'money':
            second_part = f'•{scr.amount_changer(str(other_offer))}$'
        elif offer_type == 'items':
            second_part = f'•{other_offer}'
        elif offer_type == 'empty':
            second_part = '•(<i>пусто</i>)'
        else:
            second_part = '•(<i>пусто</i>)'

    return base_text + second_part

async def get_trade_data(session, trade_id):
    trade = await get_trade_by_trade_id(session, trade_id)
    first_user = await get_user_by_tguserid(session, trade.first_user_id)
    second_user = await get_user_by_tguserid(session, trade.second_user_id)
    return trade, first_user, second_user


@router.message(F.text.lower().startswith(('трейд', 'trade', '/трейд', '/trade')))
@log("Trade logging... Maybe there is error?")
async def trade(message: Message, bot: Bot, session: AsyncSession):
    scr = Scripts()
    user_id = message.from_user.id
    message_text = message.text.split()
    message_len = len(message_text)

    user = await get_user_by_tguserid(session, user_id)
    user_trade_id = user.cur_trade_id

    if not await scr.check_registered(user, message):
        return

    if message.chat.type != 'private':
        await message.answer('💼 Эта команда доступна только в личных сообщениях с ботом.',
                             reply_to_message_id=message.message_id)
        return

    if message_len != 2:
        await message.answer(
            'Используй:\n'
            '<i>/trade</i> <b>@имя_пользователя</b>'
            '\n\n💡Пример:'
            '\n\n<i>/trade</i> <b>@FLARMIX</b>'
            '\n<i>/трейд</i> <b>@FLARMIX</b>',
            parse_mode='HTML'
        )
        return

    target = await get_user_by_tgusername(session, message_text[1])
    targe_trade_id = target.cur_trade_id

    if not target:
        await message.answer('Пользователь не найден, проверьте правильность введенного имени пользователя.',
                             reply_to_message_id=message.message_id)
        return

    if target.tguserid == user.tguserid:
        await message.answer('Вы не можете обменяться с собой!',
                             reply_to_message_id=message.message_id)
        return

    if user_trade_id != -1:
        await message.answer('Вы уже отправили запрос на обмен, сначала завершите предыдущий.',
                             reply_to_message_id=message.message_id)
        return

    if targe_trade_id != -1:
        await message.answer('Пользователь уже отправил запрос на обмен, попробуйте позже.',
                             reply_to_message_id=message.message_id)
        return

    keyboard_for_target = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Принять', callback_data=f'trade_confirm'),
            InlineKeyboardButton(text='❌ Отклонить', callback_data=f'trade_deny')
         ]
    ])

    keyboard_for_user = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Отменить предложение', callback_data=f'trade_cancel')]
    ])

    if user.is_hidden:
        user_formated_username = user.username
    else:
        user_formated_username = hlink(str(user.username), f'https://t.me/{user.tgusername[1:]}')

    if target.is_hidden:
        target_formated_username = target.username
    else:
        target_formated_username = hlink(target.username, f'https://t.me/{target.tgusername[1:]}')

    text_for_user = f'Предложение обмена успешно <b>отправлено</b>!\n\nОжидайте пока {target_formated_username} ответит...'
    text_for_target = f'Пользователь {user_formated_username} <b>предложил вам обмен</b>!'

    current_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    current_time = current_time - timedelta(days=1)
    current_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    current_time = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')

    trade = await create_trade(
        session=session,
        first_user_id=user.tguserid,
        second_user_id=target.tguserid,
        first_user_offer_type='none',
        second_user_offer_type='none',
        first_user_offer='none',
        second_user_offer='none',
        status=TradeStatus.pending,
        created_at=current_time
    )

    trade_id = trade.id
    await update_user(session, 'cur_trade_id', trade_id, user.tguserid)
    await update_user(session, 'is_in_trade', True, user.tguserid)

    await update_user(session, 'cur_trade_id', trade_id, target.tguserid)

    first_user_message = await bot.send_message(user.tguserid, text_for_user, reply_markup=keyboard_for_user,
                                                disable_web_page_preview=True, parse_mode='HTML')
    second_user_message = await bot.send_message(target.tguserid, text_for_target, reply_markup=keyboard_for_target,
                                                 disable_web_page_preview=True, parse_mode='HTML')

    await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade_id)
    await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade_id)


@router.callback_query(F.data == 'trade_cancel')
async def trade_canceled_by_first_user(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id

    if trade_id == -1:
        await callback.answer('Вы не отправляли предложение обмена!', show_alert=True)
        return

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_username = hlink(str(first_user.username), f'https://t.me/{first_user.tgusername[1:]}')
    first_user_message = trade.first_user_message_id

    second_user_username = hlink(str(second_user.username), f'https://t.me/{second_user.tgusername[1:]}')
    second_user_message = trade.second_user_message_id

    await update_user(session, 'cur_trade_id', -1, first_user.tguserid)
    await update_user(session, 'is_in_trade', False, first_user.tguserid)

    await update_user(session, 'cur_trade_id', -1, second_user.tguserid)

    await bot.delete_message(second_user.tguserid, second_user_message)
    await bot.delete_message(first_user.tguserid, first_user_message)

    await bot.send_message(first_user.tguserid, f'Вы <i>отменили</i> обмен с {second_user_username}!',
                           disable_web_page_preview=True, parse_mode='HTML')
    await bot.send_message(second_user.tguserid, f'Пользователь {first_user_username} <i>отменил</i> с вами обмен!',
                           disable_web_page_preview=True, parse_mode='HTML')

    await delete_trade(session, trade.id)


@router.callback_query(F.data == 'trade_deny')
async def trade_deny_by_second_user(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id

    if trade_id == -1:
        await callback.answer('Вы не отправляли предложение обмена!', show_alert=True)
        return

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_username = hlink(str(first_user.username), f'https://t.me/{first_user.tgusername[1:]}')
    first_user_message = trade.first_user_message_id

    second_user_username = hlink(str(second_user.username), f'https://t.me/{second_user.tgusername[1:]}')
    second_user_message = trade.second_user_message_id

    await update_user(session, 'cur_trade_id', -1, first_user.tguserid)
    await update_user(session, 'is_in_trade', False, first_user.tguserid)

    await update_user(session, 'cur_trade_id', -1, second_user.tguserid)

    await bot.delete_message(first_user.tguserid, first_user_message)
    await bot.delete_message(second_user.tguserid, second_user_message)

    await bot.send_message(second_user.tguserid, f'Вы <i>отклонили</i> обмен {first_user_username}.',
                           disable_web_page_preview=True, parse_mode='HTML')
    await bot.send_message(first_user.tguserid, f'Пользователь {second_user_username} <i>отклонил</i> ваше предложение обмена!',
                           disable_web_page_preview=True, parse_mode='HTML')

    await delete_trade(session, trade.id)


@router.callback_query(F.data == 'trade_confirm')
async def trade_confirm(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id

    if trade_id == -1:
        await callback.answer('Вы не отправляли предложение обмена!', show_alert=True)
        return

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Деньги", callback_data=f"trade_offer_money")],
        [InlineKeyboardButton(text="📦 Предметы", callback_data=f"trade_offer_items")],
        [InlineKeyboardButton(text="❌ Пусто", callback_data=f"trade_offer_empty")],
    ])


    await update_trade(session, 'second_user_id', second_user.tguserid, trade.id)
    await update_user(session, 'is_in_trade', True, second_user.tguserid)

    text = f'Отметь то, что ты дашь <b>со своей стороны:</b>'

    await bot.delete_message(first_user.tguserid, first_user_message)
    await bot.delete_message(second_user.tguserid, second_user_message)

    first_user_message = await bot.send_message(first_user.tguserid, text, reply_markup=keyboard, parse_mode='HTML')
    second_user_message = await bot.send_message(second_user.tguserid, text, reply_markup=keyboard, parse_mode='HTML')

    await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
    await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)


@router.callback_query(F.data == 'trade_offer_items')
async def trade_offer_items(callback: CallbackQuery, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    user_items = await get_user_items(session, user.tguserid)
    if not user_items:
        await callback.answer("У вас нет предметов для обмена!", show_alert=True)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Деньги", callback_data=f"trade_offer_money")],
            [InlineKeyboardButton(text="📦 Предметы", callback_data=f"trade_offer_items")],
            [InlineKeyboardButton(text="❌ Пусто", callback_data=f"trade_offer_empty")],
        ])

        text = f'У тебя нет предметов.\nВыбери, что ты хочешь дать <b>со своей стороны:</b>'

        if user.tguserid == trade.first_user_id:
            await bot.delete_message(first_user.tguserid, first_user_message)
            first_user_message = await bot.send_message(first_user.tguserid, text, reply_markup=keyboard,
                                                        parse_mode='HTML')
            await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
        else:
            await bot.delete_message(second_user.tguserid, second_user_message)
            second_user_message = await bot.send_message(second_user.tguserid, text, reply_markup=keyboard,
                                                         parse_mode='HTML')
            await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)
        return

    keyboard = create_pagination_keyboard(user_items)

    if user.tguserid == trade.first_user_id:
        await bot.delete_message(first_user.tguserid, first_user_message)
        first_user_message = await bot.send_message(first_user.tguserid, 'Выберите предмет для предложения:', reply_markup=keyboard)
        await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
        await update_trade(session, 'first_user_offer_type', 'items', trade.id)
    elif user.tguserid == trade.second_user_id:
        await bot.delete_message(second_user.tguserid, second_user_message)
        second_user_message = await bot.send_message(second_user.tguserid, 'Выбери предмет для предложния:', reply_markup=keyboard)
        await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)
        await update_trade(session, 'second_user_offer_type', 'items', trade.id)


@router.callback_query(F.data == 'trade_offer_empty')
async def trade_offer_empty(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="trade_confirm_offer"),
         InlineKeyboardButton(text='Обновить', callback_data="trade_update_offer")],
        [InlineKeyboardButton(text='Выйти из сделки', callback_data="trade_cancel_offer")],
        [InlineKeyboardButton(text='Назад', callback_data="trade_back_to_offer_type")]
    ])

    if user.tguserid == first_user.tguserid:
        await update_trade(session, 'first_user_offer_type', 'empty', trade.id)

        text_for_confirmation = format_offer_text(
            user=first_user,
            other_user=second_user,
            trade=trade,
            is_first_user=True,
            scr=scr
        )

        await bot.delete_message(first_user.tguserid, first_user_message)
        first_user_message = await bot.send_message(first_user.tguserid, text_for_confirmation,
                                                    reply_markup=keyboard, disable_web_page_preview=True,
                                                    parse_mode='HTML')

        await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)

    elif user.tguserid == second_user.tguserid:
        await update_trade(session, 'second_user_offer_type', 'empty', trade.id)

        text_for_confirmation = format_offer_text(
            user=second_user,
            other_user=first_user,
            trade=trade,
            is_first_user=False,
            scr=scr
        )

        await bot.delete_message(second_user.tguserid, second_user_message)
        second_user_message = await bot.send_message(second_user.tguserid, text_for_confirmation,
                                                    reply_markup=keyboard, disable_web_page_preview=True,
                                                    parse_mode='HTML')

        await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)


@router.callback_query(F.data == ("trade_offer_money"))
async def trade_offer_money(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id

    scr = Scripts()

    if trade_id == -1:
        await callback.answer('Вы не отправляли предложение обмена!', show_alert=True)
        return

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    if user.tguserid == first_user.tguserid:
        await update_trade(session, 'first_user_offer_type', 'money', trade.id)
        text = f'Напиши в чат, сколько денег ты хочешь выбрать. Твой баланс — <b>{scr.amount_changer(str(first_user.balance_main))}$</b>'

        await bot.delete_message(first_user.tguserid, first_user_message)
        first_user_message = await bot.send_message(first_user.tguserid, text, parse_mode='HTML')
        await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)

    elif user.tguserid == second_user.tguserid:
        await update_trade(session, 'second_user_offer_type', 'money', trade.id)
        text = f'Напиши в чат, сколько денег ты хочешь выбрать. Твой баланс — <b>{scr.amount_changer(str(second_user.balance_main))}$</b>'

        await bot.delete_message(second_user.tguserid, second_user_message)
        second_user_message = await bot.send_message(second_user.tguserid, text, parse_mode='HTML')
        await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)

    else:
        logger.error(f"{user.tguserid} is not a part of trade {trade.id}")
        return

    await state.set_state(TradeStates.entering_quantity_of_money)


@router.message(TradeStates.entering_quantity_of_money)
async def trade_entering_quantity_of_money(message: Message, state: FSMContext, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, message.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    if trade_id == -1:
        await message.answer('Вы не отправляли предложение обмена!', show_alert=True)
        return

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    message_text = message.text.lower()

    if not message_text.isdigit():
        if 'к' in message_text:
            try:
                amount = scr.unformat_number(scr.amount_changer(message_text))
            except ValueError:
                await bot.send_message(user.tguserid, 'Некорректный ввод!\nПример ввода:\n\n100000\n100к')
                await state.set_state(TradeStates.entering_quantity_of_money)
                return
        else:
            await bot.send_message(user.tguserid, 'Некорректный ввод!\nПример ввода:\n\n100000\n100к')
            await state.set_state(TradeStates.entering_quantity_of_money)
            return

    elif message_text.isdigit() and int(message_text) == 0:
        amount = 0

    elif message_text.isdigit() and int(message_text) > 0:
        amount = int(message_text)
    else:
        await bot.send_message(user.tguserid, 'Некорректный ввод!\nПример ввода:\n\n100000\n100к')
        await state.set_state(TradeStates.entering_quantity_of_money)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="trade_confirm_offer"),
         InlineKeyboardButton(text='Обновить', callback_data="trade_update_offer")],
        [InlineKeyboardButton(text='Выйти из сделки', callback_data="trade_cancel_offer")],
        [InlineKeyboardButton(text='Назад', callback_data="trade_back_to_offer_type")]
    ])

    if user.tguserid == first_user.tguserid:
        if amount > first_user.balance_main:
            await bot.send_message(user.tguserid, f'У тебя не хватает '
                                                  f'{scr.amount_changer(amount - first_user.balance_main)}$ для обмена!'
                                                  f'\nТвой баланс — <b>{scr.amount_changer(str(first_user.balance_main))}$</b>')
            await state.set_state(TradeStates.entering_quantity_of_money)
            return


        await update_trade(session, 'first_user_offer', amount, trade.id)

        text = f'Ты выбрал {scr.amount_changer(str(amount))}$ для обмена.'

        await bot.delete_message(first_user.tguserid, first_user_message)
        await bot.send_message(first_user.tguserid, text, parse_mode='HTML')

        trade = await get_trade_by_trade_id(session, trade.id)

        text_for_confirmation = format_offer_text(
            user=first_user,
            other_user=second_user,
            trade=trade,
            is_first_user=True,
            scr=scr
        )

        first_user_message = await bot.send_message(first_user.tguserid, text_for_confirmation,
                               reply_markup=keyboard, disable_web_page_preview=True, parse_mode='HTML')

        await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
        await state.clear()

    elif user.tguserid == second_user.tguserid:
        if amount > second_user.balance_main:
            await bot.send_message(user.tguserid, f'У тебя не хватает '
                                                  f'{scr.amount_changer(amount - second_user.balance_main)}$ для обмена!'
                                                  f'\nТвой баланс — <b>{scr.amount_changer(str(second_user.balance_main))}$</b>')
            await state.set_state(TradeStates.entering_quantity_of_money)
            return

        await update_trade(session, 'second_user_offer', amount, trade.id)

        text = f'Ты выбрал {scr.amount_changer(str(amount))}$ для обмена.'

        await bot.delete_message(second_user.tguserid, second_user_message)
        await bot.send_message(second_user.tguserid, text, parse_mode='HTML')

        trade = await get_trade_by_trade_id(session, trade.id)

        text_for_confirmation = format_offer_text(
            user=second_user,
            other_user=first_user,
            trade=trade,
            is_first_user=False,
            scr=scr
        )

        second_user_message = await bot.send_message(second_user.tguserid, text_for_confirmation,
                                                    reply_markup=keyboard, disable_web_page_preview=True,
                                                    parse_mode='HTML')

        await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)
        await state.clear()


@router.callback_query(F.data == "trade_update_offer")
async def trade_update_offer(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="trade_confirm_offer"),
         InlineKeyboardButton(text='Обновить', callback_data="trade_update_offer")],
        [InlineKeyboardButton(text='Выйти из сделки', callback_data="trade_cancel_offer")],
        [InlineKeyboardButton(text='Назад', callback_data="trade_back_to_offer_type")]
    ])

    if user.tguserid == first_user.tguserid:
        text = format_offer_text(first_user, second_user, trade, True, scr)
        message_id = trade.first_user_message_id
        chat_id = first_user.tguserid
    else:
        text = format_offer_text(second_user, first_user, trade, False, scr)
        message_id = trade.second_user_message_id
        chat_id = second_user.tguserid

    await bot.edit_message_text(
        chat_id=chat_id, text=text,
        reply_markup=keyboard, disable_web_page_preview=True,
        parse_mode='HTML', message_id=message_id
    )


@router.callback_query(F.data.startswith("item_"))
async def select_item_to_offer(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    item_id = int(callback.data.split('_')[1])
    item = await get_item_by_id(session, item_id)
    if not item:
        await callback.answer("Такого предмета не существует!", show_alert=True)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Деньги", callback_data=f"trade_offer_money")],
            [InlineKeyboardButton(text="📦 Предметы", callback_data=f"trade_offer_items")],
            [InlineKeyboardButton(text="❌ Пусто", callback_data=f"trade_offer_empty")],
        ])

        text = f'У тебя нет этого предмета.\nВыбери, что ты хочешь дать <b>со своей стороны:</b>'

        if user.tguserid == trade.first_user_id:
            await bot.delete_message(first_user.tguserid, first_user_message)
            first_user_message = await bot.send_message(first_user.tguserid, text, reply_markup=keyboard,
                                                        parse_mode='HTML')
            await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
        else:
            await bot.delete_message(second_user.tguserid, second_user_message)
            second_user_message = await bot.send_message(second_user.tguserid, text, reply_markup=keyboard,
                                                         parse_mode='HTML')
            await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)
        return

    text_for_first_user = format_offer_text(first_user, second_user, trade, True, scr)
    text_for_second_user = format_offer_text(second_user, first_user, trade, False, scr)


    if user.tguserid == trade.first_user_id:
        await update_trade(session, 'first_user_offer', item.item_name, trade.id)


@router.callback_query(F.data == "trade_back_to_offer_type")
async def trade_back_to_offer_type(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Деньги", callback_data=f"trade_offer_money")],
        [InlineKeyboardButton(text="📦 Предметы", callback_data=f"trade_offer_items")],
        [InlineKeyboardButton(text="❌ Пусто", callback_data=f"trade_offer_empty")],
    ])

    text = f'Отметь то, что ты дашь <b>со своей стороны:</b>'

    if user.tguserid == first_user.tguserid:
        await update_trade(session, 'first_user_offer', 'none', trade.id)
        await update_trade(session, 'first_user_confirm', False, trade.id)
        await update_trade(session, 'first_user_offer_type', 'none', trade.id)
        await bot.delete_message(first_user.tguserid, first_user_message)

        first_user_message = await bot.send_message(first_user.tguserid, text, reply_markup=keyboard,
                                                    parse_mode='HTML')

        await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)

    elif user.tguserid == second_user.tguserid:
        await update_trade(session, 'second_user_offer', 'none', trade.id)
        await update_trade(session, 'second_user_confirm', False, trade.id)
        await update_trade(session, 'second_user_offer_type', 'none', trade.id)
        await bot.delete_message(second_user.tguserid, second_user_message)

        second_user_message = await bot.send_message(second_user.tguserid, text, reply_markup=keyboard,
                                                     parse_mode='HTML')

        await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)


@router.callback_query(F.data == "trade_cancel_offer")
async def trade_cancel_offer(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_username = hlink(str(first_user.username), f'https://t.me/{first_user.tgusername[1:]}')
    first_user_message = trade.first_user_message_id

    second_user_username = hlink(str(second_user.username), f'https://t.me/{second_user.tgusername[1:]}')
    second_user_message = trade.second_user_message_id

    if user.tguserid == first_user.tguserid:
        text_for_first_user = f'Ты отменил обмен с {second_user_username}!'
        text_for_second_user = f'{first_user_username} отменил обмен!'
    elif user.tguserid == second_user.tguserid:
        text_for_first_user = f'{second_user_username} отменил обмен!'
        text_for_second_user = f'Ты отменил обмен с {first_user_username}!'
    else:
        logger.error("User is not in trade")
        return

    await bot.delete_message(first_user.tguserid, first_user_message)
    await bot.delete_message(second_user.tguserid, second_user_message)

    await bot.send_message(first_user.tguserid, text_for_first_user, parse_mode='HTML', disable_web_page_preview=True)
    await bot.send_message(second_user.tguserid, text_for_second_user, parse_mode='HTML', disable_web_page_preview=True)

    await delete_trade(session, trade_id)

    await update_user(session, 'cur_trade_id', -1, first_user.tguserid)
    await update_user(session, 'is_in_trade', False, first_user.tguserid)

    await update_user(session, 'cur_trade_id', -1, second_user.tguserid)
    await update_user(session, 'is_in_trade', False, second_user.tguserid)


@router.callback_query(F.data == 'trade_cancel_confirm')
async def trade_cancel_confirm(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="trade_confirm_offer"),
         InlineKeyboardButton(text='Обновить', callback_data="trade_update_offer")],
        [InlineKeyboardButton(text='Выйти из сделки', callback_data="trade_cancel_offer")],
        [InlineKeyboardButton(text='Назад', callback_data="trade_back_to_offer_type")]
    ])

    upd_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌Отменить подтверждение", callback_data=f"trade_cancel_confirm"),
         InlineKeyboardButton(text='Обновить', callback_data="trade_update_offer")],
        [InlineKeyboardButton(text='Выйти из сделки', callback_data="trade_cancel_offer")],
        [InlineKeyboardButton(text='Назад', callback_data="trade_back_to_offer_type")]
    ])

    if user.tguserid == first_user.tguserid:
        await update_trade(session, 'first_user_confirm', False, trade.id)

        text_for_first_user = format_offer_text(first_user, second_user, trade, True, scr)
        text_for_second_user = format_offer_text(second_user, first_user, trade, False, scr)

        await bot.edit_message_text(
            chat_id=first_user.tguserid, text=text_for_first_user, disable_web_page_preview=True,
            parse_mode='HTML', message_id=first_user_message, reply_markup=new_keyboard
        )

        await bot.edit_message_text(
            chat_id=second_user.tguserid, text=text_for_second_user, disable_web_page_preview=True,
            parse_mode='HTML', message_id=second_user_message, reply_markup=new_keyboard
        )

    elif user.tguserid == second_user.tguserid:
        await update_trade(session, 'second_user_confirm', False, trade.id)

        text_for_first_user = format_offer_text(first_user, second_user, trade, True, scr)
        text_for_second_user = format_offer_text(second_user, first_user, trade, False, scr)

        await bot.edit_message_text(
            chat_id=first_user.tguserid, text=text_for_first_user, disable_web_page_preview=True,
            parse_mode='HTML', message_id=first_user_message, reply_markup=new_keyboard
        )

        await bot.edit_message_text(
            chat_id=second_user.tguserid, text=text_for_second_user, disable_web_page_preview=True,
            parse_mode='HTML', message_id=second_user_message, reply_markup=new_keyboard
        )


@router.callback_query(F.data == 'trade_confirm_offer')
async def trade_confirm_offer(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    upd_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="trade_confirm_offer"),
         InlineKeyboardButton(text='Обновить', callback_data="trade_update_offer")],
        [InlineKeyboardButton(text='Выйти из сделки', callback_data="trade_cancel_offer")],
        [InlineKeyboardButton(text='Назад', callback_data="trade_back_to_offer_type")]
    ])

    post_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"trade_post_confirm_offer")],
        [InlineKeyboardButton(text="Назад", callback_data=f"trade_back_to_offer_type_from_post_trade")],
    ])

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌Отменить подтверждение", callback_data=f"trade_cancel_confirm"),
         InlineKeyboardButton(text='Обновить', callback_data="trade_update_offer")],
        [InlineKeyboardButton(text='Выйти из сделки', callback_data="trade_cancel_offer")],
        [InlineKeyboardButton(text='Назад', callback_data="trade_back_to_offer_type")]
    ])

    first_part = '🚫 Внимательно проверь всё. После этого подтверждения сделку <b>нельзя будет отменить</b>!'

    second_part_for_first_user = format_offer_text(
        user=first_user,
        other_user=second_user,
        trade=trade,
        is_first_user=True,
        scr=scr,
        is_symbol=False
    )
    second_part_for_second_user = format_offer_text(
        user=second_user,
        other_user=first_user,
        trade=trade,
        is_first_user=False,
        scr=scr,
        is_symbol=False
    )

    if user.tguserid == first_user.tguserid:
        await update_trade(session, 'first_user_confirm', True, trade.id)

        if trade.second_user_confirm:
            text_for_first_user = f'{first_part}\n\n{second_part_for_first_user}'
            text_for_second_user = f'{first_part}\n\n{second_part_for_second_user}'

            await bot.delete_message(second_user.tguserid, second_user_message)
            await bot.delete_message(first_user.tguserid, first_user_message)

            second_user_message = await bot.send_message(second_user.tguserid, text_for_second_user, reply_markup=post_keyboard, parse_mode='HTML',
                                   disable_web_page_preview=True)

            first_user_message = await bot.send_message(first_user.tguserid, text_for_first_user, reply_markup=post_keyboard, parse_mode='HTML',
                                   disable_web_page_preview=True)

            await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
            await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)

        else:
            text_for_first_user = format_offer_text(first_user, second_user, trade, True, scr)
            text_for_second_user = format_offer_text(second_user, first_user, trade, False, scr)

            await bot.edit_message_text(
                chat_id=first_user.tguserid, text=text_for_first_user, disable_web_page_preview=True,
                parse_mode='HTML', message_id=first_user_message, reply_markup=new_keyboard
            )

            await bot.edit_message_text(
                chat_id=second_user.tguserid, text=text_for_second_user, disable_web_page_preview=True,
                parse_mode='HTML', message_id=second_user_message, reply_markup=upd_keyboard
            )

    elif user.tguserid == second_user.tguserid:
        await update_trade(session, 'second_user_confirm', True, trade.id)

        if trade.first_user_confirm:
            text_for_first_user = f'{first_part}\n\n{second_part_for_first_user}'
            text_for_second_user = f'{first_part}\n\n{second_part_for_second_user}'

            await bot.delete_message(first_user.tguserid, first_user_message)
            await bot.delete_message(second_user.tguserid, second_user_message)

            first_user_message = await bot.send_message(first_user.tguserid, text_for_first_user, reply_markup=post_keyboard,
                                   parse_mode='HTML',
                                   disable_web_page_preview=True)

            second_user_message = await bot.send_message(second_user.tguserid, text_for_second_user, reply_markup=post_keyboard,
                                   parse_mode='HTML',
                                   disable_web_page_preview=True)

            await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
            await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)

        else:
            text_for_first_user = format_offer_text(first_user, second_user, trade, True, scr)
            text_for_second_user = format_offer_text(second_user, first_user, trade, False, scr)

            await bot.edit_message_text(
                chat_id=first_user.tguserid, text=text_for_first_user, disable_web_page_preview=True,
                parse_mode='HTML', message_id=first_user_message, reply_markup=upd_keyboard
            )

            await bot.edit_message_text(
                chat_id=second_user.tguserid, text=text_for_second_user, disable_web_page_preview=True,
                parse_mode='HTML', message_id=second_user_message, reply_markup=new_keyboard
            )


@router.callback_query(F.data == 'trade_back_to_offer_type_from_post_trade')
async def back_to_offer_type_from_post_trade(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)

    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    first_user_message = trade.first_user_message_id
    second_user_message = trade.second_user_message_id

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Деньги", callback_data=f"trade_offer_money")],
        [InlineKeyboardButton(text="📦 Предметы", callback_data=f"trade_offer_items")],
        [InlineKeyboardButton(text="❌ Пусто", callback_data=f"trade_offer_empty")],
    ])

    text = f'Отметь то, что ты дашь <b>со своей стороны:</b>'

    await bot.delete_message(first_user.tguserid, first_user_message)
    await bot.delete_message(second_user.tguserid, second_user_message)

    if user.tguserid == first_user.tguserid:
        await bot.send_message(second_user.tguserid, 'Обратная сторона хочет внести правки!')
    elif user.tguserid == second_user.tguserid:
        await bot.send_message(first_user.tguserid, 'Обратная сторона хочет внести правки!')

    await update_trade(session, 'first_user_offer', 'none', trade.id)
    await update_trade(session, 'first_user_confirm', False, trade.id)
    await update_trade(session, 'first_user_post_confirm', False, trade.id)
    await update_trade(session, 'first_user_offer_type', 'none', trade.id)

    await update_trade(session, 'second_user_offer', 'none', trade.id)
    await update_trade(session, 'second_user_confirm', False, trade.id)
    await update_trade(session, 'second_user_post_confirm', False, trade.id)
    await update_trade(session, 'second_user_offer_type', 'none', trade.id)

    first_user_message = await bot.send_message(first_user.tguserid, text, reply_markup=keyboard,
                                                parse_mode='HTML')

    second_user_message = await bot.send_message(second_user.tguserid, text, reply_markup=keyboard,
                                                 parse_mode='HTML')

    await update_trade(session, 'first_user_message_id', first_user_message.message_id, trade.id)
    await update_trade(session, 'second_user_message_id', second_user_message.message_id, trade.id)


@router.callback_query(F.data == 'trade_post_confirm_offer')
async def trade_post_confirm_offer(callback: CallbackQuery, bot: Bot, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    trade_id = user.cur_trade_id
    scr = Scripts()

    trade, first_user, second_user = await get_trade_data(session, trade_id)

    # Формируем тексты для обоих пользователей
    text_first = format_offer_text(first_user, second_user, trade, True, scr, False)
    text_second = format_offer_text(second_user, first_user, trade, False, scr, False)

    async def update_message(chat_id: int, message_id: int, text: str) -> None:
        """Вспомогательная функция для обновления сообщения."""
        await bot.edit_message_text(
            chat_id=chat_id,
            text=text,
            message_id=message_id,
            disable_web_page_preview=True,
            parse_mode='HTML',
            reply_markup=None
        )

    async def complete_trade() -> None:
        """Вспомогательная функция для завершения сделки."""
        if trade.first_user_offer_type == 'money' and trade.second_user_offer_type == 'money':
            first_offer = int(trade.first_user_offer)
            second_offer = int(trade.second_user_offer)

            # Обновляем балансы
            await update_user(session, 'balance_main', first_user.balance_main + second_offer - first_offer, first_user.tguserid)
            await update_user(session, 'balance_main', second_user.balance_main + first_offer - second_offer, second_user.tguserid)

        # TODO: Добавить логику для обмена предметами, если offer_type != 'money'
        elif trade.first_user_offer_type == 'empty' and trade.second_user_offer_type == 'money':
            second_user_offer = int(trade.second_user_offer)

            await update_user(session, 'balance_main', second_user.balance_main - second_user_offer, second_user.tguserid)
            await update_user(session, 'balance_main', first_user.balance_main + second_user_offer, first_user.tguserid)

        elif trade.first_user_offer_type == 'money' and trade.second_user_offer_type == 'empty':
            first_user_offer = int(trade.first_user_offer)

            await update_user(session, 'balance_main', first_user.balance_main - first_user_offer, first_user.tguserid)
            await update_user(session, 'balance_main', second_user.balance_main + first_user_offer, second_user.tguserid)

        # Например:
        # if trade.first_user_offer_type == 'item':
        #     await transfer_item(session, first_user.tguserid, second_user.tguserid, trade.first_user_offer)
        # if trade.second_user_offer_type == 'item':
        #     await transfer_item(session, second_user.tguserid, first_user.tguserid, trade.second_user_offer)

        # Завершаем сделку для обоих пользователей
        updates = [
            ('cur_trade_id', -1, first_user.tguserid),
            ('is_in_trade', False, first_user.tguserid),
            ('cur_trade_id', -1, second_user.tguserid),
            ('is_in_trade', False, second_user.tguserid),
            ('status', TradeStatus.completed, trade.id, True)  # Последний аргумент указывает, что это trade
        ]
        for field, value, user_id, *is_trade in updates:
            await (update_trade if is_trade else update_user)(session, field, value, trade.id if is_trade else user_id)

        # Обновляем сообщения для обоих
        await bot.send_message(first_user.tguserid, 'Обмен завершён!\n\n/me')
        await bot.send_message(second_user.tguserid, 'Обмен завершён!\n\n/me')

        await update_message(first_user.tguserid, trade.first_user_message_id, text_first)
        await update_message(second_user.tguserid, trade.second_user_message_id, text_second)


    if user.tguserid == first_user.tguserid:
        if trade.second_user_confirm:
            await complete_trade()
        else:
            await update_trade(session, 'first_user_post_confirm', True, trade.id)
            await update_message(first_user.tguserid, trade.first_user_message_id, text_first)
    elif user.tguserid == second_user.tguserid:
        if trade.first_user_post_confirm:
            await complete_trade()
        else:
            await update_trade(session, 'second_user_post_confirm', True, trade.id)
            await update_message(second_user.tguserid, trade.second_user_message_id, text_second)

