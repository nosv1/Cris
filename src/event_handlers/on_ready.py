from discord import Bot

from servers.tepcott.event_handlers.on_ready import on_ready as tepcott_on_ready


async def on_ready(bot: Bot):
    print(f"Logged in as {bot.user}")
    await tepcott_on_ready()
    return
