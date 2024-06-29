import asyncio
from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware, types


class AlbumMiddleware(BaseMiddleware):
    """This middleware is for capturing media groups."""

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.1):
        """
        You can provide custom latency to make sure
        albums are handled properly in highload.
        """
        self.latency = latency

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]) -> Any:

        if not event.media_group_id:
            return await handler(event, data)

        try:
            self.album_data[event.media_group_id].append(event)
        except KeyError:
            self.album_data[event.media_group_id] = [event]

        await asyncio.sleep(self.latency)
        try:
            data["album"] = self.album_data.pop(event.media_group_id)
            # del self.album_data[event.media_group_id]
        except KeyError:
            return
        else:
            return await handler(event, data)
