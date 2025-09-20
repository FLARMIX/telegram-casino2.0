import logging

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import Bot_username
from database.SQLmodels import Rank
from database.methods import get_user_by_tguserid, get_user_ranks, get_rank_by_id, change_rank
from handlers.init_router import router

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from scripts.loggers import log

logger = logging.getLogger(__name__)


class PaginationCallback(CallbackData, prefix="pagination"):
    action: str
    page: int


# Функция для создания клавиатуры с пагинацией
def create_pagination_keyboard(ranks: list[Rank], page: int = 0, ranks_per_page: int = 5) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    start_index = page * ranks_per_page
    end_index = start_index + ranks_per_page
    current_ranks = ranks[start_index:end_index]

    for rank in current_ranks:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=rank.rank_name, callback_data=f"rank_{rank.id}")])

    navigation_buttons = []
    total_pages = (len(ranks) + ranks_per_page - 1) // ranks_per_page

    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=PaginationCallback(action="rank_previous", page=page - 1).pack()
            )
        )

    if page < total_pages - 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=PaginationCallback(action="rank_next", page=page + 1).pack()
            )
        )

    if navigation_buttons:
        keyboard.inline_keyboard.append(navigation_buttons)

    return keyboard


@router.message(F.text.lower().in_(["ранг", "rank", "/ранг", "/rank", f'/rank@{Bot_username}']))
@log("Now, this person changing a rank. I'm logging!")
async def change_rank_command(message: Message, state: FSMContext, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, message.from_user.id)

    user_ranks = await get_user_ranks(session, user.tguserid)

    keyboard = create_pagination_keyboard(user_ranks)
    await message.answer('Выбери ранг:', reply_markup=keyboard)
    await state.update_data(user_id=user.tguserid)


@router.callback_query(F.data.startswith("rank_"))
async def select_rank(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)

    rank_id = int(callback.data.split('_')[1])

    data = await state.get_data()

    if 'user_id' not in data or data['user_id'] != user.tguserid:
        await callback.answer("Это не ваша кнопка!", show_alert=True)
        return

    rank = await get_rank_by_id(session, rank_id)

    await change_rank(session, rank, user.tguserid)

    await bot.send_message(callback.message.chat.id, f"Вы выбрали ранг {rank.rank_name}!", reply_to_message_id=callback.message.message_id)


@router.callback_query(PaginationCallback.filter(F.action.in_(["rank_next", "rank_previous"])))
async def handle_rank_pagination(callback: CallbackQuery, state: FSMContext, callback_data: PaginationCallback, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)
    data = await state.get_data()
    page = callback_data.page

    if 'user_id' not in data or data['user_id'] != user.tguserid:
        await callback.answer("Это не ваша кнопка!", show_alert=True)
        return

    user_ranks = await get_user_ranks(session, user.tguserid)

    keyboard = create_pagination_keyboard(user_ranks, page)

    await callback.message.edit_text(text="Выберите ранг:", reply_markup=keyboard)
    await callback.answer()