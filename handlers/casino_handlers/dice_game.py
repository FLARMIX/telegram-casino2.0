# TODO: Кости как в ББ, крадём их :)
import asyncio
import re

from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.markdown import hlink
from sqlalchemy.ext.asyncio import AsyncSession

from database.methods import get_user_by_tguserid, get_user_stat, update_user, create_dice_game, \
    update_dice_game, get_dice_game_by_id, delete_dice_game
from handlers.init_router import router
from scripts.loggers import log
from scripts.media_cache import file_cache_original

from scripts.scripts import Scripts

async def cancel_dice_game_logic(user, state: FSMContext, bot: Bot, session: AsyncSession, user_message=None, extra_text="") -> bool:
    """
    Отмена игры: возвращаем ставку, очищаем state, редактируем сообщение.
    Возвращает True, если игра была отменена, False если данных нет.
    """
    data = await state.get_data()
    if not data:
        return False

    if not user_message:
        user_message = data.get('user_message')

    int_amount = data.get('amount', 0)
    text = data.get('text', '') + "\n❌ предложение отменено." + extra_text

    await update_user(session, "balance_main", user.balance_main + int_amount, user.tguserid)
    await update_user(session, "cur_dice_game_id", -1, user.tguserid)

    if user_message:
        await bot.edit_message_caption(
            chat_id=user_message.chat.id,
            caption=text,
            message_id=user_message.message_id,
            reply_markup=None
        )

    await state.clear()
    return True


@router.message(F.text.regexp("^/?(кости|dice)(\s|$)", flags=re.IGNORECASE))
@log("We are enter in dice, i'm logging it!")
async def dice_game(message: Message, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, message.from_user.id)
    scr = Scripts()

    message_text = message.text.lower().split()

    is_in_game = await get_user_stat(session, user.tguserid, "cur_dice_game_id")
    if is_in_game != -1:
        await cancel_dice_game_logic(user, state, bot, session)
    else:
        pass


    if not await scr.check_registered(user, message):
        return

    if message.chat.type == "private":
        await message.answer("Игра доступна только в групповых чатах!")
        return

    if not await scr.check_channel_subscription(bot, user.tguserid):
        await message.answer('Вы не подписаны на канал, подпишитесь на канал @PidorsCasino'
                             '\nЧтобы получить доступ к боту, вам необходимо подписаться.',
                             reply_to_message_id=message.message_id)
        return

    if len(message_text) > 2 or len(message_text) < 2:
        await message.answer('Неверный формат команды. Пример:\n\n/dice 1000\n/кости 100к')
        return

    amount = message_text[-1]
    user_balance = user.balance_main

    if amount in ["все", "всё"]:
        amount = str(user_balance)

    int_amount = scr.unformat_number(scr.amount_changer(amount))

    if int_amount <= 0:
        await message.answer("Сумма ставки должна быть больше 0!")
        return

    if user_balance < int_amount:
        await message.answer("У вас нехватает средств для ставки!")
        return

    dice_game = await create_dice_game(session, user.tguserid, -1, int_amount)
    balance = await get_user_stat(session, user.tguserid, "balance_main")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_dice_game:{dice_game.id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_dice_game")]
        ]
    )

    bones_image = file_cache_original.get("media/assets/dice_img.jpg")

    formated_amount = scr.amount_changer(str(int_amount))
    text = f"{hlink(str(user.username), f'tg://user?id={user.tgusername}')}, хочет сыграть в кости! Ставка — {formated_amount}$.\n"

    user_message = await bot.send_photo(
        chat_id=message.chat.id,
        photo=bones_image,
        caption=text,
        reply_markup=keyboard,
        reply_to_message_id=message.message_id
    )

    await update_user(session, "balance_main", balance - int_amount, user.tguserid)
    await update_user(session, "cur_dice_game_id", dice_game.id, user.tguserid)

    await state.update_data(amount=int_amount, user_id=user.tguserid, user_message=user_message,
                            text=text, dice_game=dice_game)


@router.callback_query(F.data == "cancel_dice_game")
async def cancel_dice_game(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    user = await get_user_by_tguserid(session, callback.from_user.id)
    ok = await cancel_dice_game_logic(user, state, bot, session, user_message=callback.message)
    if not ok:
        await callback.answer("Отменить игру может только создатель!", show_alert=True)



@router.callback_query(F.data.startswith("accept_dice_game"))
async def accept_dice_game(callback: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    _, dice_game_id = callback.data.split(":")
    dice_game = await get_dice_game_by_id(session, int(dice_game_id))
    if not dice_game:
        await callback.answer("Игра не найдена!", show_alert=True)
        return

    scr = Scripts()
    user = await get_user_by_tguserid(session, callback.from_user.id)

    await update_user(session, "cur_dice_game_id", -1, dice_game.first_user_id)

    if dice_game.first_user_id == user.tguserid:
        await callback.answer("Вы не можете принять собственную игру!", show_alert=True)
        return

    if user.balance_main < dice_game.bet_amount:
        await callback.answer("У вас нехватает средств для игры!", show_alert=True)
        return

    await update_dice_game(session, "second_user_id", user.tguserid, dice_game.id)
    await update_user(session, "balance_main", user.balance_main - dice_game.bet_amount, user.tguserid)

    first_user = await get_user_by_tguserid(session, dice_game.first_user_id)
    is_hiden = first_user.is_hidden

    if is_hiden:
        first_user_username = first_user.username
    else:
        first_user_username = hlink(str(first_user.username), f'https://t.me/{first_user.tgusername[1:]}')

    second_user = user
    is_hiden = second_user.is_hidden
    if is_hiden:
        second_user_username = second_user.username
    else:
        second_user_username = hlink(str(second_user.username), f'https://t.me/{second_user.tgusername[1:]}')

    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=None)

    await asyncio.sleep(0.3)
    await bot.send_message(callback.message.chat.id, f"Бросает {first_user_username}!", disable_web_page_preview=True)
    first_user_dice = await bot.send_dice(chat_id=callback.message.chat.id, emoji="🎲")

    await asyncio.sleep(1.8)
    await bot.send_message(callback.message.chat.id, f"Бросает {second_user_username}!", disable_web_page_preview=True)
    second_user_dice = await bot.send_dice(chat_id=callback.message.chat.id, emoji="🎲")

    first_user_dice_result = first_user_dice.dice.value
    second_user_dice_result = second_user_dice.dice.value

    await asyncio.sleep(1.3)
    if first_user_dice_result > second_user_dice_result:
        await update_user(session, "balance_main", first_user.balance_main + dice_game.bet_amount * 2, first_user.tguserid)
        winner = first_user_username
    elif first_user_dice_result < second_user_dice_result:
        await update_user(session, "balance_main", second_user.balance_main + dice_game.bet_amount * 2, second_user.tguserid)
        winner = second_user_username
    else:
        await update_user(session, "balance_main", first_user.balance_main + dice_game.bet_amount, first_user.tguserid)
        await update_user(session, "balance_main", second_user.balance_main + dice_game.bet_amount, second_user.tguserid)
        await bot.send_message(callback.message.chat.id, "Ничья!")
        return

    win = dice_game.bet_amount * 2
    await bot.send_message(callback.message.chat.id, f"{winner} выйграл {scr.amount_changer(win)}$!", disable_web_page_preview=True)
    await delete_dice_game(session, dice_game.id)
    await state.clear()
