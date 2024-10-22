from json import load

class Scripts:
    def __init__(self):
        with open('number-color.json', 'r', encoding='utf-8') as num_col:
            self.number_color = load(num_col)

        self.admin_name = "@FLARMIX"
        self.channel_name = "@PidorsCasino"

    def format_number(self, number: int) -> str:
        number: str = str(number)[::-1]
        formated_number = ''.join([x + ',' if i % 3 == 0 else x for i, x in enumerate(number, start=1)])[::-1]
        if formated_number.startswith(','):
            formated_number = formated_number[1:]

        return formated_number

