from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDs
from database.methods import get_user_by_tguserid, get_user_by_tgusername, make_admin, update_user
from handlers.init_router import router



@router.message(Command('этоадмин'))
async def pay(message: Message, session: AsyncSession):
    user = await get_user_by_tguserid(session, message.from_user.id)
    command, target_username = message.text.split()

    if int(ADMIN_IDs[0]) == user.tguserid:
        try:
            target = await get_user_by_tgusername(session, target_username)
        except TypeError:
            await message.answer(f'Пользователь с юзом "{target_username}" не найден.',
                                 reply_to_message_id=message.message_id)
            return

        tg_username = target.tgusername
        tg_username = tg_username[1:]

        username = target.username
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

        await make_admin(session, target.tguserid)
        await update_user(session, 'rank', 'Модератор', target.tguserid)
        await message.answer(f'{formated_username} теперь админ!',
                             reply_to_message_id=message.message_id)

    elif user.is_admin and int(ADMIN_IDs[0]) != user.tguserid:
        await message.answer(f'{user.username}, у вас нет прав на это, запросите доступ у @FLARMIX!',
                             reply_to_message_id=message.message_id)

