import asyncio
import logging
import os
import textwrap

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from database.methods import init_db, get_all_users, get_user_by_tgusername, update_user, make_admin, change_rank, \
    delete_user, get_user_by_tguserid, change_rank_console
from database.SQLmodels import User
from database.session import AsyncSessionLocal
from scripts.scripts import Scripts

class ConsoleManager:
    def __init__(self, session: AsyncSessionLocal, logger,  bot=None):
        self.db_session = session
        self.scr = Scripts()
        self.bot = bot
        self.logger = logger
        self.running = True
        self.history = FileHistory(os.path.join(os.getcwd(), 'console_history'))
        self.session = PromptSession(history=self.history)
        self.commands = {
            "exit": self.cmd_exit,
            "help": self.cmd_help,
            "select": self.cmd_select,
            "set": self.cmd_set,
            "give": self.cmd_give,
            "bc": self.cmd_broadcast,
            "ban": self.delete_user,
            "clear": self.cmd_clear,
            "info": self.user_info,
            "msg": self.message,
            "rank": self.change_rank,
            "admin": self.make_admin,
            "eval": self.cmd_eval
        }
        self.selected_user = None

    async def start_console(self):
        try:
            await init_db()
            print("✅ Консоль запущена. Введите help для списка команд.")
            while self.running:
                try:
                    cmd_line = await self.async_input('> ')
                    await self.execute_command(cmd_line)
                except Exception as e:
                    print(f"❌ Ошибка: {e}")

        except KeyboardInterrupt as e:
            try:
                logging.debug(f'{e}')
                logging.info('Bot stopped by KeyboardInterrupt')
                await exit('Stopping...')
            except SystemExit:
                pass

    async def async_input(self, prompt: str = '') -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.session.prompt, prompt)

    async def execute_command(self, line: str):
        if not line.strip():
            return

        parts = line.strip().split()
        command = parts[0].lower()
        args = parts[1:]

        handler = self.commands.get(command)
        if handler:
            await handler(args)
        else:
            print(f"❓ Команда не найдена: {command}. Введите help.")

    # === Команды ===

    async def cmd_help(self, args):
        print("Команды:\n"
              "  help                 - показать список команд\n"
              "  exit                 - выйти\n"
              "  select <username>    - выбрать пользователя\n"
              "  set <amount>         - сетнуть деньги выбранному пользователю\n"
              "  give <amount>        - выдать деньги выбранному пользователю\n"
              "  bc <msg>             - отправить сообщение всем пользователям\n"
              "  ban                  - заблокировать пользователя\n"
              "  clear                - очистить консоль\n"
              "  info <username>      - информация о пользователе\n"
              "  msg <msg>            - отправить сообщение выбранному пользователю\n"
              "  rank <rank>          - изменить ранг выбранному пользователю\n"
              "  eval <command>       - выполнить код\n"
              "  admin <username>     - сделать пользователя Модератором"
              "")

    async def cmd_exit(self, args):
        self.running = False
        print("⛔ Выход из консоли")

    async def cmd_select(self, args):
        if not args:
            print("❌ Укажите user_id")
            return
        if args[0] == 'None':
            self.selected_user = None
            print("✅ Пользователь сброшен")
            return
        if args[0] == '*':
            users = await get_all_users(self.db_session)
            self.selected_user = users
            print(f"✅ Выбрано {len(users)} пользователей")
            return

        target_username = args[0]
        user = await get_user_by_tgusername(self.db_session, target_username)
        if user:
            self.selected_user = user
            print(f"✅ Пользователь {target_username} выбран")
        else:
            print("❌ Пользователь не найден")

    async def cmd_set(self, args):
        if self.selected_user is None:
            print("❌ Пользователь не выбран. Используй select <id>")
            return
        if not args:
            print("❌ Укажите сумму")
            return

        amount = int(args[0])

        if isinstance(self.selected_user, list):
            for user in self.selected_user:
                await update_user(
                    self.db_session,
                    "balance_main",
                    amount,
                    user.tguserid
                )
                print(f"💰 Сетнуто {amount}$ пользователю {user.tgusername}")
                await self.bot.send_message(user.tguserid, f"💰 Сетнуто {self.scr.amount_changer(str(amount))}$ [CONSOLE COMMAND]")
        else:
            await update_user(
                self.db_session,
                "balance_main",
                amount,
                self.selected_user.tguserid
            )
            print(f"💰 Сетнуто {amount}$ пользователю {self.selected_user.tgusername}")
            await self.bot.send_message(self.selected_user.tguserid, f"💰 Сетнуто {self.scr.amount_changer(str(amount))}$ [CONSOLE COMMAND]")

    async def cmd_give(self, args):
        if self.selected_user is None:
            print("❌ Пользователь не выбран. Используй select <id>")
            return
        if not args:
            print("❌ Укажите сумму")
            return

        amount = int(args[0])

        if isinstance(self.selected_user, list):
            for user in self.selected_user:
                await update_user(
                    self.db_session,
                    "balance_main",
                    user.balance_main + amount,
                    user.tguserid
                )
                print(f"💰 Начислено {amount}$ пользователю {user.tgusername}")
                await self.bot.send_message(user.tguserid, f"💰 Начислено {self.scr.amount_changer(str(amount))}$ от CONSOLE")

        else:
            await update_user(
                self.db_session,
                "balance_main",
                self.selected_user.balance_main + amount,
                self.selected_user.tguserid
            )
            print(f"💰 Начислено {amount}$ пользователю {self.selected_user.tgusername}")
            await self.bot.send_message(self.selected_user.tguserid, f"💰 Начислено {self.scr.amount_changer(str(amount))}$ от CONSOLE")

    async def cmd_broadcast(self, args):
        if not args:
            print("❌ Укажите сообщение")
            return
        msg = " ".join(args)
        users = await get_all_users(self.db_session)
        for user in users:
            await self.bot.send_message(user.tguserid, msg)
        print(f"📢 Сообщение отправлено {len(users)} пользователям")

    async def delete_user(self, args):
        if self.selected_user is None:
            print("❌ Пользователь не выбран. Используй select <id>")
            return

        if isinstance(self.selected_user, list):
            print("❌ Невозможно удалить несколько пользователей")
            return

        confirm = await self.async_input(f'⚠️ Вы уверены, что хотите заблокировать пользователя {self.selected_user.tgusername}? ')
        if confirm.lower() == 'y':
            reason = await self.async_input("Укажите причину: ")
            if not reason:
                reason = "Не указана"
            else:
                reason = reason

            await delete_user(self.db_session, self.selected_user.tguserid)
            print(f"✅ Пользователь {self.selected_user.tgusername} заблокирован")
            await self.bot.send_message(self.selected_user.tguserid, f"⚠️ Ваш аккаунт удалён, причина: {reason}")
        else:
            print("❌ Операция отменена")

    async def cmd_clear(self, args):
        os.system('clear')

    async def user_info(self, args):
        if self.selected_user is None:
            print("❌ Пользователь не выбран. Используй select <id>")
            return

        user: User = self.selected_user

        info = (f"username: {user.tgusername}\n"
                f"balance_main: {self.scr.amount_changer(str(user.balance_main))}\n"
                f"balance_alt: {user.balance_alt}\n"
                f"bonus time: {user.last_bonus_time}\n"
                f"mini bonus time: {user.last_mini_bonus_time}\n"
                f"bonus count: {user.bonus_count}\n"
                f"mini bonus count: {user.mini_bonus_count}\n"
                f"user_id: {user.tguserid}\n"
                f"is_admin: {user.is_admin}\n"
                f"id: {user.id}")

        print(info)

    async def message(self, args):
        if self.selected_user is None:
            print("❌ Пользователь не выбран. Используй select <id>")
            return

        print(f"📨 Отправка сообщения пользователю {self.selected_user.tgusername}")
        await self.bot.send_message(self.selected_user.tguserid, " ".join(args))

    async def change_rank(self, args):
        if self.selected_user is None:
            print("❌ Пользователь не выбран. Используй select <id>")
            return

        new_rank = ' '.join(args)

        await change_rank_console(self.db_session, new_rank, self.selected_user.tguserid)
        print(f"✅ Установлен ранг {new_rank} для пользователя {self.selected_user.tgusername}")
        await self.bot.send_message(self.selected_user.tguserid, f"✅ Установлен ранг {new_rank}")

    async def make_admin(self, args):
        if self.selected_user is None:
            print("❌ Пользователь не выбран. Используй select <id>")
            return

        await make_admin(self.db_session, self.selected_user.tguserid)
        await change_rank(self.db_session, self.selected_user.tguserid, "Модератор")
        print(f"✅ Пользователь {self.selected_user.tgusername} назначен модератором")
        await self.bot.send_message(self.selected_user.tguserid, f"✅ Вы назначены модератором")

    async def cmd_eval(self, args):
        code_str = " ".join(args)
        user = await get_user_by_tguserid(self.db_session, self.selected_user.tguserid)
        local_ctx = {
            "session": self.db_session,
            "bot": self.bot,
            "selected_user": self.selected_user,
            "upd_usr": update_user,
            "user": user,
            **globals()
        }

        try:
            result = eval(code_str, {}, local_ctx)
            if asyncio.iscoroutine(result):
                result = await result
            print(repr(result))
        except SyntaxError:
            try:
                func_code = f"async def __user_code():\n{textwrap.indent(code_str, '    ')}"
                exec(func_code, local_ctx, local_ctx)
                result = await local_ctx["__user_code"]()
            except Exception as e:
                print(f"Ошибка: {e}")
        except Exception as e:
            print(f"Ошибка: {e}")