from Bot import Bot
from Database import Database
from datetime import datetime, timedelta
import discord

from servers.tepcott.commands.startingtimes import get_starting_times_string
from servers.tepcott.database import (
    add_reserve_available,
    add_reserve_request,
    get_reserves_available,
    get_reserve_requests,
    remove_reserve_available,
    remove_reserve_request,
)
from servers.tepcott.tepcott import (
    DIVISION_STARTING_TIMES,
    LIGHT_BLUE,
    RESERVES_CHANNEL_ID,
    RESERVE_EMBED_MESSAGE_ID,
    RESERVE_LOG_CHANNEL_ID,
    RESERVE_NEEDED_STRING,
    RESERVE_DIVISION_ROLE_IDS,
    SPACE_CHAR,
    STARTING_TIMES,
    get_div_emojis,
    get_div_channels,
    get_roles,
    get_starting_time_timetamps,
)
from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver

from typing import Optional, Union


def get_reserve_assignments(
    database: Database, drivers_by_discord_id: dict[int, SpreadsheetDriver]
) -> tuple[list[SpreadsheetDriver], dict[int, list[SpreadsheetDriver]]]:
    """returns a list of all reserve needed drivers with .reserve set as a
    reserve driver or reserve needed string and then the leftover available
    reserves by division

    reserve_assignments, reserves_available_by_division"""

    reserve_requests = get_reserve_requests(
        database=database, drivers_by_discord_id=drivers_by_discord_id
    )
    reserves_available = get_reserves_available(
        database=database, drivers_by_discord_id=drivers_by_discord_id
    )

    # these lists are still in order of driver saying they're available
    reserves_available_by_division: dict[int, list[SpreadsheetDriver]] = {}
    for reserve in reserves_available:
        if reserve.reserve_division not in reserves_available_by_division:
            reserves_available_by_division[reserve.reserve_division] = []
        reserves_available_by_division[reserve.reserve_division].append(reserve)

    # sorting by division delta then by index (timestamp)
    for division in reserves_available_by_division:
        division_deltas: list[int] = []
        reserve_indexes: list[int] = []
        for i, reserve in enumerate(reserves_available_by_division[division]):
            division_delta = abs(reserve.interpreted_division - division)
            division_deltas.append(division_delta if division_delta > 1 else 0)
            reserve_indexes.append(i)

        # sort by delta then by index
        zipped = list(
            zip(
                division_deltas,
                reserve_indexes,
                reserves_available_by_division[division],
            )
        )
        zipped.sort(key=lambda x: (x[0], x[1]))
        reserves_available_by_division[division] = [x[2] for x in zipped]

    reserve_assignments: list[SpreadsheetDriver] = []
    # reserve_assignments is a list of all reserves needed where .reserve is
    # either set as a reserve driver or reserve needed string

    assignments_by_division: dict[int, set[int]] = {
        division: set() for division in DIVISION_STARTING_TIMES
    }
    # assignments_by_division is a dict[division: list[reserve_id]]

    # assign reserves
    for driver in reserve_requests:
        driver_division = int(driver.division)
        reserves_in_division = driver_division in reserves_available_by_division
        reserves_available_in_division = (
            reserves_in_division
            and len(reserves_available_by_division[driver_division]) > 0
        )

        if not reserves_available_in_division:
            driver.reserve = SpreadsheetDriver(social_club_name=RESERVE_NEEDED_STRING)
            reserve_assignments.append(driver)
            continue

        # find a reserve that isn't already reserving at the same time as division's race
        for i, reserve in enumerate(reserves_available_by_division[driver_division]):
            division_starting_time = DIVISION_STARTING_TIMES[driver_division]
            divisions_at_start_time = STARTING_TIMES[division_starting_time]

            is_reserving_at_time = False
            for division in divisions_at_start_time:
                is_reserving_at_time = (
                    reserve.discord_id in assignments_by_division[division]
                )
                if is_reserving_at_time:
                    break

            if not is_reserving_at_time:
                reserves_available_by_division[driver_division].pop(i)
                driver.reserve = reserve
                reserve_assignments.append(driver)
                assignments_by_division[driver_division].add(reserve.discord_id)
                break

    return reserve_assignments, reserves_available_by_division


async def handle_assignment_changes(
    guild: discord.Guild,
    reserve_log: discord.TextChannel,
    div_channels: list[discord.TextChannel],
    div_emojis: list[discord.Emoji],
    old_assignments: Optional[list[SpreadsheetDriver]],
    new_assignments: list[SpreadsheetDriver],
    reacter: Optional[discord.Member],
) -> None:
    """sends pings to div channels and reserve log if a reserve is newly assigned or unassigned"""

    if old_assignments is None:
        return

    reserve_roles = get_roles(guild=guild, role_ids=RESERVE_DIVISION_ROLE_IDS[1:])

    old_reserves_by_reserve_id: dict[int, SpreadsheetDriver] = {}  # reserve_id: driver
    for driver in old_assignments:
        if driver.reserve.social_club_name == RESERVE_NEEDED_STRING:
            continue
        old_reserves_by_reserve_id[driver.reserve.discord_id] = driver

    new_reserves_by_reserve_id: dict[int, SpreadsheetDriver] = {}  # reserve_id: driver
    for driver in new_assignments:
        if driver.reserve.social_club_name == RESERVE_NEEDED_STRING:
            continue
        new_reserves_by_reserve_id[driver.reserve.discord_id] = driver

    # checking if newly unassigned
    for reserve_id, driver in old_reserves_by_reserve_id.items():
        no_change = reserve_id in new_reserves_by_reserve_id
        if no_change:
            continue

        division = int(driver.division)
        div_channel = div_channels[division - 1]
        reserve_member = await div_channel.guild.fetch_member(reserve_id)
        await reserve_member.remove_roles(reserve_roles[division - 1])

        await reserve_log.send(
            f"{reserve_member.mention} is no longer assigned a {div_emojis[division-1]} reserve - was assigned to {driver.social_club_name}"
        )

        is_reacter = reacter is not None and reserve_id == reacter.id
        if is_reacter:
            continue

        await div_channel.send(
            f"Hi, {reserve_member.mention}. For the moment, you have been unassigned as a {div_emojis[division-1]} reserve. You are still on the list, though - KIFFLOM!"
        )

    # checking if newly assigned
    for reserve_id, driver in new_reserves_by_reserve_id.items():
        no_change = reserve_id in old_reserves_by_reserve_id
        different_driver = (
            no_change
            and driver.discord_id != old_reserves_by_reserve_id[reserve_id].discord_id
        )
        if no_change and not different_driver:
            continue

        division = int(driver.division)
        div_channel = div_channels[division - 1]
        reserve_member = await div_channel.guild.fetch_member(reserve_id)
        await reserve_member.add_roles(reserve_roles[division - 1])

        if different_driver:
            await reserve_log.send(
                f"{reserve_member.mention} is no longer assigned to {old_reserves_by_reserve_id[reserve_id].social_club_name}, but is now assigned to {driver.social_club_name} - {div_emojis[division-1]}"
            )

        else:
            await reserve_log.send(
                f"{reserve_member.mention} has been assigned to {driver.social_club_name} - {div_emojis[division-1]}"
            )

        is_reacter = reacter is not None and reserve_id == reacter.id
        if no_change or is_reacter:
            continue

        await div_channel.send(
            f"Hey there, {reserve_member.mention}! You have been assigned as a {div_emojis[division-1]} reserve. You can use `/startingorder` to see who you're currently assigned to - KIFFLOM!"
        )


async def update_reserve_embed(
    msg: discord.Message,
    database: Database,
    reserve_log: Optional[discord.TextChannel] = None,
    spreadsheet: Optional[Spreadsheet] = None,
    drivers_by_discord_id: Optional[dict[int, SpreadsheetDriver]] = None,
    old_reserve_assignments: Optional[list[SpreadsheetDriver]] = None,
    reacter: Optional[discord.Member] = None,
):
    """ """

    if reserve_log is None:
        reserve_log = await msg.guild.fetch_channel(RESERVE_LOG_CHANNEL_ID)

    if spreadsheet is None:
        spreadsheet = Spreadsheet()

    if drivers_by_discord_id is None:
        _, drivers_by_discord_id = spreadsheet.get_roster_drivers()

    reserve_assignments, reserves_available_by_division = get_reserve_assignments(
        database=database,
        drivers_by_discord_id=drivers_by_discord_id,
    )
    await handle_assignment_changes(
        guild=msg.guild,
        reserve_log=reserve_log,
        div_channels=get_div_channels(channels=msg.guild.text_channels),
        div_emojis=get_div_emojis(guild=msg.guild),
        old_assignments=old_reserve_assignments,
        new_assignments=reserve_assignments,
        reacter=reacter,
    )

    embed = msg.embeds[0]
    for field in embed.fields[:-1]:
        field.value = ""

    for driver in reserve_assignments:
        division_number = int(driver.division)

        driver_str = f"`{driver.social_club_name}`"

        has_reserve = driver.reserve.social_club_name != RESERVE_NEEDED_STRING
        if has_reserve:
            driver_str += " ✅"
            if driver.reserve.division.isnumeric():
                reserves_division = f"d{int(driver.reserve.division)}"
            else:
                reserves_division = f"rd{int(driver.reserve.qualifying_division)}"
            embed.fields[
                division_number
            ].value += f"{SPACE_CHAR*2}`{reserves_division}` **-** `{driver.reserve.social_club_name}` ✅\n"  # "    `d#` **-** `reserve` ✅"

        embed.fields[
            0
        ].value += f"{SPACE_CHAR*2}`d{division_number}` **-** {driver_str}\n"  # `    d#` **-** `driver` ✅

    for division in reserves_available_by_division:
        for reserve in reserves_available_by_division[division]:
            division_number = int(reserve.reserve_division)
            if reserve.division.isnumeric():
                reserves_division = f"d{int(reserve.division)}"
            else:
                reserves_division = f"rd{int(reserve.qualifying_division)}"
            embed.fields[
                division_number
            ].value += f"{SPACE_CHAR*2}`{reserves_division}` **-** `{reserve.social_club_name}`\n"  # "    `[r]d#` **-** `reserve`"

    for field in embed.fields[:-1]:
        field.value += SPACE_CHAR

    await msg.edit(embed=embed)

    return reserve_assignments


async def handle_reserve_needed_command(
    ctx: discord.ApplicationContext,
    bot: Bot,
    driver_member: Union[discord.Member, discord.User],
    remove_request: bool,
):
    """ """
    if isinstance(driver_member, discord.User):
        print(
            f"{driver_member.display_name} ({driver_member.id}) {'removed' if remove_request else 'added'} reserve request"
        )
    else:
        print(
            f"{driver_member.display_name} ({driver_member.id}) from {driver_member.guild.name} ({driver_member.guild.id}) {'removed' if remove_request else 'added'} reserve request"
        )
    interaction = await ctx.send_response("Processing...", ephemeral=True)

    author_is_not_admin = not ctx.author.guild_permissions.administrator
    author_is_not_member = ctx.author.id != driver_member.id or True  # OVERRIDING
    if author_is_not_member and author_is_not_admin:
        await interaction.response.edit_message(
            content="You do not have permission to use this command."
        )

    spreadsheet = Spreadsheet()
    _, drivers_by_discord_id = spreadsheet.get_roster_drivers()

    driver_in_roster = driver_member.id in drivers_by_discord_id
    if not driver_in_roster:
        await interaction.edit_original_response(
            content=f"{driver_member.display_name} is not in the roster."
        )
        return

    old_reserve_assignments, _ = get_reserve_assignments(
        database=bot.tepcott_database, drivers_by_discord_id=drivers_by_discord_id
    )

    driver = drivers_by_discord_id[driver_member.id]

    reserve_log_channel = await ctx.guild.fetch_channel(RESERVE_LOG_CHANNEL_ID)
    reserves_channel = await ctx.guild.fetch_channel(RESERVES_CHANNEL_ID)
    reserves_embed_msg = await reserves_channel.fetch_message(RESERVE_EMBED_MESSAGE_ID)
    div_emojis = get_div_emojis(guild=ctx.guild)

    if remove_request:
        remove_reserve_request(database=bot.tepcott_database, driver=driver)
        await reserve_log_channel.send(
            f"{driver_member.mention} does not need a reserve in {div_emojis[int(driver.division) - 1]}."
        )
        driver.reserve = SpreadsheetDriver(social_club_name="")
        reserve_assignemnts = await update_reserve_embed(
            msg=reserves_embed_msg,
            spreadsheet=spreadsheet,
            database=bot.tepcott_database,
            drivers_by_discord_id=drivers_by_discord_id,
            old_reserve_assignments=old_reserve_assignments,
            reacter=driver_member,
        )
        spreadsheet.set_reserves(reserve_assignemnts + [driver])
        await interaction.edit_original_response(
            content=f"{driver_member.display_name} has been marked as not needing a reserve. {reserves_channel.mention}"
        )
        return

    driver_in_division = driver.division.isnumeric()
    if not driver_in_division:
        print(f"{driver_member.display_name} is not in a division")
        await interaction.edit_original_response(
            content=f"{driver_member.display_name} is not in a division"
        )
        return

    add_reserve_request(database=bot.tepcott_database, driver=driver)
    await reserve_log_channel.send(
        f"{driver_member.mention} needs a reserve in {div_emojis[int(driver.division) - 1]}."
    )
    reserve_assignemnts = await update_reserve_embed(
        msg=reserves_embed_msg,
        spreadsheet=spreadsheet,
        database=bot.tepcott_database,
        drivers_by_discord_id=drivers_by_discord_id,
        old_reserve_assignments=old_reserve_assignments,
        reacter=driver_member,
    )
    spreadsheet.set_reserves(reserve_assignemnts)
    await interaction.edit_original_response(
        content=f"{driver_member.display_name} has been marked as needing a reserve. {reserves_channel.mention}"
    )


async def handle_reserve_needed_reaction(
    payload: discord.RawReactionActionEvent,
    bot: Bot,
    msg: discord.Message,
    driver_member: discord.Member,
    reaction_added: bool,
):
    print(
        f"{driver_member.display_name} ({driver_member.id}) from {driver_member.guild.name} ({driver_member.guild.id}) {'added' if reaction_added else 'removed'} {payload.emoji.name} to reserve embed"
    )

    spreadsheet = Spreadsheet()
    _, drivers_by_discord_id = spreadsheet.get_roster_drivers()

    driver_in_roster = driver_member.id in drivers_by_discord_id
    if not driver_in_roster:
        print(f"{driver_member.display_name} is not in the roster")
        await msg.remove_reaction(payload.emoji, driver_member)
        return

    old_reserve_assignments, _ = get_reserve_assignments(
        database=bot.tepcott_database, drivers_by_discord_id=drivers_by_discord_id
    )

    driver = drivers_by_discord_id[driver_member.id]

    reserve_log_channel = await msg.guild.fetch_channel(RESERVE_LOG_CHANNEL_ID)
    div_emojis = get_div_emojis(guild=msg.guild)

    if not reaction_added:
        remove_reserve_request(database=bot.tepcott_database, driver=driver)
        await reserve_log_channel.send(
            f"{driver_member.mention} no longer needs a reserve in {div_emojis[int(driver.division) - 1]}"
        )
        driver.reserve = SpreadsheetDriver(social_club_name="")
        reserve_assignemnts = await update_reserve_embed(
            msg=msg,
            spreadsheet=spreadsheet,
            database=bot.tepcott_database,
            drivers_by_discord_id=drivers_by_discord_id,
            old_reserve_assignments=old_reserve_assignments,
            reacter=driver_member,
        )
        spreadsheet.set_reserves(reserve_assignemnts + [driver])
        return

    driver_in_division = driver.division.isnumeric()
    if not driver_in_division:
        print(f"{driver_member.display_name} is not in a division")
        await msg.remove_reaction(payload.emoji, driver_member)
        return

    add_reserve_request(database=bot.tepcott_database, driver=driver)
    await reserve_log_channel.send(
        f"{driver_member.mention} needs a reserve in {div_emojis[int(driver.division - 1)]}"
    )
    reserve_assignemnts = await update_reserve_embed(
        msg=msg,
        spreadsheet=spreadsheet,
        database=bot.tepcott_database,
        drivers_by_discord_id=drivers_by_discord_id,
        old_reserve_assignments=old_reserve_assignments,
        reacter=driver_member,
    )
    spreadsheet.set_reserves(reserve_assignemnts)


async def handle_reserve_available_reaction(
    payload: discord.RawReactionActionEvent,
    bot: Bot,
    msg: discord.Message,
    reserve_member: discord.Member,
    reaction_added: bool,
):
    print(
        f"{reserve_member.display_name} ({reserve_member.id}) from {reserve_member.guild.name} ({reserve_member.guild.id}) {'added' if reaction_added else 'removed'} {payload.emoji.name} to reserve embed"
    )

    spreadsheet = Spreadsheet()
    _, drivers_by_discord_id = spreadsheet.get_roster_drivers()

    reserve_in_roster = reserve_member.id in drivers_by_discord_id
    if not reserve_in_roster:
        print(f"{reserve_member.display_name} is not in the roster")
        await msg.remove_reaction(payload.emoji, reserve_member)
        return

    old_reserve_assignments, _ = get_reserve_assignments(
        database=bot.tepcott_database, drivers_by_discord_id=drivers_by_discord_id
    )

    div_emojis = get_div_emojis(guild=msg.guild)
    reserve_division_number = [
        i for i, e in enumerate(div_emojis) if e.name == payload.emoji.name
    ][0] + 1

    reserve = drivers_by_discord_id[reserve_member.id]
    reserve.reserve_division = reserve_division_number

    reserve_log_channel = await msg.guild.fetch_channel(RESERVE_LOG_CHANNEL_ID)

    if not reaction_added:
        remove_reserve_available(database=bot.tepcott_database, reserve=reserve)
        await reserve_log_channel.send(
            f"{reserve_member.mention} is not available to reserve for {payload.emoji}"
        )
        reserve_assignments = await update_reserve_embed(
            msg=msg,
            database=bot.tepcott_database,
            spreadsheet=spreadsheet,
            drivers_by_discord_id=drivers_by_discord_id,
            old_reserve_assignments=old_reserve_assignments,
            reacter=reserve_member,
        )
        spreadsheet.set_reserves(reserve_assignments)
        return

    reserve_eligible_for_division = (
        reserve.interpreted_division - reserve_division_number
    ) >= -1
    if not reserve_eligible_for_division:
        print(
            f"{reserve_member.display_name} is not eligible for division {reserve_division_number}"
        )
        await msg.remove_reaction(payload.emoji, reserve_member)
        return

    reserve_in_division = reserve.division.isnumeric()
    if reserve_in_division:
        same_time_as_race = (
            DIVISION_STARTING_TIMES[int(reserve.division)]
            == DIVISION_STARTING_TIMES[reserve_division_number]
        )
        if same_time_as_race:
            print(
                f"{reserve_member.display_name} is already in division {reserve.division} which starts at the same time as division {reserve_division_number}"
            )
            await msg.remove_reaction(payload.emoji, reserve_member)
            return

    add_reserve_available(database=bot.tepcott_database, reserve=reserve)
    await reserve_log_channel.send(
        f"{reserve_member.mention} is available to reserve for {payload.emoji}"
    )
    reserve_assignments = await update_reserve_embed(
        msg=msg,
        database=bot.tepcott_database,
        spreadsheet=spreadsheet,
        drivers_by_discord_id=drivers_by_discord_id,
        old_reserve_assignments=old_reserve_assignments,
        reacter=reserve_member,
    )
    spreadsheet.set_reserves(reserve_assignments)


async def clear_reserves_reactions(msg: discord.Message):
    """ """
    await msg.clear_reactions()


async def add_reserves_reactions(msg: discord.Message):
    """ """
    await msg.add_reaction("👋")

    div_emojis = get_div_emojis(guild=msg.guild)[: Spreadsheet().bottom_division_number]
    for div_emoji in div_emojis:
        await msg.add_reaction(div_emoji)


async def reset_reserve_msg(msg: discord.Message):
    """ """
    print(f"Resetting reserve embed in {msg.guild.name} ({msg.guild.id})")

    await clear_reserves_reactions(msg=msg)
    await add_reserves_reactions(msg=msg)

    reserve_roles = get_roles(guild=msg.guild, role_ids=RESERVE_DIVISION_ROLE_IDS[1:])
    for role in reserve_roles:
        for member in role.members:
            await member.remove_roles(role)

    embed = msg.embeds[0]
    embed.color = discord.Color(LIGHT_BLUE)
    embed.clear_fields()
    spreadsheet = Spreadsheet()

    content_str = (
        "**Reserve Rules**\n"
        "⠀• Reserves are assigned on a first-come-first-served basis.\n"
        "⠀• Reserves can be 1 division faster or any division slower.\n"
        "⠀• Reserves within 1 division are given priority.\n"
        "⠀• Reserves cannot promote a driver, and they only score 75% points for the driver.\n"
        "⠀• Reserves from a faster division start at the back.\n"
        "⠀💥 Contact a DoubleD if you have a reserve from outside of the event.\n"
        "\n"
        f"{get_starting_times_string(tepcott_guild=msg.guild, bottom_division_number=spreadsheet.bottom_division_number)}\n"
    )

    starting_time_timestamps = get_starting_time_timetamps()
    hour_before_first_races = datetime.fromtimestamp(
        starting_time_timestamps[2]
    ) - timedelta(hours=1)
    embed.description = (
        f"⠀• If you cannot race this round, click the 👋\n"
        f"⠀• If you want to reserve this round, click the division emoji(s)\n"
        f"⠀• Un-clicking will remove your request/availability.\n"
        f"⠀• Reserves will be pinged upon (un)assignment.\n"
        f"⠀• Channel closes an hour before the first races. <t:{int(hour_before_first_races.timestamp())}:R>"
        f"{SPACE_CHAR}"
    )

    embed.add_field(name="**Reserve needed for:**", value=SPACE_CHAR, inline=False)

    div_emojis = get_div_emojis(guild=msg.guild)
    for div in range(spreadsheet.bottom_division_number):
        embed.add_field(
            name=f"**{div_emojis[div]} Reserves:**", value=SPACE_CHAR, inline=False
        )

    embed.add_field(
        name="**Extra information:**",
        value=(
            "⠀• ✅ indicates a driver is assigned a reserve and vice-versa\n"
            "⠀• `rd#` indicates driver is a reserve and is not in a division\n"
        ),
    )

    await msg.edit(content=content_str, embed=embed)
