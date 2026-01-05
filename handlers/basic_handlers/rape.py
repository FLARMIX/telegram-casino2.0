import random
import re
from datetime import datetime, timedelta

from aiogram import F
from aiogram.types import Message
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from config import Bot_username
from database.methods import get_user_by_tguserid, check_user_in, update_user
from handlers.init_router import router
from scripts.loggers import log
from scripts.scripts import Scripts


@router.message(F.text.regexp(rf'^/?(изнасиловать|rape)(@{Bot_username})?(\s+.*)?$', flags=re.IGNORECASE))
@log("Rape command used")
async def rape_command(message: Message, session: AsyncSession):
    scr = Scripts()
    
    user = await get_user_by_tguserid(session, message.from_user.id)

    if not await check_user_in(session, user.tguserid):
        await message.answer('Вы не зарегистрированы, зарегистрируйтесь через /register',
                             reply_to_message_id=message.message_id)
        return

    # Check cooldown (2 minutes)
    last_mini_bonus_time_str = str(user.last_mini_bonus_time)
    
    if last_mini_bonus_time_str:
        last_mini_bonus_time = datetime.strptime(last_mini_bonus_time_str, '%Y-%m-%d %H:%M:%S')
        time_diff = datetime.now() - last_mini_bonus_time
        
        if time_diff.total_seconds() < 120:  # 2 minutes cooldown
            next_bonus = 120 - time_diff.total_seconds()
            await message.answer(
                f"Следующее изнасилование будет доступно через {int(next_bonus)} секунд!",
                reply_to_message_id=message.message_id
            )
            return

    # Parse the arguments (everything after the command)
    command_parts = message.text.split(maxsplit=1)
    
    if len(command_parts) > 1:
        args_text = command_parts[1]
    else:
        args_text = ""

    # Generate random amount
    # 0.1% chance to get 100,000
    if random.random() < 0.001:  # 0.1% chance
        summ = 100_000
    else:
        summ = random.randint(1_000, 10_000)
    
    # Update user's balance and cooldown
    new_time = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    
    await update_user(session, 'balance_main', user.balance_main + summ, user.tguserid)
    await update_user(session, 'last_mini_bonus_time', new_time, user.tguserid)
    await update_user(session, 'mini_bonus_count', user.mini_bonus_count + 1, user.tguserid)
    
    # Format username
    tg_username = user.tgusername[1:]  # Remove @
    
    if user.is_hidden:
        formatted_username = user.username
    else:
        formatted_username = hlink(user.username, f'https://t.me/{tg_username}')
    
    # Prepare response text depending on whether arguments were provided
    if args_text:
        response_text = f"{formatted_username}, вы изнасиловали {args_text}, и нашли внутри {scr.amount_changer(str(summ))}$!"
    else:
        response_text = f"{formatted_username}, вы совершили изнасилование, и нашли внутри {scr.amount_changer(str(summ))}$!"
    
    # Send response
    await message.answer(
        response_text,
        disable_web_page_preview=True,
        reply_to_message_id=message.message_id
    )