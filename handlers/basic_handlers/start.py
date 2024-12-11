from aiogram.types import Message
from aiogram.filters import Command
from handlers.init_router import router


@router.message(Command('start'))
async def start_command(message: Message):
    await message.answer('Добро пожаловать в казино!\nЗдесь тебя ждут: Рулетка, слоты, ставки на спорт и многое другое!'
                         '\nНапиши команду /register чтобы зарегистрироваться.')
