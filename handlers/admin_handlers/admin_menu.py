from json import loads

from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


# Состояния для команды /give
class GiveBalanceStates(StatesGroup):
    choosing_currency = State()  # Выбор валюты
    entering_username = State()  # Ввод username
    entering_amount = State()    # Ввод суммы


class SetBalanceStates(StatesGroup):
    choosing_currency = State()  # Выбор валюты
    entering_username = State()  # Ввод username
    entering_amount = State()    # Ввод суммы


class AddItemStates(StatesGroup):
    entering_username = State()  # Ввод username
    entering_item = State()      # Ввод предмета
    entering_quantity = State()  # Ввод количества


# Команда /admin
@router.message(Command("admin"))
async def admin_menu(message: Message, state: FSMContext):
    db = Database()
    user_id = message.from_user.id

    if not db.get_user_stat(user_id, "is_admin"):
        await message.answer("❌ Вы не администратор.")
        return

    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выдать баланс", callback_data="give_balance")],
        [InlineKeyboardButton(text="Установить баланс", callback_data="set_balance")],
        [InlineKeyboardButton(text="Выдать предмет", callback_data="give_item")],
        [InlineKeyboardButton(text="Обновить предметы", callback_data="update_items")]
    ])

    await message.answer(
        "🔐 Админ-меню:",
        reply_markup=keyboard,
        reply_to_message_id=message.message_id
    )


# Обработка кнопки "Установить баланс"
@router.callback_query(F.data == "set_balance")
async def set_balance_start(callback: CallbackQuery, state: FSMContext):
    # Создаем клавиатуру с выбором валюты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Основной баланс (m)", callback_data="currency_main")],
        [InlineKeyboardButton(text="Альтернативный баланс (a)", callback_data="currency_alt")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ])

    await callback.message.answer(
        "➡️ Выберите тип валюты:",
        reply_markup=keyboard
    )
    await state.set_state(SetBalanceStates.choosing_currency)


# Обработка выбора валюты
@router.callback_query(SetBalanceStates.choosing_currency, F.data.in_(["currency_main", "currency_alt"]))
async def currency_chosen(callback: CallbackQuery, state: FSMContext):
    currency_type = "balance_main" if callback.data == "currency_main" else "balance_alt"
    await state.update_data(currency_type=currency_type)  # Сохраняем тип валюты

    await callback.message.answer(
        "✏️ Введите username пользователя (например, @username):"
    )
    await state.set_state(SetBalanceStates.entering_username)


# Обработка ввода username
@router.message(SetBalanceStates.entering_username)
async def username_entered(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")  # Убираем @, если есть
    await state.update_data(username=username)  # Сохраняем username

    await message.answer("💰 Введите сумму:")
    await state.set_state(SetBalanceStates.entering_amount)


# Обработка ввода суммы
@router.message(SetBalanceStates.entering_amount)
async def amount_entered(message: Message, state: FSMContext, db: Database):
    scr = Scripts()
    user_data = await state.get_data()  # Получаем сохраненные данные

    # Проверяем, что сумма — число
    try:
        amount = scr.unformat_number(scr.amount_changer(message.text))

    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число.")
        return

    # Ищем пользователя
    try:
        target_id = db.get_user_id_by_tgusername('@' + user_data["username"])
    except Exception:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    # Устанавливаем баланс
    db.update_user(user_data["currency_type"], amount, target_id)

    # Форматируем сумму
    formatted_amount = scr.amount_changer(str(amount))

    await message.answer(
        f"✅ Пользователю @{user_data['username']} установлен баланс {formatted_amount}$!"
    )
    await state.clear()


# Обработка кнопки "Выдать баланс"
@router.callback_query(F.data == "give_balance")
async def give_set_balance_start(callback: CallbackQuery, state: FSMContext):
    # Создаем клавиатуру с выбором валюты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Основной баланс (m)", callback_data="currency_main")],
        [InlineKeyboardButton(text="Альтернативный баланс (a)", callback_data="currency_alt")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ])

    await callback.message.answer(
        "➡️ Выберите тип валюты:",
        reply_markup=keyboard
    )
    await state.set_state(GiveBalanceStates.choosing_currency)


# Обработка выбора валюты
@router.callback_query(GiveBalanceStates.choosing_currency, F.data.in_(["currency_main", "currency_alt"]))
async def currency_chosen(callback: CallbackQuery, state: FSMContext):
    currency_type = "balance_main" if callback.data == "currency_main" else "balance_alt"
    await state.update_data(currency_type=currency_type)  # Сохраняем тип валюты

    await callback.message.answer(
        "✏️ Введите username пользователя (например, @username):"
    )
    await state.set_state(GiveBalanceStates.entering_username)


# Обработка ввода username
@router.message(GiveBalanceStates.entering_username)
async def username_entered(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")  # Убираем @, если есть
    print(username)
    await state.update_data(username=username)  # Сохраняем username

    await message.answer("💰 Введите сумму:")
    await state.set_state(GiveBalanceStates.entering_amount)


# Обработка ввода суммы
@router.message(GiveBalanceStates.entering_amount)
async def amount_entered(message: Message, state: FSMContext):
    db = Database()
    scr = Scripts()
    user_data = await state.get_data()  # Получаем сохраненные данные

    # Проверяем, что сумма — число
    try:
        amount = scr.unformat_number(scr.amount_changer(message.text))

    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число.")
        return

    # Ищем пользователя
    try:
        print(user_data)
        target_id = db.get_user_id_by_tgusername('@' + user_data["username"])
    except Exception:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    # Обновляем баланс
    current_balance = db.get_user_stat(target_id, user_data["currency_type"])
    db.update_user(user_data["currency_type"], current_balance + amount, target_id)

    # Форматируем сумму
    formatted_amount = scr.amount_changer(str(amount))

    await message.answer(
        f"✅ Пользователю @{user_data['username']} выдано {formatted_amount}$!"
    )
    await state.clear()


@router.callback_query(F.data == "give_item")
async def give_item_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✏️ Введите username пользователя (например, @username):"
    )
    await state.set_state(AddItemStates.entering_username)


# Обработка ввода username
@router.message(AddItemStates.entering_username)
async def username_entered(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")  # Убираем @, если есть
    await state.update_data(username=username)  # Сохраняем username

    await message.answer("🎁 Введите название предмета:")
    await state.set_state(AddItemStates.entering_item)


# Обработка ввода предмета
@router.message(AddItemStates.entering_item)
async def item_entered(message: Message, state: FSMContext):
    item = message.text.strip()
    await state.update_data(item=item)  # Сохраняем предмет

    await message.answer("🔢 Введите количество:")
    await state.set_state(AddItemStates.entering_quantity)


# Обработка ввода количества
@router.message(AddItemStates.entering_quantity)
async def quantity_entered(message: Message, state: FSMContext):
    db = Database()
    user_data = await state.get_data()  # Получаем сохраненные данные

    # Проверяем, что количество — число
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат количества. Введите число.")
        return

    # Ищем пользователя
    try:
        target_id = db.get_user_id_by_tgusername('@' + user_data["username"])
    except Exception:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    # Выдаем предмет
    try:
        for _ in range(quantity):
            db.add_item_to_user(target_id, user_data["item"])
    except ValueError as e:
        await message.answer(str(e))
        await state.clear()
        return

    await message.answer(
        f"✅ Пользователю @{user_data['username']} выдано {quantity} предметов '{user_data['item']}'!"
    )
    await state.clear()


# Обработка кнопки "Выдать предмет"
@router.callback_query(F.data == "give_item")
async def give_item_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✏️ Введите username пользователя (например, @username):"
    )
    await state.set_state(AddItemStates.entering_username)


# Обработка ввода username
@router.message(AddItemStates.entering_username)
async def username_entered(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")  # Убираем @, если есть
    await state.update_data(username=username)  # Сохраняем username

    await message.answer("🎁 Введите название предмета:")
    await state.set_state(AddItemStates.entering_item)


# Обработка ввода предмета
@router.message(AddItemStates.entering_item)
async def item_entered(message: Message, state: FSMContext):
    item = message.text.strip()
    await state.update_data(item=item)  # Сохраняем предмет

    await message.answer("🔢 Введите количество:")
    await state.set_state(AddItemStates.entering_quantity)


# Обработка ввода количества
@router.message(AddItemStates.entering_quantity)
async def quantity_entered(message: Message, state: FSMContext):
    db = Database()
    user_data = await state.get_data()  # Получаем сохраненные данные

    # Проверяем, что количество — число
    try:
        quantity = int(message.text)
    except ValueError:
        await message.answer("❌ Неверный формат количества. Введите число.")
        return

    # Ищем пользователя
    try:
        target_id = db.get_user_id_by_tgusername('@' + user_data["username"])
    except Exception:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    # Выдаем предмет
    try:
        for _ in range(quantity):
            db.add_item_to_user(target_id, user_data["item"])
    except ValueError as e:
        await message.answer(str(e))
        await state.clear()
        return

    await message.answer(
        f"✅ Пользователю @{user_data['username']} выдано {quantity} предметов '{user_data['item']}'!"
    )
    await state.clear()


# Обработка кнопки "Обновить предметы"
@router.callback_query(F.data == "update_items")
async def update_items_handler(callback: CallbackQuery):
    db = Database()
    user_id = callback.from_user.id

    if db.get_user_stat(user_id, "is_admin"):
        with open("handlers/admin_handlers/items.json", 'r', encoding='utf-8') as json_data:
            data = loads(json_data.read())
        db.update_items(data)
        await callback.message.answer("✅ Предметы обновлены.", reply_to_message_id=callback.message.message_id)


# Обработка отмены
@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Операция отменена.")