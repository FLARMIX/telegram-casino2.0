from aiogram import Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDs
from database.methods import get_user_by_tguserid, get_user_stat, get_user_items, get_item_by_name, check_user_in, \
    update_user
from database.models import ItemType
from handlers.init_router import router
from scripts.scripts import Scripts

logger = logging.getLogger(__name__)


@router.inline_query()
async def inline_roulette(inline_query: InlineQuery, bot: Bot, session: AsyncSession):
    scr = Scripts()

    user = await get_user_by_tguserid(session, inline_query.from_user.id)
    user_id = user.tguserid
    balance_main = user.balance_main

    user_channel_status = await scr.check_channel_subscription(bot, user_id)

    if not user_channel_status:
        result = InlineQueryResultArticle(
            id="1",
            title="Подпишись прежде чем играть!",
            descriprion='Вы не подписаны на канал, подпишитесь на мой канал @PidorsCasino'
                        '\nЧтобы получить доступ к боту, вам необходимо подписаться на мой канал.',
            input_message_content=InputTextMessageContent(
                message_text="Вы не подписаны на канал, подпишитесь на мой канал @PidorsCasino"
                             "\nЧтобы получить доступ к боту, вам необходимо подписаться на мой канал."
            )
        )
        await inline_query.answer([result], cache_time=1)
        return

    # Получаем текст запроса (ставка и тип ставки)
    query = inline_query.query.strip()
    if query == "я":
        if not await get_user_by_tguserid(session, user_id):
            result_text = "Вы не зарегистрированы, используйте /register в боте!"
        else:
            user = await get_user_by_tguserid(session, user_id)
            balance_main = str(user.balance_main)
            balance_alt = str(user.balance_alt)
            bonus_count = str(user.bonus_count)
            mini_bonus_count = str(user.mini_bonus_count)
            rank = user.rank

            # Получаем список предметов (без картинок)
            items = await get_user_items(session, user_id)
            avatar_items = dict()
            property_items = dict()

            for item, count in items.items():
                item_obj = await get_item_by_name(session, item)
                if item_obj.item_type == ItemType.AVATAR:
                    avatar_items[item] = count

            for item, count in items.items():
                item_obj = await get_item_by_name(session, item)
                if item_obj.item_type != ItemType.AVATAR:  # TODO: != ItemType.AVATAR <- костыль, нужно исправить в будущем.
                    property_items[item] = count

            result_text = (
                f'💰 Ваш Баланс: {scr.amount_changer(balance_main)}$\n'
                f'💰 "Word Of Alternative Balance": {scr.amount_changer(balance_alt)}\n'
                f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
                f'🤶🏻 Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}\n'
                f'🎒 Витринные предметы: {", ".join([f"{item} (x{count})" for item, count in avatar_items.items()])}\n'
                f'📦 Имущество: {", ".join([f"{item} (x{count})" for item, count in property_items.items()])}\n'
                f'💻 Ранг: {rank}'
            )

        result = InlineQueryResultArticle(
            id="1",
            title="Ваш профиль",
            description="Посмотреть информацию о себе",
            input_message_content=InputTextMessageContent(
                message_text=result_text, parse_mode="HTML"
            )
        )
        await inline_query.answer([result], cache_time=1)
        return

    try:
        stack, amount = query.split()  # Разделяем запрос на тип ставки и сумму
    except ValueError:
        # Если запрос некорректен, отправляем подсказку
        result = InlineQueryResultArticle(
            id="1",
            title="Ошибка",
            description="Используйте формат: <ставка> <сумма> (например, 'красное 100к')",
            input_message_content=InputTextMessageContent(
                message_text="Используйте формат: <ставка> <сумма> (например, 'красное 100к')"
            )
        )
        await inline_query.answer([result], cache_time=1)
        return

    if not await check_user_in(session, user_id):
        result = InlineQueryResultArticle(
            id="1",
            title="Ошибка",
            description="Вы не зарегистрированы. Используйте /register в чате с ботом.",
            input_message_content=InputTextMessageContent(
                message_text="Вы не зарегистрированы. Используйте /register в чате с ботом."
            )
        )
        await inline_query.answer([result], cache_time=1)
        return

    if amount in ['все', 'всё']:
        amount = str(balance_main)

    int_amount = scr.unformat_number(scr.amount_changer(amount))

    if int_amount <= 0:
        result = InlineQueryResultArticle(
            id="1",
            title="Ошибка",
            description="Сумма ставки должна быть больше 0!",
            input_message_content=InputTextMessageContent(
                message_text="Сумма ставки должна быть больше 0!"
            )
        )
        await inline_query.answer([result], cache_time=1)
        return

    if balance_main < int_amount:
        result = InlineQueryResultArticle(
            id="1",
            title="Ошибка",
            description=f"У вас недостаточно средств! Ваш баланс: {scr.amount_changer(str(balance_main))}$",
            input_message_content=InputTextMessageContent(
                message_text=f"У вас недостаточно средств! Ваш баланс: {scr.amount_changer(str(balance_main))}$"
            )
        )
        await inline_query.answer([result], cache_time=1)
        return

    # Обновляем баланс пользователя
    await update_user(session, "balance_main", balance_main - int_amount, user_id)
    new_balance = await get_user_stat(session, user_id, 'balance_main')

    # Симуляция результата рулетки
    if stack in ['черное', 'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт']:
        status, number = scr.roulette_randomizer(stack)
        current_stack = scr.pic_color(number)
        if status:
            win_amount = int_amount * 2
            await update_user(session, 'balance_main', new_balance + win_amount, user_id)
            current_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"🎉 [{stack} {amount}] {number} - {current_stack.capitalize()}! Ставка x2! Вы выиграли "
                f"{scr.amount_changer(str(win_amount))}$!\n"
                f"Ваш баланс: {scr.amount_changer(str(current_balance))}$"
            )
        else:
            current_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"😢 [{stack} {amount}] {number} - {current_stack.capitalize()}! Вы проиграли "
                f"{scr.amount_changer(str(int_amount))}$.\n"
                f"Ваш баланс: {scr.amount_changer(str(current_balance))}$"
            )
    elif stack in ['зеро']:
        status, number = scr.roulette_randomizer(stack)
        current_stack = scr.pic_color(number)
        if status:
            win_amount = int_amount * 36
            await update_user(session, 'balance_main', new_balance + win_amount, user_id)
            current_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"🎉 [{stack} {amount}] {number} - {current_stack.capitalize()}! Ставка x36🤑!!! Вы выиграли "
                f"{scr.amount_changer(str(win_amount))}$!\n"
                f"Ваш баланс: {scr.amount_changer(str(current_balance))}$"
            )
        else:
            current_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"😢 [{stack} {amount}] {number} - {current_stack.capitalize()}! Вы проиграли "
                f"{scr.amount_changer(str(int_amount))}$.\n"
                f"Ваш баланс: {scr.amount_changer(str(current_balance))}$"
            )
    else:
        result_text = (
            f"Ошибка! Неправильно указан стек. Используйте 'черное', 'чёрное', 'красное', "
            f"'чет', 'чёт', 'нечет', 'нечёт' или 'зеро'."
        )

    # Отправляем результат в виде inline-результата
    result = InlineQueryResultArticle(
        id="1",
        title="Результат рулетки",
        description=result_text,
        input_message_content=InputTextMessageContent(
            message_text=result_text
        )
    )

    await inline_query.answer([result], cache_time=0)  # Отключаем кэширование для тестов
