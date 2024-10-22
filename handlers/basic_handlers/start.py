from aiogram.types import Message
from aiogram.filters import Command
from handlers.init_router import router


@router.message(Command('start'))
async def start_command(message: Message):
    await message.answer('TEST NEW BOT')
