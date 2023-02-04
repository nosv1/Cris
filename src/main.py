from Bot import Bot

import discord
from discord import option

import event_handlers.on_ready as eh_on_ready

import os

from servers.phyner.phyner import GUILD_ID as phyner_guild_id
from servers.tepcott.tepcott import GUILD_ID as tepcott_guild_id

# from servers.tepcott.commands import reserve_needed as tepcott_reserve_needed
# from servers.tepcott.commands import reserve_assign_unassign as tepcott_reserve_assign
# from servers.tepcott.commands import reserve_remove as tepcott_reserve_remove
from servers.tepcott.commands import updatedivs as tepcott_updatedivs
from servers.tepcott.commands import startingorder as tepcott_startingorder
from servers.tepcott.commands import startingtimes as tepcott_startingtimes

from dotenv import load_dotenv

load_dotenv()

bot: Bot = Bot(debug=os.getenv("DEBUG").lower() == "true")

########################    EVENT HANDLERS    ########################


@bot.event
async def on_ready():
    """ """

    await eh_on_ready.on_ready(bot)


########################    COMMANDS    ########################


# tepcott_reserves_command_group = bot.create_group(
#     "reserve", "Commands for managing reserves.", guild_ids=[tepcott_guild_id]
# )

# ### /reserve needed ###
# @tepcott_reserves_command_group.command(
#     name="needed",
#     description="Sets a driver as needing a reserve.",
# )
# @option(
#     name="driver",
#     type=discord.Member,
#     description="The driver who needs a reserve.",
# )
# async def reserve(ctx: discord.ApplicationContext, driver: discord.Member):
#     """/reserve needed <@driver>"""

#     if bot.debug and not bot.is_developer(ctx.author):
#         return

#     await tepcott_reserve_needed.reserve_needed(ctx, bot, driver)


# ### /reserve assign @driver @reserve ###
# @tepcott_reserves_command_group.command(
#     name="assign",
#     description="Assigns a reserve to a driver.",
# )
# @option(
#     name="driver",
#     type=discord.Member,
#     description="The driver to assign the reserve to.",
# )
# @option(
#     name="reserve",
#     type=discord.Member,
#     description="The reserve to assign.",
# )
# async def reserve(
#     ctx: discord.ApplicationContext, driver: discord.Member, reserve: discord.Member
# ):
#     """/reserve assign <@driver> <@driverreserve>"""

#     if bot.debug and not bot.is_developer(ctx.author):
#         return

#     await tepcott_reserve_assign.reserve_assign(ctx, bot, driver, reserve)


# ### /reserve remove @driver ###
# @tepcott_reserves_command_group.command(
#     name="remove",
#     description="Removes a driver's reserve.",
# )
# @option(
#     name="driver",
#     type=discord.Member,
#     description="The driver to remove the reserve from.",
# )
# async def reserve(ctx: discord.ApplicationContext, driver: discord.Member):
#     """/reserve remove <@driver>"""

#     if bot.debug and not bot.is_developer(ctx.author):
#         return

#     await tepcott_reserve_remove.reserve_remove(ctx, bot, driver)


### /startingorder ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="Gets a division's starting order.",
)
async def startingorder(ctx: discord.ApplicationContext):
    """/startingorder"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_startingorder.startingorder(ctx, bot)


### /startingtimes ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="Displays the starting times in local time and UTC.",
)
async def startingtimes(ctx: discord.ApplicationContext):
    """/startingtimes"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_startingtimes.startingtimes(ctx, bot)


### /updatedivs ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="Updates the division roles and nicknames of all participants.",
)
async def updatedivs(ctx: discord.ApplicationContext):
    """/updatedivs"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_updatedivs.updatedivs(ctx, bot)


########################    MAIN    ########################

if __name__ == "__main__":
    # token: str = os.getenv("PROTO_DISCORD_TOKEN")
    token: str = os.getenv("CRIS_DISCORD_TOKEN")
    bot.run(token)