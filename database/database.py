import json
import sqlite3 as sql
from datetime import datetime
from typing import Any

from config import ADMIN_IDs


class Database:
    def __init__(self):
        self.conn = sql.connect('main.db')
        self.cursor = self.conn.cursor()
        # Данные об игроках
        self.cursor.execute("CREATE TABLE IF NOT EXISTS Users ("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                            "username TEXT NOT NULL,"
                            "balance_main INTEGER NOT NULL,"
                            "balance_alt INTEGER NOT NULL,"
                            "last_bonus_time TEXT NOT NULL,"
                            "last_mini_bonus_time TEXT NOT NULL,"
                            "bonus_count INTEGER NOT NULL,"
                            "mini_bonus_count INTEGER NOT NULL,"
                            "is_admin BOOLEAN NOT NULL,"
                            "is_worker BOOLEAN NOT NULL,"
                            "work_name TEXT NOT NULL,"
                            "tgusername TEXT NOT NULL,"
                            "tguserid INTEGER NOT NULL)")

        # Данные о предметах игроков (картинки, машины, самолеты, недвижимость)
        self.cursor.execute("CREATE TABLE IF NOT EXISTS UserItems ("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                            "items_list TEXT NOT NULL,"
                            "avatar_item TEXT NOT NULL,"
                            "tguserid INTEGER NOT NULL)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS Items ("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                            "item_name TEXT NOT NULL UNIQUE,"
                            "item_path TEXT,"
                            "item_type TEXT NOT NULL,"
                            "item_buy_price INTEGER,"
                            "item_sell_price INTEGER)")

        self.save()

        # корневые строки БД не подлежащие изменению
        self.basic_rows = ['id', 'username', 'balance_main', 'balance_alt', 'last_bonus_time', 'last_mini_bonus_time'
                                                                                               'bonus_count',
                           'mini_bonus_count', 'is_admin', 'tguserid', 'tgusername']

    def save(self):
        self.conn.commit()

    def register_user(self, username: str, tguserid: int):
        if self.get_user_by_tgid(tguserid) is not None:
            return False

        tgusername = '@' + username

        self.cursor.execute("INSERT INTO Users (username, balance_main, balance_alt, last_bonus_time,"
                            "last_mini_bonus_time, bonus_count, mini_bonus_count, is_admin, is_worker, work_name,"
                            "tgusername, tguserid) VALUES "
                            "(?, 35000, 0, '1970-01-01 00:00:00', '1970-01-01 00:00:00', 0, 0, 0, 0, 'None', ?, ?)",
                            (username, tgusername, tguserid))

        self.cursor.execute("INSERT INTO UserItems (items_list, avatar_item, tguserid) VALUES (?, ?, ?)",
                            ('{}', 'черви', tguserid))

        if str(tguserid) in ADMIN_IDs:
            self.make_admin(tguserid)

        self.save()
        return True

    def get_user_by_tgid(self, tguserid: int):
        self.cursor.execute("SELECT * FROM Users WHERE tguserid = ?", (tguserid,))
        return self.cursor.fetchone()

    def get_user_stat(self, tguserid: int, stat_name: str):
        self.cursor.execute("SELECT {} FROM Users WHERE tguserid =?".format(stat_name), (tguserid,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_user_id_by_tgusername(self, tgusername: str):
        self.cursor.execute("SELECT tguserid FROM Users WHERE tgusername =?", (tgusername,))
        return self.cursor.fetchone()[0]

    def get_user_items(self, tguserid: int) -> dict:
        self.cursor.execute("SELECT items_list FROM UserItems WHERE tguserid = ?", (tguserid,))
        result = self.cursor.fetchone()
        if result and result[0] != '{}':  # Проверяем, что результат не пустой и не '{}'
            try:
                return json.loads(result[0])  # Десериализация JSON-строки в словарь
            except json.JSONDecodeError:
                return {}  # Возвращаем пустой словарь, если JSON некорректен
        return {}  # Возвращаем пустой словарь, если предметов нет

    def get_item_path(self, item_name: str) -> str:
        self.cursor.execute("SELECT item_path FROM Items WHERE item_name = ?", (item_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_item_type(self, item_name: str) -> str:
        self.cursor.execute("SELECT item_type FROM Items WHERE item_name =?", (item_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_user_avatar(self, tguserid: int) -> str:
        self.cursor.execute("SELECT avatar_item FROM UserItems WHERE tguserid =?", (tguserid,))
        result = self.cursor.fetchone()
        return result[0] if result else 'chervi'  # Возвращаем аватарку по умолчанию

    def update_user(self, stat_name: str, value: Any, tguserid: int):
        self.cursor.execute("UPDATE Users SET {} =? WHERE tguserid =?".format(stat_name), (value, tguserid))
        self.save()

    def update_username(self, username: str, tguserid: int):
        self.cursor.execute("UPDATE Users SET username =? WHERE tguserid =?",
                            (username, tguserid))
        self.save()

    def update_bonus(self, tguserid: int, current_time: datetime):
        self.cursor.execute("UPDATE Users SET bonus_count = bonus_count + 1, last_bonus_time =? WHERE tguserid =?",
                            (current_time, tguserid))
        self.save()

    def update_mini_bonus(self, tguserid: int, current_time: datetime):
        self.cursor.execute("UPDATE Users SET mini_bonus_count = mini_bonus_count + 1, "
                            "last_mini_bonus_time =? WHERE tguserid =?",
                            (current_time, tguserid))
        self.save()

    def add_item(self, item_name: str, item_type: str, path: str = None,
                 item_buy_price: int = None, item_sell_price: int = None):
        self.cursor.execute("INSERT INTO Items (item_name, item_path, item_type, item_buy_price, item_sell_price) "
                            "VALUES (?,?,?,?,?)",
                            (item_name, path, item_type, item_buy_price, item_sell_price))
        self.save()

    def get_existing_items_names(self) -> list:
        self.cursor.execute("SELECT item_name FROM Items")
        return [item[0] for item in self.cursor.fetchall()]

    def add_item_to_user(self, tguserid: int, item: str) -> None:
        if item not in self.get_existing_items_names():
            raise ValueError(f'Item {item} does not exist in the database')

        # Получаем текущий словарь предметов
        self.cursor.execute("SELECT items_list FROM UserItems WHERE tguserid = ?", (tguserid,))
        result = self.cursor.fetchone()
        items = json.loads(result[0]) if result and result[0] != '{}' else {}

        # Увеличиваем количество предмета или добавляем новый
        if item in items:
            items[item] += 1
        else:
            items[item] = 1

        # Обновляем словарь предметов в БД
        self.cursor.execute(
            "UPDATE UserItems SET items_list = ? WHERE tguserid = ?",
            (json.dumps(items, ensure_ascii=False), tguserid)  # Убедитесь, что ensure_ascii=False
        )
        self.save()

    def update_items(self, json_data: dict):
        self.cursor.execute("DELETE FROM Items")
        self.save()

        for item_name, item_data in json_data.items():
            self.add_item(item_name, item_data['type'], item_data.get('path'),
                          item_data.get('buy_price'), item_data.get('sell_price'))

        self.save()

    def make_admin(self, tguserid: int):
        self.cursor.execute("UPDATE Users SET is_admin = 1 WHERE tguserid =?", (tguserid,))
        self.save()

    def remove_admin(self, tguserid: int):
        if tguserid in ADMIN_IDs:
            return False
        self.cursor.execute("UPDATE Users SET is_admin = 0 WHERE tguserid =?", (tguserid,))
        self.save()

    def check_user_in(self, tguserid: int) -> bool:
        self.cursor.execute("SELECT COUNT(*) FROM Users WHERE tguserid =?", (tguserid,))
        return self.cursor.fetchone()[0] > 0

    def add_new_row_for_all_users(self, row_name: str, value: int | str = None):
        self.cursor.execute("ALTER TABLE Users ADD COLUMN IF NOT EXISTS {} {}".
                            format(row_name,
                                   'INTEGER' if isinstance(value,
                                                           int) else 'TEXT'))

        if value is not None:
            self.cursor.execute("UPDATE Users SET {} =?".format(row_name), (value,))

        self.save()

    def delete_row_for_all_users(self, row_name):
        if row_name not in self.basic_rows:
            self.cursor.execute("ALTER TABLE Users DROP COLUMN {}".format(row_name))
            self.save()
        else:
            print(f"Can't delete basic row '{row_name}'")
