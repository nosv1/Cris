
from Bot import Bot

import discord
from discord import Member, Role

from src.servers.tepcott.spreadsheet import Spreadsheet
from src.servers.tepcott.tepcott import (
    DIVISION_CHANNELS_IDS,
    DIVISION_ROLE_IDS,
    format_discord_name)

from typing import Optional

async def update_division_roles(ctx: discord.ApplicationContext) -> None:
    """ """

    spreadsheet = Spreadsheet()
    drivers = spreadsheet.get_roster_drivers()

    division_roles: list[Role] = [None] * len(DIVISION_ROLE_IDS)
    division_channels: list[discord.TextChannel] = [None] * len(DIVISION_ROLE_IDS)
    promotions_by_division: list[list[Optional[Member]]] = [[] for _ in range(len(DIVISION_ROLE_IDS))]
    demotions_by_division: list[list[Optional[Member]]] = [[] for _ in range(len(DIVISION_ROLE_IDS))]
    # [0] is not used because division 0 is not a thing

    for role in ctx.guild.roles:
        if role.id in DIVISION_ROLE_IDS:
            division_roles[DIVISION_ROLE_IDS.index(role.id)] = role

    for channel in ctx.guild.channels:
        if channel.id in DIVISION_CHANNELS_IDS:
            division_channels[DIVISION_CHANNELS_IDS.index(channel.id)] = channel

    for driver in drivers.values():      
        # looping spreadsheet drivers
        # if driver in a division, update their name

        # loop driver roles
        # if role is a divivion role, check if driver should have it
        # if driver should not have it, remove it

        # if driver should be in a division, add the correct division role

        driver_in_division = driver.division.isnumeric()
        try:
            driver_member = await ctx.guild.fetch_member(driver.discord_id)
        except discord.errors.NotFound:
            if driver_in_division:
                await ctx.channel.send(
                    content=f"Driver {driver.social_club_name} does not exist in the guild anymore", ephemeral=True)
            continue

        if driver_in_division:
            await format_discord_name(
                member=driver_member,
                discord_name=driver_member.display_name,
                social_club_name=driver.social_club_name)

        for role in driver_member.roles:
            if role not in division_roles:
                continue

            division_index = division_roles.index(role)

            incorrect_division_role = (
                not driver_in_division 
                or role.id != DIVISION_ROLE_IDS[int(driver.division)])

            if incorrect_division_role:
                await driver_member.remove_roles(role)
                print(f"Removed {role.name} from {driver_member.display_name}")
                demotions_by_division[division_index].append(driver_member)

        if driver_in_division:
            division_index = int(driver.division)
            correct_division_role = division_roles[division_index]
            await driver_member.add_roles(correct_division_role)
            print(f"Added {correct_division_role.name} to {driver_member.display_name}")
            promotions_by_division[division_index].append(driver_member)

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
        
        promotion_message += "\n".join([
            f" - {member.mention}" 
            for member 
            in promotions_by_division[div]])
        demotion_message += "\n".join([
            f" - {member.mention}"
            for member
            in demotions_by_division[div]])

        if promotions_by_division[div] != []:
            await channel.send(promotion_message)
        if demotions_by_division[div] != []:
            await channel.send(demotion_message)

async def updatedivs(
    ctx: discord.ApplicationContext, bot: Bot) -> None:
    """ """

    class ConfirmButton(discord.ui.Button):
        def __init__(self, ctx: discord.ApplicationContext, **kwargs):
            super().__init__(**kwargs)

            self.view: discord.ui.View
            self.ctx = ctx

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.edit_message(content="Updating division roles...", view=None)
            await update_division_roles(self.ctx)
            await interaction.response.edit_message(content="Updated division roles")

            
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
        ephemeral=True)

    # view: InitialView = InitialView(bot=bot)

    # await ctx.respond(view=view, ephemeral=True)

    # ctx.author.guild_permissions.administrator()