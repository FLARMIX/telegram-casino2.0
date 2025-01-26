from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink

from datetime import datetime

from handlers.init_router import router

from database.database import Database
from scripts.scripts import Scripts


@router.message(Command('бонус'))
@router.message(Command('bonus'))
async def bonus(message: Message):
    db = Database()
    scr = Scripts()

    user_id = message.from_user.id

    if not db.check_user_in(user_id):
        await message.answer('Вы не зарегистрированы, зарегистрируйтесь через /register',
                             reply_to_message_id=message.message_id)
        return

    balance_main = db.get_user_stat(user_id, 'balance_main')
    last_bonus_time_str = db.get_user_stat(user_id, 'last_bonus_time')  # Получаем строку из БД
    username = db.get_user_stat(user_id, "username")
    tg_username = db.get_user_stat(user_id, "tgusername")[1:]
    formated_name = hlink(f'{username}', f'https://t.me/{tg_username}')

    if last_bonus_time_str:
        # Преобразуем строку в объект datetime
        last_bonus_time = datetime.strptime(last_bonus_time_str, '%Y-%m-%d %H:%M:%S')
        time_diff = datetime.now() - last_bonus_time
        if time_diff.total_seconds() < 1800:
            next_bonus = 1800 - time_diff.total_seconds()
            await message.answer(
                f"{formated_name}, следующий бонус через {int(next_bonus)} сек.!",
                disable_web_page_preview=True,
                reply_to_message_id=message.message_id
            )
            return

    BONUS_AMOUNT = 50000
    db.update_user('balance_main', balance_main + BONUS_AMOUNT, user_id)
    # Сохраняем текущее время как строку в формате БД
    db.update_user('last_bonus_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id)
    db.update_user('bonus_count', db.get_user_stat(user_id, 'bonus_count') + 1, user_id)

    await message.answer(
        f"{formated_name}, вам начислен бонус {scr.amount_changer(str(BONUS_AMOUNT))}$!",
        disable_web_page_preview=True,
        reply_to_message_id=message.message_id
    )
