from Bot import Bot

import discord

from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver
from typing import Optional
from servers.tepcott.tepcott import (
    DIVISION_CHANNEL_IDS,
    LATE_JOINERS_AND_RESERVES_CHANNEL_ID,
    RESERVE_NEEDED_STRING,
)


class ReserveAssignConfirmButton(discord.ui.Button):
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

        # inform user reserve is being assigned

        await interaction.response.edit_message(
            content="Reserve is being removed...", view=None
        )

        self.spreadsheet.set_reserves(drivers=[self.driver])
        self.spreadsheet.remove_reserve_request(self.driver.discord_id)

        reserve_is_member = self.reserve_member is not None
        if reserve_is_member:
            message_str = f"Good news, friends! `{self.ctx.author.display_name}` says `{self.driver_member.display_name}` no longer needs {self.reserve_member.mention} as a reserve for Round {self.spreadsheet.round_number}."
        else:
            message_str = f"Good news, friends! `{self.ctx.author.display_name}` says `{self.driver_member.display_name}` no longer needs a reserve for Round {self.spreadsheet.round_number}."

        div_channel = await self.bot.fetch_channel(
            DIVISION_CHANNEL_IDS[int(self.driver.division)]
        )
        interaction_channel_is_div_channel = interaction.channel.id == div_channel.id
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
            reserves_needed_string = (
                f"Reserves needed in D{self.driver.division} (in order of request):\n"
            )
            reserves_needed_string += "\n".join(
                [d.social_club_name for d in reserves_needed_in_division]
            )
            if reserve_is_member:
                reserves_needed_string += (
                    f"\nPerhaps {self.reserve_member.mention} can be re-assigned?"
                )
            await late_joiners_and_reserves_channel.send(reserves_needed_string)


class ReserveAssignCancelButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.view: discord.ui.View

    async def callback(self, interaction: discord.Interaction):
        self.view.disable_all_items()
        await interaction.response.edit_message(content="Cancelled", view=None)


class ReserveUnassignConfirmButton(discord.ui.Button):
    def __init__(
        self,
        ctx: discord.ApplicationContext,
        bot: Bot,
        spreadsheet: Spreadsheet,
        driver: SpreadsheetDriver,
        driver_member: discord.Member,
        reserve_member: discord.Member,
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
        await interaction.response.edit_message(
            content="Reserve is being unassigned...", view=None
        )

        self.driver.reserve.social_club_name = RESERVE_NEEDED_STRING
        self.spreadsheet.set_reserves(drivers=[self.driver])

        div_channel = await self.bot.fetch_channel(
            DIVISION_CHANNEL_IDS[int(self.driver.division)]
        )
        await div_channel.send(
            f"Well this is less than ideal... It has been brough to my attention {self.reserve_member.mention} is no longer reserving for {self.driver_member.mention} for Round {self.spreadsheet.round_number}."
        )

        late_joiners_and_reserves_channel = await self.bot.fetch_channel(
            LATE_JOINERS_AND_RESERVES_CHANNEL_ID
        )
        await late_joiners_and_reserves_channel.send(
            f"`{self.ctx.author.display_name}` unassigned `{self.reserve_member.display_name}` as a reserve for `{self.driver_member.display_name}` for Round {self.spreadsheet.round_number}."
        )

        await interaction.response.edit_message(
            content=f"Reserve unassigned.", view=None
        )


class ReserveUnassignCancelButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.view: discord.ui.View

    async def callback(self, interaction: discord.Interaction):
        self.view.disable_all_items()
        await interaction.response.edit_message(content="Cancelled", view=None)


async def reserve_assign_unassign(
    ctx: discord.ApplicationContext,
    bot: Bot,
    driver_member: discord.Member,
    reserve_member: discord.Member,
    unassign: bool = False,
) -> None:
    """ """

    author_is_not_admin = not ctx.author.guild_permissions.administrator
    author_is_not_reserve_member = ctx.author.id != current_reserve_member.id
    if not unassign and author_is_not_admin:
        await ctx.respond(
            content="You do not have permission to use this command. Contact a DoubleD to assign a reserve.",
            ephemeral=True,
        )
        return
    if unassign and (author_is_not_reserve_member and author_is_not_admin):
        await ctx.respond(
            content="You do not have permission to use this command. Contact a DoubleD to unassign a reserve.",
            ephemeral=True,
        )
        return

    interaction = await ctx.send_response(
        content="Hello, friend. I'm just doing some checks real quick... - KIFFLOM!",
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

    try:
        reserve = drivers_by_discord_id[reserve_member.id]
    except KeyError:
        await interaction.edit_original_response(
            content=f"`{reserve_member.display_name}` is not on the spreadsheet roster."
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

    reserve_in_division = reserve.division.isnumeric()
    if not reserve_in_division:
        reserve.division = driver.division
        # NOTE: not sure what the correct logic here is, driver comes from out
        # of the event, are they considered faster than current div?

    division_number = int(driver.division)
    driver_reserve = [
        d for d in starting_orders[division_number] if d.discord_id == driver.discord_id
    ][0].reserve

    driver_has_reserve = driver_reserve and driver_reserve.social_club_name != ""
    current_reserve_member: Optional[discord.Member] = None
    if driver_has_reserve:
        current_reserve_member = ctx.guild.fetch_member(driver.reserve.discord_id)

    view = discord.ui.View()
    if unassign:
        view.add_item(
            ReserveUnassignConfirmButton(
                ctx=ctx,
                bot=bot,
                spreadsheet=spreadsheet,
                driver=driver,
                driver_member=driver_member,
                reserve_member=reserve_member,
                current_reserve_member=current_reserve_member,
                label="Confirm",
                style=discord.ButtonStyle.green,
                custom_id="confirm_reserve_unassign",
            )
        )
        view.add_item(
            ReserveUnassignCancelButton(
                label="Cancel",
                style=discord.ButtonStyle.red,
                custom_id="cancel_reserve_unassign",
            )
        )

        await interaction.edit_original_response(
            content=f"Are you sure you want to unassign `{reserve.social_club_name}` as `{driver.social_club_name}'s` reserve?",
            view=view,
        )

    else:
        view.add_item(
            ReserveAssignConfirmButton(
                ctx=ctx,
                bot=bot,
                spreadsheet=spreadsheet,
                driver=driver,
                driver_member=driver_member,
                reserve_member=reserve_member,
                current_reserve_member=reserve_member,
                label="Confirm",
                style=discord.ButtonStyle.green,
                custom_id="confirm_reserve_assign",
            )
        )
        view.add_item(
            ReserveAssignCancelButton(
                label="Cancel",
                style=discord.ButtonStyle.red,
                custom_id="cancel_reserve_assign",
            )
        )

        if current_reserve_member:
            await interaction.edit_original_response(
                content=f"`{driver.social_club_name}` already has `{reserve.social_club_name}` assigned as a reserve. Are you sure you want to overwrite the current assignment with `{reserve_member.display_name}` as a reserve for `{driver_member.display_name}`?",
                view=view,
            )
        else:
            await interaction.edit_original_response(
                content=f"Are you sure you want to assign `{reserve_member.display_name}` as a reserve for `{driver_member.display_name}`?",
                view=view,
            )
