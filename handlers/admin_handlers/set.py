from aiogram import F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDs
from database.methods import get_user_by_tguserid, get_user_by_tgusername, update_user
from handlers.init_router import router
from scripts.loggers import log
from scripts.scripts import Scripts


@router.message(F.text.lower().startswith(('сет', 'set', '/сет', '/set')))
@log("I'm logging you, my Lord...")
async def set(message: Message, session: AsyncSession):
    scr = Scripts()
    user = await get_user_by_tguserid(session, message.from_user.id)
    is_you = False
    if str(user.tguserid) in ADMIN_IDs:
        command, which_balance, target_username, amount = message.text.split()
        amount = scr.unformat_number(scr.amount_changer(amount))
        if target_username.lower() == 'я':
            target_user = user
            is_you = True
        else:
            target_user = await get_user_by_tgusername(session, target_username)
            if not target_user.tguserid:
                await message.answer(f"Пользователь с ником '{target_username}' не найден.",
                                     reply_to_message_id=message.message_id)
                return

        if which_balance in ["m", "м"]:
            balance_type = "balance_main"
            msg = "$"
        elif which_balance in ["a", "а"]:
            balance_type = "balance_alt"
            msg = ' "Word Of Alternative Balance"'
        else:
            await message.answer("Используйте /set m для основного баланса или /set a для альтернативного.",
                                 reply_to_message_id=message.message_id)
            return

        if target_user.tguserid:
            await update_user(session, balance_type, int(amount), target_user.tguserid)
            if is_you:
                await message.answer(f"Вы установили себе {scr.amount_changer((str(amount)))}{msg}")
            else:
                await message.answer(f"Вы установили {scr.amount_changer((str(amount)))}{msg} пользователю "
                                     f"{target_username}",
                                     reply_to_message_id=message.message_id)

    elif user.is_admin:
        await message.answer("Вы явлеетесь модератором, команда доступна только администрации.",
                             reply_to_message_id=message.message_id)
