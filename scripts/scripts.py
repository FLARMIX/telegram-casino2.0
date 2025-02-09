from json import load
from random import randint as ri
from random import choice
from aiogram import Bot
import os

from config import CHANNEL_ID


class Scripts:
    def __init__(self):
        relative_path = "scripts/number_color.json"
        absolute_path = os.path.abspath(relative_path)
        with open(absolute_path, 'r', encoding='utf-8') as num_col:
            self.number_color = load(num_col)

        self.admin_name = "@FLARMIX"
        self.channel_name = "@PidorsCasino"

    async def check_channel_subscription(self, bot: Bot, user_id: int) -> bool:
        """
        Проверяет, подписан ли пользователь на канал.

        :param bot: Объект бота (aiogram.Bot).
        :param user_id: ID пользователя, которого нужно проверить.
        :return: True, если пользователь подписан, иначе False.
        """
        channel_id = CHANNEL_ID
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            # Обработка ошибок, например, если бот не имеет доступа к каналу
            print(f"Ошибка при проверке подписки: {e}")
            return False

    def randomize_emoji(self, win: bool) -> str:
        if win:
            return choice('🥵😝😎🏆🔥')
        else:
            return choice('😢😭🥶😱😨😰😥😓')


    def unformat_number(self, formated_number: str) -> int:
        number: str = formated_number.replace(',', '')
        return int(number)

    def format_number(self, number: int) -> str:
        number: str = str(number)[::-1]
        formated_number = ''.join([x + ',' if i % 3 == 0 else x for i, x in enumerate(number, start=1)])[::-1]
        if formated_number.startswith(','):
            formated_number = formated_number[1:]

        return formated_number

    def amount_changer(self, string: str) -> str:
        k_counter = 0
        for i in string:
            if i == 'к' or i == 'k':
                k_counter += 1
        multiple_counter = 1000 ** k_counter
        if '.' in string:
            string = string.replace('к', '')
            result = float(string) * multiple_counter
        else:
            result = float(string.replace('к', '')) * multiple_counter
        return self.format_number(int(result))

    def random_number(self) -> str:
        return str(ri(0, 36))

    def pic_color(self, number: str) -> str:
        if number in self.number_color:
            return self.number_color[number]
        else:
            raise ValueError("Invalid number color: %s not in range(0, 36 + 1)" % number)

    def roulette_randomizer(self, stack: str):
        if stack in ['красное', 'черное', 'чёрное', 'зеро']:
            if stack == 'чёрное':
                stack = 'черное'
            number = self.random_number()
            return self.number_color[number] == stack, number
        elif stack in ['чет', 'чёт']:
            number = self.random_number()
            return int(number) % 2 == 0 and int(number) != 0, number
        elif stack in ['нечёт', 'нечет']:
            number = self.random_number()
            return int(number) % 2 != 0, number
