from json import load
from random import randint as ri
import os


class Scripts:
    def __init__(self):
        relative_path = "scripts/number_color.json"
        absolute_path = os.path.abspath(relative_path)
        with open(absolute_path, 'r', encoding='utf-8') as num_col:
            self.number_color = load(num_col)

        self.admin_name = "@FLARMIX"
        self.channel_name = "@PidorsCasino"

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




if __name__ == '__main__':
    cnt_zero = 0
    cnt_even = 0
    cnt_odd = 0
    all_cnt = 0
    scripts = Scripts()
    for i in range(10000000):
        test_even = scripts.roulette_randomizer("чет")

        all_cnt += 1
        if test_even:
            cnt_even += 1
        else:
            cnt_odd += 1

    print((cnt_zero/all_cnt) * 100)
    print((cnt_even/all_cnt) * 100)
    print((cnt_odd/all_cnt) * 100)


