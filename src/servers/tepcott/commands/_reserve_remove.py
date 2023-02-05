from Bot import Bot

import discord
from discord import Message

from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver
from typing import Optional
from servers.tepcott.tepcott import (
    DIVISION_CHANNELS_IDS,
    LATE_JOINERS_AND_RESERVES_CHANNEL_ID,
    RESERVE_NEEDED_STRING,
)


async def reserve_remove(
    ctx: discord.ApplicationContext, bot: Bot, driver_member: discord.Member
) -> None:
    """ """

    # use command
    # check if driver had reserve
    # check if reserve was actually a driver
    # if reserve was a driver, ping them to let em know
    # include note to see if any other drivers in same div need a reserve

    author_is_not_admin = not ctx.author.guild_permissions.administrator
    author_is_not_member = ctx.author.id != driver_member.id
    if author_is_not_member and author_is_not_admin:
        await ctx.respond(
            content="You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    class ReserveRemoveConfirmButton(discord.ui.Button):
        def __init__(
            self,
            ctx: discord.ApplicationContext,
            bot: Bot,
            spreadsheet: Spreadsheet,
            driver: SpreadsheetDriver,
            driver_member: discord.Member,
            reserve_member: Optional[discord.Member],
            **kwargs,
        ):
            super().__init__(**kwargs)

            self.view: discord.ui.View
            self.ctx = ctx
            self.bot = bot
            self.spreadsheet = spreadsheet
            self.driver = driver
            self.driver_member = driver_member
            self.reserve_member = reserve_member

        async def callback(self, interaction: discord.Interaction):
            """ """

            # inform user reserve is being removed

            # check if reserve is a driver
            # if so, inform div channel driver can race with reserve ping
            # otherwise inform div channel driver can race

            # inform late joiners and reserves channel driver can race
            # check if any other drivers in same div need a reserve
            # if so, inform late joiners and reserves channel

            await interaction.response.edit_message(
                content="Reserve is being removed...", view=None
            )

            self.spreadsheet.set_reserves(drivers=[self.driver])
            self.spreadsheet.remove_reserve_request(self.driver.discord_id)

            reserve_is_member = self.reserve_member is not None
            if reserve_is_member:
                message_str = f"`Good news, friends! {self.ctx.author.display_name}` says `{self.driver_member.display_name}` no longer needs {self.reserve_member.mention} as a reserve for Round {self.spreadsheet.round_number}."
            else:
                message_str = f"`Good news, friends! {self.ctx.author.display_name}` says `{self.driver_member.display_name}` no longer needs a reserve for Round {self.spreadsheet.round_number}."

            div_channel = await self.bot.fetch_channel(
                DIVISION_CHANNELS_IDS[int(self.driver.division)]
            )
            interaction_channel_is_div_channel = (
                interaction.channel.id == div_channel.id
            )
            if interaction_channel_is_div_channel:
                await interaction.channel.send(message_str)
            else:
                await div_channel.send(message_str)
                await interaction.response.edit_message(
                    f"Reserve removed. {div_channel.mention}"
                )

            late_joiners_and_reserves_channel = await self.bot.fetch_channel(
                LATE_JOINERS_AND_RESERVES_CHANNEL_ID
            )
            await late_joiners_and_reserves_channel.send(
                f"`{self.ctx.author.display_name}` marked `{self.driver_member.display_name}` as no longer needing a reserve for Round {self.spreadsheet.round_number}."
            )

            reserves_needed_in_division = self.spreadsheet.get_reserves_needed(
                division=int(self.driver.division), include_filled_reserves=False
            )
            if not not reserves_needed_in_division:
                reserves_needed_string = f"Reserves needed in D{self.driver.division} (in order of request):\n"
                reserves_needed_string += "\n".join(
                    [d.social_club_name for d in reserves_needed_in_division]
                )
                if reserve_is_member:
                    reserves_needed_string += (
                        f"\nPerhaps {self.reserve_member.mention} can be re-assigned?"
                    )
                await late_joiners_and_reserves_channel.send(reserves_needed_string)

    class ReserveRemoveCancelButton(discord.ui.Button):
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
    if not driver_has_reserve or not driver_needs_reserve:
        await interaction.edit_original_response(
            content=f"`{driver_member.display_name}` does not need a reserve."
        )
        return

    driver.reserve.social_club_name = ""

    view = discord.ui.View()
    view.add_item(
        ReserveRemoveConfirmButton(
            ctx=ctx,
            bot=bot,
            spreadsheet=spreadsheet,
            driver=driver,
            driver_member=driver_member,
            label="Confirm",
            style=discord.ButtonStyle.green,
            custom_id="confirm_reserve_remove",
        )
    )
    view.add_item(
        ReserveRemoveCancelButton(
            label="Cancel",
            style=discord.ButtonStyle.red,
            custom_id="cancel_reserve_remove",
        )
    )

    await interaction.edit_original_response(
        content=f"Are you sure you want to remove the reserve for `{driver_member.display_name}`?",
        view=view,
    )
