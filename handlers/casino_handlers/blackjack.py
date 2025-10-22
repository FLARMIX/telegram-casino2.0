import asyncio
import re

from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, get_user_stat, update_user, create_blackjack_game, update_blackjack_game, delete_blackjack_game
from handlers.init_router import router
from scripts.loggers import log
from scripts.media_cache import file_cache_original

from scripts.scripts import Scripts


@router.message(F.text.regexp("^/?(блэкджек|blackjack|g21|г21)", flags=re.IGNORECASE))
@log("We are enter in blackjack, i'm logging it!")
async def blackjack_game(message: Message, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    scr = Scripts()
    user_id = message.from_user.id
    user = await get_user_by_tguserid(session, user_id)

    message_text = message.text
    message_text = message_text.split()
    len_text = len(message_text)

    user_channel_status = await scr.check_channel_subscription(bot, user_id)

    if not await scr.check_channel_subscription(bot, user.tguserid):
        await message.answer('Вы не подписаны на канал, подпишитесь на канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться.',
                             reply_to_message_id=message.message_id)
        return

    if not await scr.check_registered(user, message):
        return

    if len_text != 3:
        await message.answer(
            'Используй:\n'
            '<i>/blackjack</i> <b>@имя_пользователя</b> <b>value</b>'
            '\n\n💡Пример:'
            '\n\n<i>/blackjack</i> <b>@FLARMIX</b> <b>500к</b>'
            '\n<i>г21</i> <b>@FLARMIX</b> <b>10000</b>',
            parse_mode='HTML'
        )
        return

    cmd, target_username, bet_value = message_text

    balance_main = user.balance_main
    is_hidden = user.is_hidden
    username = user.username
    tg_username = user.tgusername

    if is_hidden:
        formated_username = username
    else:
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')


    if bet_value in ['все', 'всё']:
        amount = str(balance_main)

    int_amount = scr.unformat_number(scr.amount_changer(amount))

    if int_amount <= 0:
        await message.answer("Сумма ставки должна быть больше 0!",
                             reply_to_message_id=message.message_id)
        return

