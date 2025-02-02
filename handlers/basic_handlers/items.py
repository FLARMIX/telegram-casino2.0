from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import BufferedInputFile
from aiogram import F
from aiogram.types import CallbackQuery

from handlers.init_router import router

from database.database import Database

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@router.message(Command("предметы"))
@router.message(Command("items"))
async def show_items_menu(message: Message):
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Аватарки", callback_data="items_avatar")],
        [InlineKeyboardButton(text="Имущество", callback_data="items_property")],
        [InlineKeyboardButton(text="Все предметы", callback_data="items_all")]
    ])

    await message.answer(
        "Выберите тип предметов:",
        reply_markup=keyboard,
        reply_to_message_id=message.message_id
    )


@router.callback_query(F.data == "items_avatar")
async def show_avatar_items(callback: CallbackQuery):
    db = Database()
    user_id = callback.from_user.id

    # Получаем предметы с типом "avatar"
    items = db.get_user_items(user_id)
    avatar_items = {item: count for item, count in items.items() if db.get_item_type(item) == "avatar"}

    if not avatar_items:
        await callback.message.answer("У вас нет аватарок.", reply_to_message_id=callback.message.message_id)
        return

    # Создание объединенного изображения для аватарок
    all_paths = []
    for item, count in avatar_items.items():  # Итерируем по словарю
        item_path = db.get_item_path(item)
        if item_path:
            all_paths.append((item_path, count))  # Сохраняем путь и количество

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
    for idx, (path, count) in enumerate(all_paths):
        try:
            item_img = Image.open(path).resize((image_width, image_height))
            combined_image.paste(item_img, (x_offset, y_offset))

            # Добавляем текст с количеством аватарок
            draw = ImageDraw.Draw(combined_image)
            font = ImageFont.load_default(size=30)
            draw.text((x_offset + 20, y_offset + 20), f"x{count}", fill="white", font=font)

            # Обновляем координаты для следующей аватарки
            x_offset += image_width

            # Переход на новую строку, если достигнут предел в строке
            if (idx + 1) % num_per_row == 0:
                x_offset = 0
                y_offset += image_height
        except Exception as e:
            print(f"Ошибка загрузки {path}: {e}")

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
async def show_property_items(callback: CallbackQuery):
    db = Database()
    user_id = callback.from_user.id

    # Получаем предметы с типом, отличным от "avatar"
    items = db.get_user_items(user_id)
    property_items = {item: count for item, count in items.items() if db.get_item_type(item) != "avatar"}

    if not property_items:
        await callback.message.answer("У вас нет имущества.", reply_to_message_id=callback.message.message_id)
        return

    # Отправляем список имущества
    items_list = "\n".join([f"{item} (x{count})" for item, count in property_items.items()])
    await callback.message.answer(f"Ваше имущество:\n{items_list}", reply_to_message_id=callback.message.message_id)


@router.callback_query(F.data == "items_all")
async def show_all_items(callback: CallbackQuery):
    db = Database()
    user_id = callback.from_user.id

    # Получаем все предметы пользователя
    items = db.get_user_items(user_id)

    if not items:
        await callback.message.answer("У вас нет ни одного предмета.", reply_to_message_id=callback.message.message_id)
        return

    # Отправляем список всех предметов и их тип
    items_list = "\n".join([f"{item} (x{count})" for item, count in items.items()])
    await callback.message.answer(f"Все ваши предметы:\n{items_list}", reply_to_message_id=callback.message.message_id)
