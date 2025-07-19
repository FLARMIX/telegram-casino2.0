import functools
import inspect
import logging

basic_logger = logging.getLogger(__name__)

def log(message: str):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                basic_logger.info(f'{message}  |  FUNC:{func.__name__}/ARGS={args}/KWARGS={kwargs}')
                await func(*args, **kwargs)

            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                basic_logger.info(f'{message}  |  FUNC:{func.__name__}/ARGS={args}/KWARGS={kwargs}')
                func(*args, **kwargs)

            return sync_wrapper

    return decorator