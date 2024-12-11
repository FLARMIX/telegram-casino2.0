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
                            "items_names_list TEXT NOT NULL,"
                            "tguserid INTEGER NOT NULL)")
        self.save()

        # корневые строки БД не подлежащие изменению
        self.basic_rows = ['id', 'username', 'balance_main', 'balance_alt', 'last_bonus_time', 'last_mini_bonus_time'
                           'bonus_count', 'mini_bonus_count', 'is_admin', 'tguserid', 'tgusername']

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

    def add_new_row_for_all_users(self, row_name: str, value: int|str = None):
        self.cursor.execute("ALTER TABLE Users ADD COLUMN IF NOT EXISTS {} {}".format(row_name, 'INTEGER' if isinstance(value, int) else 'TEXT'))

        if value is not None:
            self.cursor.execute("UPDATE Users SET {} =?".format(row_name), (value,))

        self.save()

    def delete_row_for_all_users(self, row_name):
        if row_name not in self.basic_rows:
            self.cursor.execute("ALTER TABLE Users DROP COLUMN {}".format(row_name))
            self.save()
        else:
            print(f"Can't delete basic row '{row_name}'")

