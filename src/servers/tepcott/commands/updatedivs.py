from Bot import Bot

import discord
from discord import Member, Message, Role

from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver
from servers.tepcott.tepcott import (
    DIVISION_CHANNELS_IDS,
    DIVISION_ROLE_IDS,
    RACER_ROLE_ID,
    format_discord_name,
)

from typing import Optional


async def update_division_roles(ctx: discord.ApplicationContext, msg: Message) -> None:
    """ """

    spreadsheet = Spreadsheet()
    driver_by_social_club_name: dict[str, SpreadsheetDriver]
    driver_by_social_club_name, _ = spreadsheet.get_roster_drivers()

    racer_role = ctx.guild.get_role(RACER_ROLE_ID)
    division_roles: list[Role] = [None] * len(DIVISION_ROLE_IDS)
    division_channels: list[discord.TextChannel] = [None] * len(DIVISION_CHANNELS_IDS)
    promotions_by_division: list[list[Optional[Member]]] = [
        [] for _ in range(len(DIVISION_ROLE_IDS))
    ]
    demotions_by_division: list[list[Optional[Member]]] = [
        [] for _ in range(len(DIVISION_ROLE_IDS))
    ]
    # [0] is not used because division 0 is not a thing

    for role in ctx.guild.roles:
        if role.id in DIVISION_ROLE_IDS:
            division_roles[DIVISION_ROLE_IDS.index(role.id)] = role

    for channel in await ctx.guild.fetch_channels():
        if channel.id in DIVISION_CHANNELS_IDS:
            division_channels[DIVISION_CHANNELS_IDS.index(channel.id)] = channel

    total_drivers = len(driver_by_social_club_name)
    for i, driver in enumerate(driver_by_social_club_name.values()):
        if i + 1 % 10 == 0:
            await msg.edit(
                content=f"Updating division roles... ({i+1}/{total_drivers})"
            )
        # looping spreadsheet drivers
        # if driver in a division, update their name

        # loop driver roles
        # if role is a divivion role, check if driver should have it
        # if driver should not have it, remove it

        # if driver should be in a division, add the correct division role

        driver_in_division = driver.division.isnumeric()
        driver_is_reserve = driver.status == "Reserve"
        driver_in_waiting_list = driver.division == "WL"
        try:
            driver_member = await ctx.guild.fetch_member(driver.discord_id)
        except discord.errors.NotFound:
            if driver_in_division or driver_is_reserve or driver_in_waiting_list:
                await ctx.channel.send(
                    content=f"{driver.social_club_name} does not exist in the guild anymore",
                    ephemeral=True,
                )
            continue

        driver_has_racer_role = racer_role in driver_member.roles

        if driver_in_division or driver_is_reserve or driver_in_waiting_list:
            await format_discord_name(
                member=driver_member,
                discord_name=driver_member.display_name,
                social_club_name=driver.social_club_name,
            )

        for role in driver_member.roles:
            if role not in division_roles:
                continue

            division_index = division_roles.index(role)

            incorrect_division_role = (
                not driver_in_division
                or role.id != DIVISION_ROLE_IDS[int(driver.division)]
            )

            if incorrect_division_role:
                demotions_by_division[division_index].append(driver_member)
                try:
                    await driver_member.remove_roles(role)
                    print(f"Removed {role.name} from {driver_member.display_name}")

                except discord.errors.Forbidden:
                    await ctx.channel.send(
                        content=f"Not enough permissions to remove {role.name} from {driver_member.display_name}",
                        ephemeral=True,
                    )

                except discord.errors.HTTPException:
                    await ctx.channel.send(
                        content=f"HTTPException when removing {role.name} from {driver_member.display_name}",
                        ephemeral=True,
                    )

        if not driver_in_division and not driver_in_waiting_list:
            try:
                if driver_has_racer_role:
                    await driver_member.remove_roles(racer_role)
                    print(
                        f"Removed {racer_role.name} from {driver_member.display_name}"
                    )

            except discord.errors.Forbidden:
                await ctx.channel.send(
                    content=f"Not enough permissions to remove {racer_role.name} from {driver_member.display_name}",
                    ephemeral=True,
                )

            except discord.errors.HTTPException:
                await ctx.channel.send(
                    content=f"HTTPException when removing {racer_role.name} from {driver_member.display_name}",
                    ephemeral=True,
                )
            continue

        if driver_in_division or driver_in_waiting_list:
            try:
                if not driver_has_racer_role:
                    await driver_member.add_roles(racer_role)
                    print(f"Added {racer_role.name} to {driver_member.display_name}")

            except discord.errors.Forbidden:
                await ctx.channel.send(
                    content=f"Not enough permissions to add {racer_role.name} to {driver_member.display_name}",
                    ephemeral=True,
                )

            except discord.errors.HTTPException:
                await ctx.channel.send(
                    content=f"HTTPException when removing {racer_role.name} from {driver_member.display_name}",
                    ephemeral=True,
                )

        if not driver_in_division:
            continue

        division_index = int(driver.division)
        correct_division_role = division_roles[division_index]
        does_not_have_correct_role = correct_division_role not in driver_member.roles
        if driver_in_division and does_not_have_correct_role:
            promotions_by_division[division_index].append(driver_member)
            try:
                await driver_member.add_roles(correct_division_role)
                print(
                    f"Added {correct_division_role.name} to {driver_member.display_name}"
                )

            except discord.errors.Forbidden:
                await ctx.channel.send(
                    content=f"Not enough permissions to add {correct_division_role.name} to {driver_member.display_name}",
                    ephemeral=True,
                )
                continue

            except discord.errors.HTTPException:
                await ctx.channel.send(
                    content=f"HTTPException when adding {correct_division_role.name} to {driver_member.display_name}",
                    ephemeral=True,
                )
                continue

    # TODO: HEY YOU THIS SHOULD ONLY BE HERE FOR PRE-ROUND 1, IT SHOULD CHANGE AFTER
    division_welcome_messages = [
        "",  # 0
        "Division 1, the ultimate test of will and determination. Welcome, my fellow epsilonsist - KIFFLOM!",
        "The time has come as we race towards ultimate understanding. Welcome, my friends, to Division 2 - KIFFLOM!"
        "Come, let's find truth together. Welcome, my beloved believers in Kraff, to Division 3 - KIFFLOM!"
        "The path to truth and glory begins here. Welcome, truth seekers, to Division 4 - KIFFLOM!",
        "Let us begin the journey to enlightenment. Welcome, followers, to Division 5 - KIFFLOM!",
    ]

    for div, channel in enumerate(division_channels):
        if div == 0:
            continue

        promotion_message = f"**{division_welcome_messages[div]}**\n"
        # demotion_message = f"**{division_welcome_messages[div]}**\n"

        promotion_message += "\n".join(
            [f" - {member.mention}" for member in promotions_by_division[div]]
        )
        # demotion_message += "\n".join(
        #     [f" - {member.mention}" for member in demotions_by_division[div]]
        # )

        # if promotions_by_division[div] != []:
        #     await channel.send(promotion_message)
        # if demotions_by_division[div] != []:
        #     await channel.send(demotion_message)


async def updatedivs(ctx: discord.ApplicationContext, bot: Bot) -> None:
    """ """
    print(
        f"{ctx.author.display_name} ({ctx.author.id}) from {ctx.guild.name} ({ctx.guild.id}) used ./{ctx.command.name}"
    )

    if not ctx.author.guild_permissions.administrator:
        await ctx.send(
            content="You do not have permission to use this command", ephemeral=True
        )
        return

    class ConfirmButton(discord.ui.Button):
        def __init__(self, ctx: discord.ApplicationContext, **kwargs):
            super().__init__(**kwargs)

            self.view: discord.ui.View
            self.ctx = ctx
            self.msg: Optional[Message] = None

        async def callback(self, interaction: discord.Interaction):
            self.view.disable_all_items()
            self.msg = await interaction.response.send_message(
                content="Updating division roles..."
            )
            await update_division_roles(self.ctx)
            await self.msg.edit(content="Updated division roles")

    class CancelButton(discord.ui.Button):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.view: discord.ui.View

        async def callback(self, interaction: discord.Interaction):
            self.view.disable_all_items()
            await interaction.response.edit_message(content="Cancelled", view=None)

    view = discord.ui.View()
    view.add_item(ConfirmButton(ctx, label="Yes", style=discord.ButtonStyle.green))
    view.add_item(CancelButton(label="No", style=discord.ButtonStyle.red))
    await ctx.send_response(
        f"Update division roles for **Round {Spreadsheet().round_number}**?",
        view=view,
        ephemeral=True,
    )

    # view: InitialView = InitialView(bot=bot)

    # await ctx.respond(view=view, ephemeral=True)

    # ctx.author.guild_permissions.administrator()
