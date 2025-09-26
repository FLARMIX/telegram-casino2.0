import re

from aiogram import Bot, F
from aiogram.types import Message

from config import HELP_COMMAND_TEXT
from handlers.init_router import router
from scripts.loggers import log

@router.message(F.text.regexp(r'^/?(помощь|хелп|help)$', flags=re.IGNORECASE))
@log('We are in help command, and I search bugs!')
async def help_command(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    message_text = HELP_COMMAND_TEXT

    await bot.send_message(user_id, message_text, parse_mode=None)