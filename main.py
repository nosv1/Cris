from Bot import Bot
import discord
import os
import src.event_handlers.on_ready as eh_on_ready

from src.servers.phyner.phyner import GUILD_ID as phyner_guild_id
from src.servers.tepcott.tepcott import GUILD_ID as tepcott_guild_id
# from src.servers.tepcott.commands import reserve as tepcott_reserve
from src.servers.tepcott.commands import updatedivs as tepcott_updatedivs
from src.servers.tepcott.commands import startingorder as tepcott_startingorder

bot: Bot = Bot(
    debug=os.getenv("DEBUG").lower() == "true")

########################    EVENT HANDLERS    ########################

@bot.event
async def on_ready():
    await eh_on_ready.on_ready(bot)

########################    COMMANDS    ########################

# @bot.slash_command(guild_ids=[tepcott_guild_id], description="Assign/unassign a reserve to/from a driver")
# async def reserve(ctx: discord.ApplicationContext):
#     """ """

#     if bot.debug and not bot.is_developer(ctx.author):
#         return

#     await tepcott_reserve.reserve(ctx, bot)

@bot.slash_command(guild_ids=[tepcott_guild_id], description="Update the division roles and nicknames of all participants based on the spreadsheet")
async def updatedivs(ctx: discord.ApplicationContext):
    """ """

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_updatedivs.updatedivs(ctx, bot)

@bot.slash_command(guild_ids=[tepcott_guild_id], description="Get the starting order for the current round.")
async def startingorder(ctx: discord.ApplicationContext):
    """ """

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_startingorder.startingorder(ctx, bot)

########################    MAIN    ########################

if __name__ == "__main__":
    # token: str = os.getenv("PROTO_DISCORD_TOKEN")
    token: str = os.getenv("CRIS_DISCORD_TOKEN")
    bot.run(token)