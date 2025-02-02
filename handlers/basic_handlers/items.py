from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

from handlers.init_router import router

from database.database import Database

from io import BytesIO
from PIL import Image


@router.message(Command("предметы"))
@router.message(Command("items"))
async def show_items(message: Message):
    db = Database()
    user_id = message.from_user.id

    # Проверка регистрации
    if not db.check_user_in(user_id):
        await message.answer("Вы не зарегистрированы. Используйте /register.",
                             reply_to_message_id=message.message_id)
        return

    # Получение словаря предметов пользователя
    items = db.get_user_items(user_id)

    if not items:
        await message.answer("У вас нет предметов!", reply_to_message_id=message.message_id)
        return

    # Получение аргументов команды
    args = message.text.split()
    item_name = args[1] if len(args) > 1 else "все"

    if item_name != "все":
        # Отправка одного предмета
        if item_name in items:
            item_path = db.get_item_path(item_name)
            if item_path:
                with open(item_path, 'rb') as photo:
                    await message.answer_photo(
                        photo=photo,
                        caption=f"Предмет: {item_name} (x{items[item_name]})",  # Указываем количество
                        reply_to_message_id=message.message_id
                    )
            else:
                await message.answer(f"Изображение для предмета {item_name} не найдено.",
                                     reply_to_message_id=message.message_id)
        else:
            await message.answer("У вас нет такого предмета!",
                                 reply_to_message_id=message.message_id)
        return

    # Создание объединенного изображения
    all_paths = []
    for item, count in items.items():  # Итерируем по словарю
        item_path = db.get_item_path(item)
        if item_path:
            all_paths.append((item_path, count))  # Сохраняем путь и количество

    if not all_paths:
        await message.answer("Нет доступных изображений для ваших предметов.",
                             reply_to_message_id=message.message_id)
        return

    # Параметры сетки
    image_width = 200  # Размер каждого изображения
    image_height = 200
    num_per_row = 5  # Количество изображений в строке
    num_rows = (len(all_paths) + num_per_row - 1) // num_per_row

    # Создание холста
    combined_image = Image.new('RGB', (image_width * num_per_row, image_height * num_rows), (245, 245, 245))

    # Наложение изображений
    x_offset, y_offset = 0, 0
    for idx, (path, count) in enumerate(all_paths):
        try:
            item_img = Image.open(path).resize((image_width, image_height))
            combined_image.paste(item_img, (x_offset, y_offset))

            # Добавляем текст с количеством предметов
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(combined_image)
            font = ImageFont.load_default()
            draw.text((x_offset + 10, y_offset + 10), f"x{count}", fill="white", font=font)

            x_offset += image_width

            # Переход на новую строку
            if (idx + 1) % num_per_row == 0:
                x_offset = 0
                y_offset += image_height
        except Exception as e:
            print(f"Ошибка загрузки {path}: {e}")

    # Конвертация в bytes
    img_byte_arr = BytesIO()
    combined_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    img_byte_arr = img_byte_arr.getvalue()

    # Создаем InputFile из BytesIO
    input_file = BufferedInputFile(img_byte_arr, filename="items.png")

    # Отправка объединенного изображения
    await message.answer_photo(
        photo=input_file,
        caption=f"Все ваши предметы ({len(items)} шт.):",
        reply_to_message_id=message.message_id
    )