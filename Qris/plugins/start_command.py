from hydrogram import filters
from hydrogram.enums import ParseMode
from Qris import bot
from Qris.utils import TEXT, BUTTON
from Qris.database import *

@bot.on_message(filters.command("start"))
async def cmd_start(c, m):
    user = m.from_user.id
    username = m.from_user.mention
    bot_name = c.me.mention

    await dB.add_broadcast(user)

    text = TEXT.start_msg(username, bot_name)
    keyboard = BUTTON.start()

    await m.reply(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )