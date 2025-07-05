from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, check_user_in, update_user
from handlers.init_router import router

from scripts.scripts import Scripts


@router.message(Command('бонус'))
@router.message(Command('bonus'))
async def bonus(message: Message, session: AsyncSession):
    scr = Scripts()

    user = await get_user_by_tguserid(session, message.from_user.id)

    if not await check_user_in(session, user.tguserid):
        await message.answer('Вы не зарегистрированы, зарегистрируйтесь через /register',
                             reply_to_message_id=message.message_id)
        return

    tg_username = user.tgusername
    tg_username = tg_username[1:]

    is_hidden = user.is_hidden
    username = user.username

    if is_hidden:
        formated_username = username
    else:
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

    balance_main = user.balance_main
    last_bonus_time_str = str(user.last_bonus_time)  # Получаем строку из БД

    if last_bonus_time_str:
        # Преобразуем строку в объект datetime
        last_bonus_time = datetime.strptime(last_bonus_time_str, '%Y-%m-%d %H:%M:%S')
        time_diff = datetime.now() - last_bonus_time
        if time_diff.total_seconds() < 1800:
            next_bonus = 1800 - time_diff.total_seconds()
            await message.answer(
                f"{formated_username}, следующий бонус через {int(next_bonus)} сек.!",
                disable_web_page_preview=True,
                reply_to_message_id=message.message_id
            )
            return

    BONUS_AMOUNT = 500_000_000

    new_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

    await update_user(session, 'balance_main', balance_main + BONUS_AMOUNT, user.tguserid)
    # Сохраняем текущее время как строку в формате БД
    await update_user(session, 'last_bonus_time', new_time, user.tguserid)
    await update_user(session, 'bonus_count', user.bonus_count + 1, user.tguserid)

    await message.answer(
        f"{formated_username}, вам начислен бонус {scr.amount_changer(str(BONUS_AMOUNT))}$!",
        disable_web_page_preview=True,
        reply_to_message_id=message.message_id
    )
