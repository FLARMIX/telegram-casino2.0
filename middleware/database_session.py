from typing import Callable, Awaitable, Any, Dict

from aiogram import BaseMiddleware

from database.session import AsyncSessionLocal


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
            event: Any,
            data: Dict[str, Any]
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data['session'] = session
            return await handler(event, data)
