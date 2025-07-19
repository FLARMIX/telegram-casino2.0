from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDs, Bot_username
from database.methods import get_user_by_tguserid, update_username, update_user
from handlers.init_router import router
from scripts.loggers import log


@router.message(F.text.lower().startswith(('ник', 'nick', '/ник', '/nick')))
@log("Logging nickname command.")
async def nickname(message: Message, state: FSMContext, session: AsyncSession):
    user = await get_user_by_tguserid(session, message.from_user.id)
    temp_list = message.text.split()

    if len(temp_list) == 1:
        if not user.is_hidden:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Скрыть ник", callback_data="hide_nick")]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Показать ник", callback_data="show_nick")]
            ])

        sent_message = await message.answer(
            text="Выберите действие:",
            reply_markup=keyboard,
            reply_to_message_id=message.message_id
        )
        await state.update_data(sent_message_id=sent_message.message_id, message_id=message.message_id)
        return

    elif len(temp_list) == 2:
        command, username = message.text.split()
    else:
        username = ' '.join(message.text.split()[1:])

    if user.is_admin:
        if str(user.tguserid) in ADMIN_IDs[0]:
            await update_username(session, username, user.tguserid)
            await message.answer(f"Ты успешно установили имя {username}!")
            return

        elif user.is_admin and len(username) > 55:
            await message.answer("Имя админа не может быть длиннее 55 символов!")
            return

        elif user.is_admin and len(username) < 3:
            await message.answer("Имя не может быть короче 3 символов!")
            return

    elif len(username) > 20:
        await message.answer("Имя не может быть длиннее 20 символов!")
        return

    elif len(username) < 3:
        await message.answer("Имя не может быть короче 3 символов!")
        return

    await update_user(session, "username", username, user.tguserid)
    await message.answer(f"Вы успешно установили имя {username}!")

@router.callback_query(F.data == "hide_nick")
async def hide_nick(callback: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['sent_message_id'])
    await update_user(session, "is_hidden", True, callback.from_user.id)

    await callback.message.answer(text="Ник скрыт от чужих глаз 👀", reply_to_message_id=data['message_id'])


@router.callback_query(F.data == "show_nick")
async def show_nick(callback: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=data['sent_message_id'])
    await update_user(session, "is_hidden", False, callback.from_user.id)

    await callback.message.answer(text="Ник показан всем 👀", reply_to_message_id=data['message_id'])
