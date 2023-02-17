from Bot import Bot

import discord
from discord import option

import event_handlers.on_message as eh_on_message
import event_handlers.on_raw_reaction as eh_on_raw_reaction
import event_handlers.on_ready as eh_on_ready

import os

from servers.phyner.phyner import GUILD_ID as phyner_guild_id

from servers.tepcott.commands import raceday as tepcott_raceday
from servers.tepcott.commands import startingorder as tepcott_startingorder
from servers.tepcott.commands import startingtimes as tepcott_startingtimes
from servers.tepcott.commands import track as tepcott_track
from servers.tepcott.commands import updatedivs as tepcott_updatedivs
from servers.tepcott.commands import vehicles as tepcott_vehicles

from servers.tepcott.reserves import (
    handle_reserve_needed_command as tepcott_handle_reserve_needed_command,
)
from servers.tepcott.tepcott import GUILD_ID as tepcott_guild_id
from servers.tepcott.tepcott import LIGHT_BLUE as tepcott_light_blue

from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot: Bot = Bot(debug=os.getenv("DEBUG").lower() == "true", intents=intents)

########################    EVENT HANDLERS    ########################


@bot.event
async def on_ready():
    """ """

    await eh_on_ready.on_ready(bot)


@bot.event
async def on_message(message: discord.Message):
    """ """

    await eh_on_message.on_message(bot, message)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """ """

    await eh_on_raw_reaction.on_raw_reaction(payload, bot, reaction_added=True)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """ """

    await eh_on_raw_reaction.on_raw_reaction(payload, bot, reaction_added=False)


########################    COMMANDS    ########################

tepcott_reserves_command_group = bot.create_group(
    "reserve", "Commands for managing reserves.", guild_ids=[tepcott_guild_id]
)

### /vehicles ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="Displays the vehicles for each division for the current round.",
)
async def vehicles(ctx: discord.ApplicationContext):
    """/vehicles"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_vehicles.handle_vehicles_command(ctx)


### /track ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="Displays the track for the current round.",
)
async def track(ctx: discord.ApplicationContext):
    """/track"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_track.handle_track_command(ctx)


### /handbook ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="Sends a link to the TEPCOTT Handbook.",
)
async def handbook(ctx: discord.ApplicationContext):
    """/handbook"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await ctx.respond(
        "https://docs.google.com/document/d/1Hayw1pUfQq9RWy5mbGG33Yszq6RuuwX_nERtbyIb6Bs"
    )


### /qualifying ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="Displays basic information about qualifying and joining event.",
)
async def qualifying(ctx: discord.ApplicationContext):
    """/qualifying"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    embed = discord.Embed()
    embed.title = "**Qualifying Information**"
    embed.description = (
        f"**Track:** [Vinewood Spirit](https://socialclub.rockstargames.com/job/gtav/nrNVvKm69EeSprSROo7nPA)\n"
        f"**Vehicle:** [Infernus](https://gtacars.net/gta5/infernus)\n"
        f"**Example:** [sexy lap](https://www.youtube.com/watch?v=YqB5ZLma7TQ)\n"
        f"\n💥 Framerate must be locked at 60fps 💥\n"
    )
    embed.color = tepcott_light_blue
    await ctx.respond(embed=embed)


### /raceday ###
@bot.slash_command(
    guild_ids=[tepcott_guild_id],
    description="(ADMIN ONLY) Displays details specific to a division for the current round.",
)
async def raceday(ctx: discord.ApplicationContext):
    """/raceday"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    await tepcott_raceday.handle_raceday_command(ctx=ctx, bot=bot)


## /reserve needed ###
@tepcott_reserves_command_group.command(
    name="needed",
    description="(ADMIN ONLY) Sets a driver as needing a reserve.",
)
@option(
    name="driver",
    type=discord.Member,
    description="The driver who needs a reserve.",
)
@option(
    name="driver id",
    type=int,
    description="The driver who no longer needs a reserve.",
)
async def reserve(
    ctx: discord.ApplicationContext,
    driver: discord.Member = None,
    driver_id: int = None,
):
    """/reserve needed <@driver>"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    if driver is None and driver_id is None:
        await ctx.respond("You must provide a driver or driver id.")
        return

    if driver is None:
        driver = await bot.fetch_user(driver_id)

    await tepcott_handle_reserve_needed_command(
        ctx=ctx, bot=bot, driver_member=driver, remove_request=False
    )


### /reserve remove ###
@tepcott_reserves_command_group.command(
    name="remove",
    description="(ADMIN ONLY) Removes a driver from the list of drivers needing a reserve.",
)
@option(
    name="driver",
    type=discord.Member,
    description="The driver who no longer needs a reserve.",
)
@option(
    name="driver id",
    type=int,
    description="The driver who no longer needs a reserve.",
)
async def reserve(
    ctx: discord.ApplicationContext,
    driver: discord.Member = None,
    driver_id: int = None,
):
    """/reserve remove <@driver>"""

    if bot.debug and not bot.is_developer(ctx.author):
        return

    if driver is None and driver_id is None:
        await ctx.respond("You must provide a driver or driver id.")
        return

    if driver is None:
        driver = await bot.fetch_user(driver_id)

    await tepcott_handle_reserve_needed_command(
        ctx=ctx, bot=bot, driver_member=driver, remove_request=True
    )


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

    await tepcott_startingtimes.startingtimes(ctx)


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
