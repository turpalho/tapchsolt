# from typing import Callable, Dict, Any, Awaitable

# from aiogram import BaseMiddleware
# from aiogram.types import Message

# from infrastructure.database.repo.requests import RequestsRepo


# class DatabaseMiddleware(BaseMiddleware):
#     def __init__(self, session_pool) -> None:
#         self.session_pool = session_pool

#     async def __call__(
#         self,
#         handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
#         event: Message,
#         data: Dict[str, Any],
#     ) -> Any:
#         async with self.session_pool() as session:
#             repo = RequestsRepo(session)
#             data["session"] = session
#             data["repo"] = repo

#             # if the user click on the /start button, we mustn't create him in the database
#             if isinstance(event, Message) and event.text and event.text.startswith("/start"):
#                 return await handler(event, data)

#             # add the user to data
#             user = await repo.users.get_or_create_user(
#                 event.from_user.id,
#                 str(event.from_user.id),  # store the user_id as username
#                 event.from_user.first_name,
#                 event.from_user.last_name,
#                 event.from_user.username,
#             )
#             data["user"] = user

#             result = await handler(event, data)
#         return result
