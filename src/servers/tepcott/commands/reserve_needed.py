from Bot import Bot

import discord
from discord import Message

from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver
from typing import Optional
from servers.tepcott.tepcott import (
    DIVISION_CHANNEL_IDS,
    LATE_JOINERS_AND_RESERVES_CHANNEL_ID,
    RESERVE_NEEDED_STRING,
)
from servers.tepcott.database import add_reserve_request


async def reserve_needed(
    ctx: discord.ApplicationContext, bot: Bot, driver_member: discord.Member
) -> None:
    """ """

    # check if author is the driver, or an admin
    # check if driver in a division
    # check if driver needs a reserve
    # check if driver has a reserve
    # confirm reserve needed
    # offer to inform neighboring divisions

    author_is_not_admin = not ctx.author.guild_permissions.administrator
    author_is_not_member = ctx.author.id != driver_member.id or True  # OVERRIDING
    if author_is_not_member and author_is_not_admin:
        await ctx.respond(
            content="You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    class InformChannelsButton(discord.ui.Button):
        def __init__(
            self,
            ctx: discord.ApplicationContext,
            bot: Bot,
            spreadsheet: Spreadsheet,
            driver: SpreadsheetDriver,
            **kwargs,
        ):
            super().__init__(**kwargs)

            self.view: discord.ui.View
            self.spreadsheet = spreadsheet
            self.driver = driver

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()
            await interaction.message.edit(view=None)

            for division_number in self.spreadsheet.get_neighboring_division_numbers(
                division_number=int(self.driver.division)
            ):
                division_channel = await ctx.guild.fetch_channel(
                    DIVISION_CHANNEL_IDS[division_number]
                )
                await division_channel.send(
                    f"Hello, friends. {interaction.user.display_name} wanted to inform you all, {self.driver.social_club_name}, in Division {self.driver.division}, needs a reserve. Contact a DoubleD if you are interested in reserving - KIFFLOM!"
                )

    class ReserveNeededConfirmButton(discord.ui.Button):
        def __init__(
            self,
            ctx: discord.ApplicationContext,
            bot: Bot,
            spreadsheet: Spreadsheet,
            driver: SpreadsheetDriver,
            driver_member: discord.Member,
            **kwargs,
        ):
            super().__init__(**kwargs)

            self.view: discord.ui.View
            self.ctx = ctx
            self.bot = bot
            self.spreadsheet = spreadsheet
            self.driver = driver
            self.driver_member = driver_member
            self.msg: Optional[Message] = None

        async def callback(self, interaction: discord.Interaction):
            """ """
            await interaction.response.edit_message(
                content="Reserve is being set...", view=None
            )

            self.spreadsheet.set_reserves(drivers=[self.driver])
            # self.spreadsheet.add_reserve_request(self.driver.discord_id)

            view = discord.ui.View()
            view.add_item(
                InformChannelsButton(
                    ctx=self.ctx,
                    bot=self.bot,
                    spreadsheet=self.spreadsheet,
                    driver=self.driver,
                    label="Inform neighboring divisions (no ping)?",
                    style=discord.ButtonStyle.blurple,
                )
            )

            add_reserve_request(bot.tepcott_database, self.driver)
            await interaction.channel.send(
                content=f"`{self.ctx.author.display_name}` marked `{self.driver_member.display_name}` as needing a reserve for Round {self.spreadsheet.round_number}.",
            )

            # await interaction.channel.send(
            #     content=f"`{self.ctx.author.display_name}` marked `{self.driver_member.display_name}` as needing a reserve for Round {self.spreadsheet.round_number}.",
            #     view=view,
            # )
            # late_joiners_and_reserves_channel = await self.bot.fetch_channel(
            #     LATE_JOINERS_AND_RESERVES_CHANNEL_ID
            # )
            # await late_joiners_and_reserves_channel.send(
            #     f"`{self.ctx.author.display_name}` marked `{self.driver_member.display_name}` as needing a reserve for Round {self.spreadsheet.round_number}."
            # )

    class ReserveNeededCancelButton(discord.ui.Button):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.view: discord.ui.View

        async def callback(self, interaction: discord.Interaction):
            self.view.disable_all_items()
            await interaction.response.edit_message(content="Cancelled", view=None)

    interaction = await ctx.send_response(
        content="Hello, friend. I'm just doing some checks real quick...",
        ephemeral=True,
    )

    spreadsheet = Spreadsheet()
    _, drivers_by_discord_id = spreadsheet.get_roster_drivers()
    try:
        driver = drivers_by_discord_id[driver_member.id]
    except KeyError:
        await interaction.edit_original_response(
            content=f"`{driver_member.display_name}` is not on the spreadsheet roster."
        )
        return
    starting_orders = spreadsheet.get_starting_orders(
        round_number=spreadsheet.round_number
    )

    driver_in_division = driver.division.isnumeric()
    if not driver_in_division:
        await interaction.edit_original_response(
            content=f"`{driver_member.display_name}` is not in a division."
        )
        return

    division_number = int(driver.division)
    driver_reserve = [
        d for d in starting_orders[division_number] if d.discord_id == driver.discord_id
    ][0].reserve

    driver_needs_reserve = (
        driver_reserve and driver_reserve.social_club_name == RESERVE_NEEDED_STRING
    )
    driver_has_reserve = driver_reserve and driver_reserve.social_club_name != ""
    if driver_has_reserve:
        await interaction.edit_original_response(
            content=f"`{driver_member.display_name}` already has `{driver_reserve.social_club_name}` as a reserve for Round {spreadsheet.round_number}."
        )
        return
    if driver_needs_reserve:
        await interaction.edit_original_response(
            content=f"`{driver_member.display_name}` is already marked as needing a reserve for Round {spreadsheet.round_number}."
        )
        return

    driver.reserve = SpreadsheetDriver(social_club_name=RESERVE_NEEDED_STRING)

    view = discord.ui.View()
    view.add_item(
        ReserveNeededConfirmButton(
            ctx=ctx,
            bot=bot,
            spreadsheet=spreadsheet,
            driver=driver,
            driver_member=driver_member,
            label="Confirm",
            style=discord.ButtonStyle.green,
            custom_id="confirm_reserve_needed",
        )
    )
    view.add_item(
        ReserveNeededCancelButton(
            label="Cancel",
            style=discord.ButtonStyle.red,
            custom_id="cancel_reserve_needed",
        )
    )

    await interaction.edit_original_response(
        content=f"Are you sure you want to mark `{driver_member.display_name}` as needing a reserve for Round {spreadsheet.round_number}?",
        view=view,
    )
