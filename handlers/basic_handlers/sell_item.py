from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from database.SQLmodels import Item
from database.methods import get_user_by_tguserid, get_dict_user_items, get_item_by_name, get_user_items, \
    get_item_by_id, update_user, remove_item_from_user
from handlers.init_router import router


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from scripts.loggers import log
from scripts.scripts import Scripts


class PaginationCallback(CallbackData, prefix="pagination"):
    action: str
    page: int


# Функция для создания клавиатуры с пагинацией
def create_pagination_keyboard(items: list[Item], page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    start_index = page * items_per_page
    end_index = start_index + items_per_page
    current_items = items[start_index:end_index]

    for item in current_items:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=item.item_name, callback_data=f"pre_sell_item_{item.id}")])

    navigation_buttons = []
    total_pages = (len(items) + items_per_page - 1) // items_per_page

    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=PaginationCallback(action="sell_command_previous", page=page - 1).pack()
            )
        )

    if page < total_pages - 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=PaginationCallback(action="sell_command_next", page=page + 1).pack()
            )
        )

    if navigation_buttons:
        keyboard.inline_keyboard.append(navigation_buttons)

    return keyboard

@router.message(F.text.lower().startswith(('продать', 'sell', '/продать', '/sell')))
@log("Selling items... What is this? Oh it's me, LOG!")
async def sell_item(message: Message, state: FSMContext, session: AsyncSession) -> None:
    scr = Scripts()

    user_id = message.from_user.id
    message_text = message.text.split()
    message_len = len(message_text)

    if not await get_user_by_tguserid(session, user_id):
        await message.answer('Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register')
        return

    user = await get_user_by_tguserid(session, message.from_user.id)
    user_items_list = await get_user_items(session, user.tguserid)
    user_items_dict = await get_dict_user_items(session, user.tguserid)

    if not user_items_list:
        await message.answer('У вас нет предметов!')
        return

    if message_len == 1:
        keyboard = create_pagination_keyboard(user_items_list)
        user_message = await message.answer('Выберите предмет для продажи:', reply_markup=keyboard)
        await state.update_data(user_message=user_message, user_id=user.tguserid, message_with_keyboard=user_message)
        return

    try:
        count = int(message_text[-1])
        item_name_parts = message_text[1:-1]
    except ValueError:
        count = 1
        item_name_parts = message_text[1:]

    item_for_sale = ' '.join(item_name_parts)

    if message_len > 2 and not item_name_parts:
        await message.answer(
            'Неверный формат команды! Примеры:\n\n/sell <предмет> [кол-во]\n/sell (далее с помощью кнопок)',
            parse_mode=None)
        return

    if user_items_dict.get(item_for_sale) < count:
        await message.answer('У вас нет столько предметов!')
        return

    item = await get_item_by_name(session, item_for_sale)

    if item:
        flag = await remove_item_from_user(session, item.id, user.tguserid, count)
        if flag:
            await message.answer(f'Вы продали {count} "{item_for_sale}", за {scr.amount_changer(str(item.item_sell_price * count))}')
            await update_user(session, 'balance_main', user.balance_main + item.item_sell_price * count, user.tguserid)

        else:
            await message.answer(f'У вас нет "{item_for_sale}"')
            return
    else:
        await message.answer('Такого предмета нет!')


@router.callback_query(F.data.startswith("pre_sell_item_"))
async def select_item_to_sell(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)

    data = await state.get_data()

    chat_id = callback.message.chat.id
    scr = Scripts()

    if 'user_id' not in data or data['user_id'] != user.tguserid:
        await callback.answer("Это не ваша кнопка!", show_alert=True)
        return

    item_id = int(callback.data.split("_")[3])
    item = await get_item_by_id(session, item_id)

    item_price = scr.amount_changer(str(item.item_sell_price))
    item_name = item.item_name

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'Продать за {item_price}', callback_data=f'sell_item_{item_id}')],
        [InlineKeyboardButton(text='Отмена', callback_data='cancel_sell_item')]
    ])

    await bot.send_message(chat_id, f'Вы выбрали предмет "{item_name}". Вы уверены что хотите его продать?', reply_markup=keyboard)


@router.callback_query(F.data == "cancel_sell_item")
async def cancel_sell_item(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)
    chat_id = callback.message.chat.id

    data = await state.get_data()

    if 'user_id' not in data or data['user_id'] != user.tguserid:
        await callback.answer("Это не ваша кнопка!", show_alert=True)
        return

    user_message = data["user_message"]
    user_message_id = user_message.message_id

    user_items = await get_user_items(session, user.tguserid)
    new_keyboard = create_pagination_keyboard(user_items)

    await bot.delete_message(chat_id, user_message_id)
    user_message = await bot.send_message(chat_id, 'Выберите предмет для продажи:', reply_markup=new_keyboard)
    await state.update_data(user_message=user_message)


@router.callback_query(F.data.startswith("sell_item_"))
async def confirm_sell_item(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)
    chat_id = callback.message.chat.id

    data = await state.get_data()
    user_balance = user.balance_main
    scr = Scripts()

    if 'user_id' not in data or data['user_id'] != user.tguserid:
        await callback.answer("Это не ваша кнопка!", show_alert=True)
        return

    item_id = int(callback.data.split("_")[2])
    item = await get_item_by_id(session, item_id)

    # Получаем словарь предметов пользователя, чтобы узнать количество
    user_items_dict = await get_dict_user_items(session, user.tguserid)
    item_name = item.item_name
    count = user_items_dict.get(item_name, 0)  # Продаем все доступные предметы

    if count == 0:
        await callback.answer("У вас нет этого предмета!", show_alert=True)
        return

    # Удаляем предметы
    flag = await remove_item_from_user(session, item_id, user.tguserid)
    if not flag:
        await callback.answer("Ошибка при продаже предмета!", show_alert=True)
        return

    # Обновляем баланс
    total_price = item.item_sell_price
    await update_user(session, "balance_main", user_balance + total_price, user.tguserid)

    # Обновляем клавиатуру
    user_items = await get_user_items(session, user.tguserid)
    keyboard = create_pagination_keyboard(user_items)
    user_message = data["message_with_keyboard"]

    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=user_message.message_id,
            reply_markup=keyboard
        )
    except:
        # Если сообщение не удается отредактировать, отправляем новое
        await bot.delete_message(chat_id, user_message.message_id)
        user_message = await bot.send_message(chat_id, 'Выберите предмет для продажи:', reply_markup=keyboard)
        await state.update_data(message_with_keyboard=user_message)

    # Отправляем подтверждение продажи
    await bot.send_message(
        chat_id,
        f'Вы продали "{item.item_name}" за {scr.amount_changer(str(total_price))}$'
    )
    await callback.answer()

@router.callback_query(PaginationCallback.filter(F.action.in_(["sell_command_next", "sell_command_previous"])))
async def handle_sell_command_pagination(callback: CallbackQuery, state: FSMContext, callback_data: PaginationCallback, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)
    data = await state.get_data()
    page = callback_data.page

    if 'user_id' not in data or data['user_id'] != user.tguserid:
        await callback.answer("Это не ваша кнопка!", show_alert=True)
        return

    user_items_list = await get_user_items(session, user.tguserid)
    keyboard = create_pagination_keyboard(user_items_list, page)

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()