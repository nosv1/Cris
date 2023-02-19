from Bot import Bot

import discord
from discord import option
from discord.ext import commands
from discord.commands import SlashCommandGroup

from servers.phyner.phyner import GUILD_ID as phyner_guild_id

from servers.tepcott.commands import pits as tepcott_pits
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


class SlashCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    ### /vehicles ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Displays the vehicles for each division for the current round.",
    )
    async def vehicles(self, ctx: discord.ApplicationContext):
        """/vehicles"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await tepcott_vehicles.handle_vehicles_command(ctx)

    ### /track ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Displays the track for the current round.",
    )
    async def track(self, ctx: discord.ApplicationContext):
        """/track"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await tepcott_track.handle_track_command(ctx)

    ### /handbook ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Sends a link to the TEPCOTT Handbook.",
    )
    async def handbook(self, ctx: discord.ApplicationContext):
        """/handbook"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await ctx.respond(
            "https://docs.google.com/document/d/1Hayw1pUfQq9RWy5mbGG33Yszq6RuuwX_nERtbyIb6Bs"
        )

    ### /pits ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Shows the pit demo and rules",
    )
    async def pits(self, ctx: discord.ApplicationContext):
        """/pits"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await tepcott_pits.handle_pits_command(ctx)

    ### /qualifying ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Displays basic information about qualifying and joining event.",
    )
    async def qualifying(self, ctx: discord.ApplicationContext):
        """/qualifying"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
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
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="(ADMIN ONLY) Displays details specific to a division for the current round.",
    )
    async def raceday(self, ctx: discord.ApplicationContext):
        """/raceday"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await tepcott_raceday.handle_raceday_command(ctx=ctx, bot=self.bot)

    reserve_group = SlashCommandGroup(
        name="reserve",
        description="Commands for managing reserves.",
        guild_ids=[tepcott_guild_id],
    )

    ## /reserve needed ###
    @reserve_group.command(
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
        type=str,
        description="The driver who no longer needs a reserve.",
    )
    async def reserve(
        self,
        ctx: discord.ApplicationContext,
        driver: discord.Member = None,
        driver_id: str = None,
    ):
        """/reserve needed <@driver>"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        if driver is None and (driver_id is None or not driver_id.isnumeric()):
            await ctx.respond("You must provide a driver or driver id.")
            return

        if driver is None:
            driver = await self.bot.fetch_user(int(driver_id))

        await tepcott_handle_reserve_needed_command(
            ctx=ctx, bot=self.bot, driver_member=driver, remove_request=False
        )

    ### /reserve remove ###
    @reserve_group.command(
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
        type=str,
        description="The driver who no longer needs a reserve.",
    )
    async def reserve(
        self,
        ctx: discord.ApplicationContext,
        driver: discord.Member = None,
        driver_id: str = None,
    ):
        """/reserve remove <@driver>"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        if driver is None and (driver_id is None or not driver_id.isnumeric()):
            await ctx.respond("You must provide a driver or driver id.")
            return

        if driver is None:
            driver = await self.bot.fetch_user(int(driver_id))

        await tepcott_handle_reserve_needed_command(
            ctx=ctx, bot=self.bot, driver_member=driver, remove_request=True
        )

    ### /startingorder ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Gets a division's starting order.",
    )
    async def startingorder(self, ctx: discord.ApplicationContext):
        """/startingorder"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await tepcott_startingorder.startingorder(ctx, self.bot)

    ### /startingtimes ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Displays the starting times in local time and UTC.",
    )
    async def startingtimes(self, ctx: discord.ApplicationContext):
        """/startingtimes"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await tepcott_startingtimes.startingtimes(ctx)

    ### /updatedivs ###
    @commands.slash_command(
        guild_ids=[tepcott_guild_id],
        description="Updates the division roles and nicknames of all participants.",
    )
    async def updatedivs(self, ctx: discord.ApplicationContext):
        """/updatedivs"""

        if self.bot.debug and not self.bot.is_developer(ctx.author):
            return

        await tepcott_updatedivs.updatedivs(ctx, self.bot)


def setup(bot: Bot):
    bot.add_cog(SlashCommands(bot))
