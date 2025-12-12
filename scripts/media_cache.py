import os
from PIL import Image
from aiogram.types import BufferedInputFile
from io import BytesIO

MEDIA_FOLDER = "media"

# Кэши
image_cache_original: dict[str, Image.Image] = {}
image_cache_resized_500: dict[str, Image.Image] = {}
file_cache_original: dict[str, BufferedInputFile] = {}
file_cache_resized_500: dict[str, BufferedInputFile] = {}

def preload_media_cache():
    """
    Предзагружает все картинки/видео из папки media в кэш:
    - Оригинальные изображения -> image_cache_original
    - Сжатые до 500x500 -> image_cache_resized_500
    - BufferedInputFile (из оригинала) -> file_cache_original
    """
    supported_ext = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webm"}
    for root, dirs, files in os.walk(MEDIA_FOLDER):
        print(root)
        print(dirs)
        print(files)
        for file in files:
            path = os.path.join(root, file)
            # Normalize path for cross-platform compatibility
            normalized_path = os.path.normpath(path)
            ext = os.path.splitext(file)[1].lower()

            if ext not in supported_ext:
                continue

            try:
                with open(path, "rb") as f:
                    raw_bytes = f.read()

                # Кэшируем оригинал как BufferedInputFile
                file_cache_original[normalized_path] = BufferedInputFile(raw_bytes, filename=file)
                print(path)

                if ext in {".jpg", ".jpeg", ".png"}:
                    img = Image.open(BytesIO(raw_bytes)).convert("RGB")
                    image_cache_original[normalized_path] = img
                    resized_image = img.resize((500, 500))
                    image_cache_resized_500[normalized_path] = resized_image

                    bio = BytesIO()
                    resized_image.save(bio, format="PNG")
                    file_cache_resized_500[normalized_path] = BufferedInputFile(bio.getvalue(), filename=file)


                print(image_cache_original)
                print(image_cache_resized_500)
                print(file_cache_original)
                print(file_cache_resized_500)
            except Exception as e:
                print(f"❌ Ошибка при загрузке {file}: {e}")