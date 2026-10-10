from Qris import bot
from hydrogram import filters
from hydrogram.errors import MessageIdInvalid

class Rz:
    @staticmethod
    def callback(command):
        def wrapper(func):
            @bot.on_callback_query(filters.regex(command))
            async def wrapped(client, cq, *args):
                try:
                    return await func(client, cq)
                except MessageIdInvalid:
                    pass
            return wrapped
        return wrapper