from dotenv import load_dotenv
from os import getenv

# Загрузите переменные среды из файла .env в текущую среду.
load_dotenv()


# Получите значение переменной среды 'TOKEN' и 'ADMIN_IDs'
BOT_TOKEN = getenv('TOKEN')
ADMIN_IDs = getenv('ADMIN_IDS').split()
