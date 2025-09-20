import re
from uuid import uuid4

from aiogram import Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDs
from database.SQLmodels import Rank
from scripts.scripts import Scripts
from scripts.loggers import log
from handlers.init_router import router

from aiogram.utils.markdown import hlink


from database.methods import (
    get_user_by_tguserid,
    get_user_stat,
    get_dict_user_items,
    get_item_by_name,
    update_user, get_items_by_names, get_user_avatar, get_user_rank,
)
from database.models import ItemType

COLOR_STACKS = {'черное', 'чёрное', 'красное', 'чет', 'чёт', 'нечет', 'нечёт'}
ZERO_STACK = 'зеро'


@router.inline_query()
@log("Finding errors in inline roulette :)")
async def inline_roulette(inline_query: InlineQuery, bot: Bot, session: AsyncSession):
    scr = Scripts()
    query = (inline_query.query or "").strip()

    # ---------- минимальные проверки ----------
    # получаем пользователя (в базе)
    user = await get_user_by_tguserid(session, inline_query.from_user.id)
    if not user:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Вы не зарегистрированы",
            description="Используйте /register в боте, чтобы начать играть.",
            input_message_content=InputTextMessageContent(
                message_text="Вы не зарегистрированы, используйте /register в боте."
            ),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    user_id = user.tguserid

    # проверяем подписку на канал
    if not await scr.check_channel_subscription(bot, user_id):
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Подпишитесь на канал",
            description="Чтобы получить доступ — подпишитесь на @PidorsCasino.",
            input_message_content=InputTextMessageContent(
                message_text="Вы не подписаны на канал @PidorsCasino. Подпишитесь, чтобы получить доступ к боту."
            ),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    # --- админская команда: "сет <сумма>" ---
    if query.lower().startswith("сет"):
        # если не админ — вежливо отвечаем и выходим
        if str(user_id) not in ADMIN_IDs:
            result = InlineQueryResultArticle(
                id=str(uuid4()),
                title="Нет доступа",
                description="Команда доступна только администраторам.",
                input_message_content=InputTextMessageContent(
                    message_text="⛔ Команда доступна только администраторам."
                ),
            )
            await inline_query.answer([result], cache_time=0, is_personal=True)
            return

        # ожидаем формат: "сет <сумма>"
        parts = query.split(None, 1)
        if len(parts) == 1:
            result = InlineQueryResultArticle(
                id=str(uuid4()),
                title="Укажите сумму",
                description="Формат: сет <сумма> (например: 'сет 100к' или 'сет 2kk')",
                input_message_content=InputTextMessageContent(
                    message_text="Укажите сумму: пример 'сет 100к' или 'сет 2kk'"
                ),
            )
            await inline_query.answer([result], cache_time=0, is_personal=True)
            return

        amount = parts[1].lower().strip()

        # special: "все"/"всё"
        if amount in ("все", "всё"):
            current_balance = await get_user_stat(session, user_id, "balance_main")
            amount = str(current_balance)

        # парсим сумму через Scripts
        try:
            int_amount = scr.unformat_number(scr.amount_changer(amount))
        except Exception:
            result = InlineQueryResultArticle(
                id=str(uuid4()),
                title="Неверная сумма",
                description="Не удалось распознать сумму. Пример: 100, 100к, 2kk",
                input_message_content=InputTextMessageContent(
                    message_text="Не удалось распознать сумму. Пример: 100, 100к, 2kk"
                ),
            )
            await inline_query.answer([result], cache_time=0, is_personal=True)
            return

        if int_amount <= 0:
            result = InlineQueryResultArticle(
                id=str(uuid4()),
                title="Неверная сумма",
                description="Сумма должна быть больше 0.",
                input_message_content=InputTextMessageContent(
                    message_text="Сумма должна быть > 0."
                ),
            )
            await inline_query.answer([result], cache_time=0, is_personal=True)
            return

        await update_user(session, "balance_main", int_amount, user_id)

        result_text = f"[Команда Гл. Админов] Вы поставили себе: {scr.amount_changer(int_amount)}$"
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Баланс обновлён",
            description=(result_text[:200] if len(result_text) > 200 else result_text),
            input_message_content=InputTextMessageContent(message_text=result_text),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return  # <<< критично: не проваливаемся в разбор ставок ниже



    if query == "":
        # если пусто — показываем подсказку
        hint = ("Используйте формат: <ставка> <сумма>\n"
                "Примеры:\n"
                "красное 100к\n"
                "чёт 200\n"
                "зеро все")
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Как играть",
            description="Пример: 'красное 100к' или 'зеро все'",
            input_message_content=InputTextMessageContent(message_text=hint),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    # если запрос = "я" — показываем профиль
    if query.lower() == "я":
        # обновляем данные пользователя на случай изменений
        user = await get_user_by_tguserid(session, user_id)

        # предметы (без картинок)
        items = await get_dict_user_items(session, user_id)
        avatar_items = {}
        property_items = {}
        for item, count in items.items():
            item_obj = await get_item_by_name(session, item)
            if item_obj.item_type == ItemType.AVATAR:
                avatar_items[item] = count
            else:
                property_items[item] = count

        tg_username = user.tgusername
        tg_username = tg_username[1:]

        is_hidden = user.is_hidden
        username = user.username

        if is_hidden:
            formated_username = username
        else:
            formated_username = hlink(f'{username}', f'https://t.me/{tg_username}')

        balance_main = str(user.balance_main)
        balance_alt = str(user.balance_alt)
        bonus_count = str(user.bonus_count)
        mini_bonus_count = str(user.mini_bonus_count)
        roulette_zero_count = str(user.roulette_zero_count)
        slot_777_count = str(user.slot_777_count)
        rank = await get_user_rank(session, user_id)

        if isinstance(rank, Rank):
            rank_name = rank.rank_name
        else:
            rank_name = rank

        # Получаем аватар игрока
        avatar_item_name = await get_user_avatar(session, user.tguserid)
        avatar_item = await get_item_by_name(session, avatar_item_name)

        # Предметы
        user_items = await get_dict_user_items(session, user.tguserid)
        all_item_names = list(user_items.keys())
        item_objects = await get_items_by_names(session, all_item_names)
        item_map = {item.item_name: item for item in item_objects}

        avatar_items = {}
        property_items = {}
        for name, count in user_items.items():
            obj = item_map.get(name)
            if not obj:
                continue
            (avatar_items if obj.item_type == ItemType.AVATAR else property_items)[name] = count

        result_text = (
            f'🎮 Ваша кликуха: {formated_username}\n'
            f'💰 Баланс: {scr.amount_changer(balance_main)}$\n'
            f'💦 Конча: {scr.amount_changer(balance_alt)}\n'
            f'🎁 Кол-во бонусов: {scr.amount_changer(bonus_count)}\n'
            f'✨ Кол-во мини-бонусов: {scr.amount_changer(mini_bonus_count)}\n'
            f'🎯 Кол-во "0" в рулетке: {scr.amount_changer(roulette_zero_count)}\n'
            f'🎰 Кол-во "777" в слотах: {scr.amount_changer(slot_777_count)}\n'
            f'🖼 Аватар: {avatar_item.item_name}\n'
            f'🎒 Витринные предметы: {", ".join([f"{item} (x{count})" for item, count in avatar_items.items()])}\n'
            f'📦 Имущество: {", ".join([f"{item} (x{count})" for item, count in property_items.items()])}\n'
            f'💻 Ранг: {rank_name}'
        )

        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Ваш профиль",
            description="Посмотреть свою информацию и баланс.",
            input_message_content=InputTextMessageContent(
                message_text=result_text, parse_mode="HTML", disable_web_page_preview=True
            ),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    # ---------- разбор ставки ----------

    # защитный разбор: stack + optional amount (maxsplit=1)
    try:
        stack, amount = query.split(None, 1)
    except ValueError:
        # нет суммы
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Укажите сумму",
            description="Формат: <ставка> <сумма> (например: 'красное 100к')",
            input_message_content=InputTextMessageContent(
                message_text="Укажите сумму ставки. Пример: 'красное 100к'"
            ),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    stack = stack.lower()
    amount = amount.lower().strip()

    # проверка валидности стека
    if stack not in COLOR_STACKS and stack != ZERO_STACK:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Неправильный стек",
            description="Используйте: 'черное', 'красное', 'чет', 'нечет' или 'зеро'.",
            input_message_content=InputTextMessageContent(
                message_text="Ошибка! Неправильно указан стек. Используйте 'черное', 'красное', 'чет', 'нечет' или 'зеро'."
            ),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    # special: "все"/"всё"
    if amount in ("все", "всё"):
        current_balance = await get_user_stat(session, user_id, "balance_main")
        amount = str(current_balance)

    # пытаемся распарсить сумму через ваш Scripts
    try:
        int_amount = scr.unformat_number(scr.amount_changer(amount))
    except Exception:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Неверная сумма",
            description="Не удалось распознать сумму. Пример: 100, 100к, 2kk",
            input_message_content=InputTextMessageContent(
                message_text="Не удалось распознать сумму. Пример: 100, 100к, 2kk"
            ),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    if int_amount <= 0:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Неверная сумма",
            description="Сумма ставки должна быть больше 0.",
            input_message_content=InputTextMessageContent(message_text="Сумма должна быть > 0.")
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    # получаем актуальный баланс (еще раз)
    current_balance = await get_user_stat(session, user_id, "balance_main")
    if current_balance < int_amount:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Недостаточно средств",
            description=f"Ваш баланс: {scr.amount_changer(str(current_balance))}$",
            input_message_content=InputTextMessageContent(
                message_text=f"У вас недостаточно средств! Ваш баланс: {scr.amount_changer(str(current_balance))}$"
            ),
        )
        await inline_query.answer([result], cache_time=0, is_personal=True)
        return

    # списываем ставку (немедленно)
    await update_user(session, "balance_main", current_balance - int_amount, user_id)
    balance_after_bet = await get_user_stat(session, user_id, "balance_main")

    # симулируем рулетку
    status, number = scr.roulette_randomizer(stack)
    current_stack = scr.pic_color(number)

    if stack in COLOR_STACKS:
        if status:
            win_amount = int_amount * 2
            await update_user(session, "balance_main", balance_after_bet + win_amount, user_id)
            final_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"🎉 [{stack} {scr.amount_changer(amount)}] {number} - {current_stack.capitalize()}! Ставка x2! "
                f"Вы выиграли {scr.amount_changer(win_amount)}$!\n"
                f"Баланс: {scr.amount_changer(final_balance)}$"
            )
        else:
            final_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"😢 [{stack} {scr.amount_changer(amount)}] {number} - {current_stack.capitalize()}! Вы проиграли "
                f"{scr.amount_changer(int_amount)}$.\n"
                f"Баланс: {scr.amount_changer(final_balance)}$"
            )

    else:  # 'зеро'
        if status:
            win_amount = int_amount * 42
            await update_user(session, "balance_main", balance_after_bet + win_amount, user_id)
            # можно увеличить счетчик нулей если есть поле user.roulette_zero_count
            final_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"🎉 [{stack} {scr.amount_changer(amount)}] {number} - {current_stack.capitalize()}! Ставка x42! "
                f"Вы выиграли {scr.amount_changer(win_amount)}$!\n"
                f"Баланс: {scr.amount_changer(final_balance)}$"
            )
        else:
            final_balance = await get_user_stat(session, user_id, "balance_main")
            result_text = (
                f"😢 [{stack} {scr.amount_changer(amount)}] {number} - {current_stack.capitalize()}! Вы проиграли "
                f"{scr.amount_changer(int_amount)}$.\n"
                f"Баланс: {scr.amount_changer(final_balance)}$"
            )

    # отправляем один персональный inline-результат
    result = InlineQueryResultArticle(
        id=str(uuid4()),
        title="Результат рулетки",
        description=(result_text[:200] if len(result_text) > 200 else result_text),
        input_message_content=InputTextMessageContent(message_text=result_text),
    )
    await inline_query.answer([result], cache_time=0, is_personal=True)
