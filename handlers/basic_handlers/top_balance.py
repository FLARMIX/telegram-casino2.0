import re

from aiogram import Bot, F
from aiogram.types import Message
from aiogram.utils.markdown import hlink
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.SQLmodels import User
from handlers.init_router import router
from scripts.loggers import log
from scripts.scripts import Scripts


@router.message(F.text.regexp(r'^/?топ|top$', flags=re.IGNORECASE))
@log('Top balance command')
async def top_balance(message: Message, bot: Bot, session: AsyncSession) -> None:
    user_id = message.from_user.id
    
    stmt = select(User).order_by(User.balance_main.desc()).limit(10)
    result = await session.execute(stmt)
    top_users = result.scalars().all()
    
    scr = Scripts()
    
    rating_text = "🏆 ТОП 10 САМЫХ БОГАТЫХ 🏆\n\n"
    
    for i, user in enumerate(top_users, 1):
        position = f"{i}. "
        
        if user.is_hidden:
            username = user.username
        else:
            if user.tgusername and user.tgusername != "@":
                username = hlink(f'{user.username}', f'https://t.me/{user.tgusername[1:]}')
            else:
                username = user.username
        
        balance = scr.amount_changer(str(user.balance_main))
        
        rating_text += f"{position}{username} - {balance}$\n"
    
    await bot.send_message(user_id, rating_text, parse_mode=None)