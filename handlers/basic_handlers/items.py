import logging

from aiogram.types import Message
from aiogram.types import BufferedInputFile
from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import Bot_username
from database.methods import get_user_by_tguserid, get_dict_user_items, get_item_by_name
from handlers.init_router import router

from database.models import ItemType

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from scripts.loggers import log
from scripts.media_cache import image_cache_resized_500

logger = logging.getLogger(__name__)


@router.message(F.text.lower().in_(["предметы", "items", '/преметы', '/items', f'/items@{Bot_username}']))
@log("I searching errors in items!")
async def show_items_menu(message: Message):
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Аватарки", callback_data="items_avatar"),
            InlineKeyboardButton(text="Имущество", callback_data="items_property")
         ],
        [InlineKeyboardButton(text="Все предметы", callback_data="items_all")]
    ])

    await message.answer(
        "Выберите тип предметов:",
        reply_markup=keyboard,
        reply_to_message_id=message.message_id
    )


@router.callback_query(F.data == "items_avatar")
async def show_avatar_items(callback: CallbackQuery, session: AsyncSession):
    user = await get_user_by_tguserid(session, callback.from_user.id)

    # Получаем предметы с типом "avatar"
    items = await get_dict_user_items(session, user.tguserid)

    avatar_items = dict()
    for item, count in items.items():
        item_obj = await get_item_by_name(session, item)
        if item_obj.item_type == ItemType.AVATAR:
            avatar_items[item] = count

    if not avatar_items:
        await callback.message.answer("У вас нет аватарок.", reply_to_message_id=callback.message.message_id)
        return

    # Создание объединенного изображения для аватарок
    all_paths = []
    all_names = []
    for item, count in avatar_items.items():  # Итерируем по словарю
        item_path = await get_item_by_name(session, item)
        if item_path and item_path.item_path:
            all_paths.append((item_path.item_path, count, item))  # Сохраняем путь и количество

    if not all_paths:
        await callback.message.answer("Нет доступных изображений для ваших аватарок.",
                                      reply_to_message_id=callback.message.message_id)
        return

    # Параметры изображений
    image_width = 500  # Ширина одного изображения
    image_height = 500  # Высота одного изображения
    num_per_row = 5  # Количество изображений в строке

    # Рассчитываем размер холста
    if len(all_paths) <= num_per_row:
        # Если аватарок меньше или равно 5, ширина холста равна сумме ширин всех аватарок
        total_width = image_width * len(all_paths)
        total_height = image_height
    else:
        # Если аватарок больше 5, ширина холста фиксированная (5 аватарок в строке)
        total_width = image_width * num_per_row
        # Высота холста зависит от количества строк
        num_rows = (len(all_paths) + num_per_row - 1) // num_per_row
        total_height = image_height * num_rows

    # Создание холста
    combined_image = Image.new('RGB', (total_width, total_height), (245, 245, 245))

    # Наложение изображений
    x_offset, y_offset = 0, 0
    for idx, (path, count, item_name) in enumerate(all_paths):
        try:
            item_img = image_cache_resized_500.get(path)
            combined_image.paste(item_img, (x_offset, y_offset))

            # Добавляем текст с количеством аватарок
            draw = ImageDraw.Draw(combined_image)
            font_path = "scripts/Roboto.ttf"
            font = ImageFont.truetype(font=font_path, size=30)
            draw.text((x_offset + 20, y_offset + 20), f"x{count} {item_name}", fill="white", font=font)

            # Обновляем координаты для следующей аватарки
            x_offset += image_width

            # Переход на новую строку, если достигнут предел в строке
            if (idx + 1) % num_per_row == 0:
                x_offset = 0
                y_offset += image_height
        except Exception as e:
            logger.info(f"Ошибка загрузки {path}: {e}")

    # Конвертация в bytes
    img_byte_arr = BytesIO()
    combined_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Получаем байты из BytesIO
    image_bytes = img_byte_arr.getvalue()

    # Создаем BufferedInputFile из байтов
    input_file = BufferedInputFile(image_bytes, filename="avatars.png")

    # Отправка объединенного изображения
    await callback.message.answer_photo(
        photo=input_file,
        caption=f"Ваши аватарки:",
        reply_to_message_id=callback.message.message_id
    )


@router.callback_query(F.data == "items_property")
async def show_property_items(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id

    # Получаем предметы с типом, отличным от "avatar"
    items = await get_dict_user_items(session, user_id)

    property_items = dict()
    for item, count in items.items():
        item_obj = await get_item_by_name(session, item)
        if item_obj.item_type != ItemType.AVATAR: # TODO: != ItemType.AVATAR <- костыль, нужно исправить в будущем.
            property_items[item] = count

    if not property_items:
        await callback.message.answer("У вас нет имущества.", reply_to_message_id=callback.message.message_id)
        return

    # Отправляем список имущества
    items_list = "\n".join([f"{item} (x{count})" for item, count in property_items.items()])
    await callback.message.answer(f"Ваше имущество:\n{items_list}", reply_to_message_id=callback.message.message_id)


@router.callback_query(F.data == "items_all")
async def show_all_items(callback: CallbackQuery, session: AsyncSession):
    user_id = callback.from_user.id

    # Получаем все предметы пользователя
    items = await get_dict_user_items(session, user_id)

    if not items:
        await callback.message.answer("У вас нет ни одного предмета.", reply_to_message_id=callback.message.message_id)
        return

    # Отправляем список всех предметов и их тип
    items_list = "\n".join([f"{item} (x{count})" for item, count in items.items()])
    await callback.message.answer(f"Все ваши предметы:\n{items_list}", reply_to_message_id=callback.message.message_id)
