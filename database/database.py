import sqlite3 as sql
from datetime import datetime
from config import ADMIN_IDs

class Database:
    def __init__(self):
        self.conn = sql.connect('main.db')
        self.cursor = self.conn.cursor()
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
                            "tgusername TEXT NOT NULL,"
                            "tguserid INTEGER NOT NULL)")

        self.save()

    def save(self):
        self.conn.commit()

    def register_user(self, username: str, tguserid: int):
        if self.get_user_by_tgid(tguserid) is not None:
            return False

        tgusername = '@' + username

        self.cursor.execute("INSERT INTO Users (username, balance_main, balance_alt, last_bonus_time, "
                            "last_mini_bonus_time, bonus_count, mini_bonus_count, is_admin, tgusername, tguserid) VALUES "
                            "(?, 35000, 0, '1970-01-01 00:00:00', '1970-01-01 00:00:00', 0, 0, 0, ?, ?)",
                            (username, tgusername, tguserid))
        self.save()
        return True

    def get_user_by_tgid(self, tguserid: int):
        self.cursor.execute("SELECT * FROM Users WHERE tguserid = ?", (tguserid,))
        return self.cursor.fetchone()

    def get_user_stat(self, tguserid: int, stat_name: str):
        self.cursor.execute("SELECT {} FROM Users WHERE tguserid =?".format(stat_name), (tguserid,))
        return self.cursor.fetchone()[0] if self.cursor.fetchone() else None

    def get_user_id_by_tgusername(self, tgusername: str):
        self.cursor.execute("SELECT tguserid FROM Users WHERE tgusername =?", (tgusername,))
        return self.cursor.fetchone()

    def update_user(self, balance_main: int, balance_alt: int, tguserid: int):
        self.cursor.execute("UPDATE Users SET balance_main = ?, balance_alt = ? WHERE tguserid = ?",
                            (balance_main, balance_alt, tguserid))
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
