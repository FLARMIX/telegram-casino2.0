import sqlite3 as sql

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
                            "tguserid INTEGER NOT NULL)")

        self.save()

    def save(self):
        self.conn.commit()

    def register_user(self, username: str, tguserid: int):
        if self.get_user_by_tgid(tguserid) is not None:
            return False

        self.cursor.execute("INSERT INTO Users (username, balance_main, balance_alt, last_bonus_time, "
                            "last_mini_bonus_time, bonus_count, mini_bonus_count, tguserid) VALUES "
                            "(?, 35000, 0, '1970-01-01 00:00:00', '1970-01-01 00:00:00', 0, 0, ?)",
                            (username, tguserid))
        self.save()
        return True

    def get_user_by_tgid(self, tguserid: int):
        self.cursor.execute("SELECT * FROM Users WHERE tguserid = ?", (tguserid,))
        return self.cursor.fetchone()

    def update_user(self, username: str, balance_main: int, balance_alt: int, tguserid: int):
        self.cursor.execute("UPDATE Users SET username = ?, balance_main = ?, balance_alt = ? WHERE tguserid = ?",
                            (username, balance_main, balance_alt, tguserid))
        self.save()