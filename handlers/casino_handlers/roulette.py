import re

from aiogram import Bot, F
from aiogram.types import Message
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from config import Bot_username
from database.methods import get_user_by_tguserid, get_user_stat, check_user_in, update_user
from handlers.init_router import router
from scripts.loggers import log

from scripts.scripts import Scripts


STACKS = r"(?:красное|черное|чёрное|зеро|чет|чёт|нечет|нечёт)"
AMOUNT = r"(?P<amount>(?:вс[её])|\d+(?:[.,]\d+)?[кk]*)"  # 200, 200к/200k, 2m, "все/всё"

ROULETTE_RE = re.compile(
    rf"^/?(?:рулетка|рул|roulette|rul|roulette@{re.escape(Bot_username)}|rul@{re.escape(Bot_username)})\s+"
    rf"(?P<stack>{STACKS})(?:\s+{AMOUNT})?\s*$",
    re.IGNORECASE,
)


@router.message(F.text.regexp(ROULETTE_RE).as_("m"))
@log("If in this roulette has an error, then here is the log UwU")
async def roulette(message: Message, bot: Bot, session: AsyncSession, m: re.Match):
    scr = Scripts()

    stack = m.group("stack").lower()
    amount = m.group("amount")

    if amount is None:
        await message.answer("Укажите сумму ставки!", reply_to_message_id=message.message_id)

    user = await get_user_by_tguserid(session, message.from_user.id)
    user_id = user.tguserid

    tg_username = await get_user_stat(session, user_id, "tgusername")
    tg_username = tg_username[1:]

    balance_main = user.balance_main
    is_hidden = user.is_hidden
    username = user.username

    if is_hidden:
        formated_username = username
    else:
        formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

    user_channel_status = await scr.check_channel_subscription(bot, user_id)

    if not await scr.check_channel_subscription(bot, user.tguserid):
        await message.answer('Вы не подписаны на канал, подпишитесь на канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться.',
                             reply_to_message_id=message.message_id)
        return

    if not await check_user_in(session, user_id):
        await message.answer("Вы не зарегистрированы, пожалуйста, зарегистрируйтесь с помощью /register",
                             reply_to_message_id=message.message_id)
        return

    if amount in ['все', 'всё']:
        amount = str(balance_main)

    int_amount = scr.unformat_number(scr.amount_changer(amount))

    if int_amount <= 0:
        await message.answer("Сумма ставки должна быть больше 0!",
                             reply_to_message_id=message.message_id)
        return

    if balance_main < int_amount:
        await message.answer(f"У вас недостаточно средств!\nВаш баланс {scr.amount_changer(str(balance_main))}",
                             reply_to_message_id=message.message_id)
        return

    await update_user(session, "balance_main", balance_main - int_amount, user_id)

    if stack in ['черное', 'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт']:
        status, number = scr.roulette_randomizer(stack)
        current_stack = scr.pic_color(number)
        if status:
            before_balance = await get_user_stat(session, user_id, "balance_main")
            await update_user(session, 'balance_main', before_balance + int_amount * 2, user_id)
            current_balance = await get_user_stat(session, user_id, "balance_main")

            await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Ставка x2 "
                                 f"{scr.randomize_emoji(win=True)}, вы выиграли "
                                 f"{scr.amount_changer(str(int_amount * 2))}$"
                                 f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                 disable_web_page_preview=True, reply_to_message_id=message.message_id)
            await update_user(session, "balance_main", balance_main + int_amount, user_id)
        else:
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Вы проиграли "
                                 f"{scr.amount_changer(str(int_amount))}$ {scr.randomize_emoji(win=False) * 2}"
                                 f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                 disable_web_page_preview=True, reply_to_message_id=message.message_id)
    elif stack in ['зеро']:
        status, number = scr.roulette_randomizer(stack)
        current_stack = scr.pic_color(number)
        if status:
            before_balance = await get_user_stat(session, user_id, "balance_main")
            await update_user(session, 'balance_main', before_balance + int_amount * 42, user_id)
            current_balance = await get_user_stat(session, user_id, "balance_main")

            current_zero_count = user.roulette_zero_count
            await update_user(session, 'roulette_zero_count', current_zero_count + 1, user_id)

            await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Ставка x42🤑!!! "
                                 f"вы выиграли "
                                 f"{scr.amount_changer(str(int_amount * 42))}$"
                                 f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                 disable_web_page_preview=True, reply_to_message_id=message.message_id)
        else:
            current_balance = await get_user_stat(session, user_id, 'balance_main')
            await message.answer(f"{formated_username}, {number} - {current_stack.capitalize()}! Вы проиграли "
                                 f"{scr.amount_changer(str(int_amount))}$ {scr.randomize_emoji(win=False) * 2}"
                                 f"\nБаланс: {scr.amount_changer(str(current_balance))}$",
                                 disable_web_page_preview=True, reply_to_message_id=message.message_id)
    else:
        await update_user(session, "balance_main", balance_main + int_amount, user_id)
        await message.answer(f"Ошибка! Неправильно указан стек. Вы можете использовать 'черное', "
                             f"'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт' или 'зеро'.",
                             reply_to_message_id=message.message_id)


@router.message(F.text.regexp(f"^/?(рулетка|рул|roulette|rul|roulette@{Bot_username})(?:\s|$)", flags=re.IGNORECASE))
@log("If in this roulette has an error, then here is the log UwU")
async def roulette_no_stack(message: Message):
    await message.answer("Неверный формат команды. Пример:\n\n/rul красное 101\nрулетка чёт 200к\nрул зеро все\n\n"
                         "Все текущие стеки: 'черное', 'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт' или 'зеро'.")

