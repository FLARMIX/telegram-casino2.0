from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from datetime import datetime

from handlers.init_router import router

from aiogram.utils.keyboard import InlineKeyboardBuilder


@router.message(Command("enslave"))
@router.message(Command("поработить"))
async def enslave(message: Message):
    db = Database()
    user_id = message.from_user.id
    if not await db.check_user_in(user_id):
        await message.answer('Сначала зарегистрируйтесь: /register')
        return

    command, target_username = message.text.split()
    target_user = await db.get_user_by_tgusername(target_username)
    if not await db.check_user_in(target_user.id):
        await message.answer('Такого пользователя не существует!')
        return

    if await db.start_slavery(user_id, target_user.id) == "success":
        username = target_user.username
        formated_username = hlink(f'{username}', f'https://t.me/{target_username}')
        await message.answer(f'{formated_username} '
                             f'теперь ваш раб!',
                             reply_to_message_id=message.message_id)
        return
    else:
        await message.answer('Вы уже имеете раба!')

@router.message(Command("slavery"))
@router.message(Command("рабство"))
async def slavery(message: Message):
    db = Database()
    user_id = message.from_user.id

    if not await db.check_user_in(user_id):
        await message.answer('Сначала зарегистрируйтесь: /register')
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🛠 Мой раб", callback_data="slave_info")
    builder.button(text="💰 Копилка", callback_data="piggy_bank")
    builder.button(text="⏳ Остаток времени", callback_data="time_left")
    builder.adjust(2, 1)

    await message.answer(
        "🏛 Меню рабства:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("slave_info"))
async def slave_info(callback: CallbackQuery):
    db = Database()
    slavery_info = await db.get_slavery_info(callback.from_user.id)

    if not slavery_info:
        await callback.answer("У вас нет раба!")
        return

    slave_data = await db.get_user_by_tguserid(slavery_info[1])
    text = (
        f"🔗 Раб: {slave_data[1]}\n"
        f"💸 Баланс раба: {slave_data[2]}$\n"
        f"📦 Копилка: {slavery_info[4]}$"
    )
    await callback.message.edit_text(text)


@router.callback_query(F.data.startswith("piggy_bank"))
async def piggy_bank(callback: CallbackQuery):
    db = Database()
    user_id = callback.from_user.id
    withdrawn = await db.withdraw_piggy_bank(user_id)
    slavery_info = await db.get_slavery_info(user_id)

    if not slavery_info:
        await callback.answer("У вас нет раба!")
        return

    if withdrawn is False:
        await callback.answer("Снимать можно раз в сутки!")
    else:
        await db.update_user("balance_main", await db.get_user_stat(callback.from_user.id, "balance_main") + withdrawn, user_id)
        await callback.answer(f"Снято {withdrawn}$!")