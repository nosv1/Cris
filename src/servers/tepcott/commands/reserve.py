from Bot import Bot

import discord
from discord import Message

from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver
from typing import Optional
from servers.tepcott.tepcott import (
    DIVISION_CHANNELS_IDS,
    SPREADSHEET_CHANNEL_ID,
)


async def handle_reserve_needed(
    ctx: discord.ApplicationContext, driver_member: discord.Member, bot: Bot
):
    """ """

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
            for division_number in self.spreadsheet.get_neighboring_division_numbers(
                division_number=int(self.driver.division)
            ):
                division_channel = await ctx.guild.fetch_channel(
                    DIVISION_CHANNELS_IDS[division_number]
                )
                await division_channel.send(
                    f"Hello, friends. {interaction.user.display_name} wanted to inform you all, {self.driver.social_club_name}, in Division {self.driver.division}, needs a reserve. Contact a DoubleD if you are interested in reserving - KIFFLOM!."
                )
                await interaction.message.edit(view=None)
                await interaction.response.defer()

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
            self.spreadsheet.set_reserves(
                round_number=self.spreadsheet.round_number, drivers=[self.driver]
            )

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

            await interaction.response.send_message(
                content=f"{self.ctx.author.display_name} marked {self.driver_member.display_name} as needing a reserve for Round {self.spreadsheet.round_number}.",
                view=view,
            )
            spreadsheet_channel = await self.bot.fetch_channel(SPREADSHEET_CHANNEL_ID)
            await spreadsheet_channel.send(
                f"{self.ctx.author.display_name} marked {self.driver_member.display_name} as needing a reserve for Round {self.spreadsheet.round_number}."
            )

    class ReserveNeededCancelButton(discord.ui.Button):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.view: discord.ui.View

        async def callback(self, interaction: discord.Interaction):
            self.view.disable_all_items()
            await interaction.response.edit_message(content="Cancelled", view=None)

    spreadsheet = Spreadsheet()
    _, drivers_by_discord_id = spreadsheet.get_roster_drivers()
    try:
        driver = drivers_by_discord_id[driver_member.id]
    except KeyError:
        await ctx.respond(
            content=f"`{driver_member.display_name}` is not on the spreadsheet roster.",
            ephemeral=True,
        )
    starting_orders = spreadsheet.get_starting_orders(
        round_number=spreadsheet.round_number
    )

    driver_in_division = driver.division.isnumeric()
    if not driver_in_division:
        return

    division_number = int(driver.division)
    driver_reserve = [
        d for d in starting_orders[division_number] if d.discord_id == driver.discord_id
    ][0].reserve

    driver_needs_reserve = driver_reserve.social_club_name == "RESERVE NEEDED"
    if driver_needs_reserve:
        await ctx.respond(
            content=f"`{driver_member.display_name}` is already marked as needing a reserve for Round {spreadsheet.round_number}.",
            ephemeral=True,
        )
        return

    driver.reserve = SpreadsheetDriver(social_club_name="RESERVE NEEDED")

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

    await ctx.respond(
        content=f"Are you sure you want to mark `{driver_member.display_name}` as needing a reserve for Round {spreadsheet.round_number}?",
        view=view,
        ephemeral=True,
    )


async def reserve_needed(
    ctx: discord.ApplicationContext, bot: Bot, driver_member: discord.Member
) -> None:
    """ """

    author_is_not_admin = not ctx.author.guild_permissions.administrator
    author_is_not_member = ctx.author.id != driver_member.id
    if author_is_not_member and author_is_not_admin:
        await ctx.respond(
            content="You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    await handle_reserve_needed(ctx=ctx, driver_member=driver_member, bot=bot)


# class DriversDropdown(discord.ui.Select):
#     def __init__(
#         self,
#         bot: discord.Bot,
#         placeholder: str,
#         drivers: list[SpreadsheetDriver] = [],) -> None:
#         """ """

#         self.bot = bot

#         options: list[discord.SelectOption] = []
#         for driver in drivers:
#             options.append(discord.SelectOption(
#                 label=driver.social_club_name))

#         super().__init__(
#             placeholder=placeholder,
#             min_values=1,
#             max_values=1,
#             options=options)

#     async def callback(self, interaction: discord.Interaction) -> None:
#         await interaction.response.defer()


# class ReserveCancelButton(discord.ui.Button):
#     def __init__(self, bot: discord.Bot) -> None:
#         """ """

#         self.bot = bot

#         super().__init__(
#             label="Cancel",
#             style=discord.ButtonStyle.red,
#             custom_id="cancel_reserve")

#     async def callback(self, interaction: discord.Interaction):
#         await interaction.response.edit_message(f"**Reserve cancelled**")


# class ReserveConfirmButton(discord.ui.Button):
#     def __init__(
#         self,
#         bot: discord.Bot,
#         reserve_dropdown: discord.ui.Select,
#         driver_dropdown: discord.ui.Select,
#         drivers: list[SpreadsheetDriver],
#         division_number: int) -> None:
#         """ """

#         self.bot = bot
#         self.reserve_dropdown = reserve_dropdown
#         self.driver_dropdown = driver_dropdown
#         self.drivers = drivers
#         self.division_number = division_number

#         super().__init__(
#             label="Confirm",
#             style=discord.ButtonStyle.green,
#             custom_id="confirm_reserve")

#     async def callback(self, interaction: discord.Interaction) -> None:
#         """ """

#         selected_reserve: str = self.reserve_dropdown.values[0]
#         selected_driver: str = self.driver_dropdown.values[0]

#         reserve_driver: SpreadsheetDriver = None
#         driver_driver: SpreadsheetDriver = None

#         for driver in self.drivers:
#             if driver.social_club_name == selected_reserve:
#                 reserve_driver = driver
#             elif driver.social_club_name == selected_driver:
#                 driver_driver = driver

#         reserve_found: bool = reserve_driver is not None
#         driver_found: bool = driver_driver is not None

#         if not reserve_found or not driver_found:
#             await interaction.response.defer()
#             return

#         reserve_member: discord.Member = await interaction.guild.fetch_member(
#             reserve_driver.discord_id)
#         driver_member: discord.Member = await interaction.guild.fetch_member(
#             driver_driver.discord_id)

#         # await interaction.message.delete()
#         await interaction.response.send_message(
#             content=f"**{reserve_member.mention} reserving for {driver_member.mention}**")


# class DriversDropdownView(discord.ui.View):
#     def __init__(self, bot: discord.Bot, division: str) -> None:
#         """ """

#         self.bot = bot
#         super().__init__()

#         drivers: list[SpreadsheetDriver] = get_spreadsheet_drivers()

#         drivers_in_division: list[SpreadsheetDriver] = []
#         possible_reserves: list[SpreadsheetDriver] = []
#         division_number: int = int(division)
#         for driver in drivers:
#             if driver.status == "Reserve":
#                 possible_reserves.append(driver)
#                 continue

#             if driver.division == division:
#                 drivers_in_division.append(driver)
#                 continue

#             if not driver.division.isnumeric():
#                 continue

#             is_one_div_below: bool = int(driver.division) == division_number - 1
#             is_one_div_above: bool = int(driver.division) == division_number + 1
#             if is_one_div_below or is_one_div_above:
#                 possible_reserves.append(driver)

#         drivers_in_division.sort(key=lambda d: d.social_club_name)
#         possible_reserves.sort(key=lambda d: d.social_club_name)

#         driver_dropdown: DriversDropdown = DriversDropdown(
#             placeholder="Select the driver...",
#             bot=self.bot,
#             drivers=drivers_in_division)
#         reserve_dropdown: DriversDropdown = DriversDropdown(
#             placeholder="Select the reserve...",
#             bot=self.bot,
#             drivers=possible_reserves)
#         cancel_button: ReserveCancelButton = ReserveCancelButton(
#             bot=self.bot)
#         confirm_button: ReserveConfirmButton = ReserveConfirmButton(
#             bot=self.bot,
#             reserve_dropdown=reserve_dropdown,
#             driver_dropdown=driver_dropdown,
#             drivers=drivers,
#             division_number=division_number)

#         self.add_item(driver_dropdown)
#         self.add_item(reserve_dropdown)
#         self.add_item(cancel_button)
#         self.add_item(confirm_button)


# async def reserve(
#     ctx: discord.ApplicationContext, bot: discord.Bot) -> None:
#     """ """

#     try:
#         division = "1"
#         # division: str = str(DIVISION_CHANNELS_IDS.index(ctx.channel.id))

#     except ValueError:
#         await ctx.respond(
#             content="Use this command in the division channel where the driver needs or no longer needs a reserve.",
#             ephemeral=True)
#         return

#     view: DriversDropdownView = DriversDropdownView(
#         bot=bot, division=division)

#     await ctx.respond(
#         content="**Reserve Assignment**", view=view, ephemeral=True)
