from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import logging

from handlers.init_router import router
from database.database import Database
from scripts.scripts import Scripts


logger = logging.getLogger(__name__)


@router.inline_query()
async def inline_roulette(inline_query: InlineQuery):
    db = Database()
    scr = Scripts()

    user_id = inline_query.from_user.id
    balance_main = db.get_user_stat(user_id, "balance_main")

    # Получаем текст запроса (ставка и тип ставки)
    query = inline_query.query.strip()
    if query == "я":
        if not db.get_user_by_tgid(user_id):
            result_text = "Вы не зарегистрированы, используйте /register"
        else:
            balance_main = str(db.get_user_stat(user_id, "balance_main"))
            balance_alt = str(db.get_user_stat(user_id, "balance_alt"))
            bonus_count = str(db.get_user_stat(user_id, "bonus_count"))
            mini_bonus_count = str(db.get_user_stat(user_id, "mini_bonus_count"))

            # Получаем список предметов (без картинок)
            items = db.get_user_items(user_id)
            avatar_items = {item: count for item, count in items.items() if db.get_item_type(item) == "avatar"}
            property_items = {item: count for item, count in items.items() if db.get_item_type(item) != "avatar"}

            result_text = (
                f'💰 Ваш Баланс: {scr.amount_changer(balance_main)}$\n'
                f'💰 "Word Of Alternative Balance": {scr.amount_changer(balance_alt)}\n'
                f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
                f'🤶🏻 Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}\n'
                f'🎒 Витринные предметы: {", ".join([f"{item} (x{count})" for item, count in avatar_items.items()])}\n'
                f'📦 Имущество: {", ".join([f"{item} (x{count})" for item, count in property_items.items()])}'
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

    if not db.check_user_in(user_id):
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
            description=f"У вас недостаточно средств! Ваш баланс: {scr.amount_changer(balance_main)}$",
            input_message_content=InputTextMessageContent(
                message_text=f"У вас недостаточно средств! Ваш баланс: {scr.amount_changer(balance_main)}$"
            )
        )
        await inline_query.answer([result], cache_time=1)
        return

    # Обновляем баланс пользователя
    db.update_user("balance_main", balance_main - int_amount, user_id)
    new_balance = db.get_user_stat(user_id, 'balance_main')

    # Симуляция результата рулетки
    if stack in ['черное', 'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт']:
        status, number = scr.roulette_randomizer(stack)
        current_stack = scr.pic_color(number)
        if status:
            win_amount = int_amount * 2
            db.update_user('balance_main', new_balance + win_amount, user_id)
            current_balance = db.get_user_stat(user_id, "balance_main")
            result_text = (
                f"🎉 [{stack} {amount}] {number} - {current_stack.capitalize()}! Ставка x2! Вы выиграли "
                f"{scr.amount_changer(str(win_amount))}$!\n"
                f"Ваш баланс: {scr.amount_changer(str(current_balance))}$"
            )
        else:
            current_balance = db.get_user_stat(user_id, "balance_main")
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
            db.update_user('balance_main', new_balance + win_amount, user_id)
            current_balance = db.get_user_stat(user_id, "balance_main")
            result_text = (
                f"🎉 [{stack} {amount}] {number} - {current_stack.capitalize()}! Ставка x36🤑!!! Вы выиграли "
                f"{scr.amount_changer(str(win_amount))}$!\n"
                f"Ваш баланс: {scr.amount_changer(str(current_balance))}$"
            )
        else:
            current_balance = db.get_user_stat(user_id, "balance_main")
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