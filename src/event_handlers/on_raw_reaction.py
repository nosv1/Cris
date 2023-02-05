from Bot import Bot
import discord

from servers.tepcott.event_handlers import on_raw_reaction as tepcott_on_raw_reaction
from servers.tepcott.tepcott import GUILD_ID as tepcott_guild_id


async def on_raw_reaction(
    payload: discord.RawReactionActionEvent, bot: Bot, reaction_added=True
):
    """ """

    is_in_tepcott = payload.guild_id == tepcott_guild_id
    if is_in_tepcott:
        await tepcott_on_raw_reaction.on_raw_reaction(
            payload=payload, bot=bot, reaction_added=reaction_added
        )
