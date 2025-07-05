import asyncio
import logging
from loader import main_run

if __name__ == "__main__":
    logging.basicConfig(filename='bot.log', level=logging.INFO,
                        format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
                        encoding='utf-8')
    asyncio.run(main_run())
