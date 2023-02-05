from Bot import Bot
from Database import Database
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
    RESERVE_NEEDED_STRING,
    SPACE_CHAR,
    get_div_emojis,
    get_div_channels,
)
from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver

from typing import Optional


def get_reserve_assignments(
    reserves_requests: list[SpreadsheetDriver],
    reserves_available: list[SpreadsheetDriver],
) -> tuple[list[SpreadsheetDriver], dict[int, list[SpreadsheetDriver]]]:
    """returns a list of all reserve needed drivers with .reserve set as a
    reserve driver or reserve needed string and then the leftover available
    reserves by division

    reserve_assignments, reserves_available_by_division"""

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

    # assign reserves
    for driver in reserves_requests:
        driver_division = int(driver.division)
        if driver_division not in reserves_available_by_division:
            driver.reserve = SpreadsheetDriver(social_club_name=RESERVE_NEEDED_STRING)
            reserve_assignments.append(driver)
            continue

        reserve = reserves_available_by_division[driver_division].pop(0)
        driver.reserve = reserve
        reserve_assignments.append(driver)

    return reserve_assignments, reserves_available_by_division


async def handle_assignment_changes(
    div_channels: list[discord.TextChannel],
    div_emojis: list[discord.Emoji],
    old_assignments: Optional[list[SpreadsheetDriver]],
    new_assignments: list[SpreadsheetDriver],
) -> None:
    """sends pings to div channels if a reserve is newly assigned or unassigned"""

    if old_assignments is None:
        return

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
        await div_channel.send(
            f"Hi, <@{reserve_id}>. For the moment, you have been unassigned as a {div_emojis[division-1]} reserve. You are still on the list, though - KIFFLOM!"
        )

    # checking if newly assigned
    for reserve_id, driver in new_reserves_by_reserve_id.items():
        no_change = reserve_id in old_reserves_by_reserve_id
        if no_change:
            continue

        division = int(driver.division)
        div_channel = div_channels[division - 1]
        await div_channel.send(
            f"Hey there, <@{reserve_id}>! You have been assigned as a {div_emojis[division-1]} reserve. You can use `/startingorder` to see who you're currently assigned to - KIFFLOM!"
        )


async def update_reserve_embed(
    msg: discord.Message,
    database: Database,
    spreadsheet: Optional[Spreadsheet] = None,
    drivers_by_discord_id: Optional[dict[int, SpreadsheetDriver]] = None,
    old_reserve_assignments: Optional[list[SpreadsheetDriver]] = None,
    reserve_reaction: bool = True,
):
    """ """

    if spreadsheet is None:
        spreadsheet = Spreadsheet()

    if drivers_by_discord_id is None:
        _, drivers_by_discord_id = spreadsheet.get_roster_drivers()

    reserve_requests = get_reserve_requests(
        database=database, drivers_by_discord_id=drivers_by_discord_id
    )
    reserves_available = get_reserves_available(
        database=database, drivers_by_discord_id=drivers_by_discord_id
    )
    reserve_assignments, reserves_available_by_division = get_reserve_assignments(
        reserves_requests=reserve_requests, reserves_available=reserves_available
    )
    if not reserve_reaction:
        # we only ping if it wasn't a reserve that reacted
        await handle_assignment_changes(
            div_channels=get_div_channels(channels=msg.guild.text_channels),
            div_emojis=get_div_emojis(guild=msg.guild),
            old_assignments=old_reserve_assignments,
            new_assignments=reserve_assignments,
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
    old_reserves_needed = get_reserve_requests(
        database=bot.tepcott_database, drivers_by_discord_id=drivers_by_discord_id
    )
    old_reserves_available = get_reserves_available(
        database=bot.tepcott_database, drivers_by_discord_id=drivers_by_discord_id
    )
    old_reserve_assignments, _ = get_reserve_assignments(
        reserves_requests=old_reserves_needed, reserves_available=old_reserves_available
    )

    driver_in_roster = driver_member.id in drivers_by_discord_id
    if not driver_in_roster:
        print(f"{driver_member.display_name} is not in the roster")
        await msg.remove_reaction(payload.emoji, driver_member)
        return

    driver = drivers_by_discord_id[driver_member.id]

    if not reaction_added:
        remove_reserve_request(database=bot.tepcott_database, driver=driver)
        driver.reserve = SpreadsheetDriver(social_club_name="")
        reserve_assignemnts = await update_reserve_embed(
            msg=msg,
            spreadsheet=spreadsheet,
            database=bot.tepcott_database,
            drivers_by_discord_id=drivers_by_discord_id,
            old_reserve_assignments=old_reserve_assignments,
            reserve_reaction=False,
        )
        spreadsheet.set_reserves(reserve_assignemnts + [driver])
        return

    driver_in_division = driver.division.isnumeric()
    if not driver_in_division:
        print(f"{driver_member.display_name} is not in a division")
        await msg.remove_reaction(payload.emoji, driver_member)
        return

    add_reserve_request(database=bot.tepcott_database, driver=driver)
    reserve_assignemnts = await update_reserve_embed(
        msg=msg,
        spreadsheet=spreadsheet,
        database=bot.tepcott_database,
        drivers_by_discord_id=drivers_by_discord_id,
        old_reserve_assignments=old_reserve_assignments,
        reserve_reaction=False,
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
    old_reserves_needed = get_reserve_requests(
        database=bot.tepcott_database, drivers_by_discord_id=drivers_by_discord_id
    )
    old_reserves_available = get_reserves_available(
        database=bot.tepcott_database, drivers_by_discord_id=drivers_by_discord_id
    )
    old_reserve_assignments, _ = get_reserve_assignments(
        reserves_requests=old_reserves_needed, reserves_available=old_reserves_available
    )

    div_emojis = get_div_emojis(guild=msg.guild)
    reserve_division_number = [
        i for i, e in enumerate(div_emojis) if e.name == payload.emoji.name
    ][0] + 1

    reserve_in_roster = reserve_member.id in drivers_by_discord_id
    if not reserve_in_roster:
        print(f"{reserve_member.display_name} is not in the roster")
        await msg.remove_reaction(payload.emoji, reserve_member)
        return

    reserve = drivers_by_discord_id[reserve_member.id]
    reserve.reserve_division = reserve_division_number

    if not reaction_added:
        remove_reserve_available(database=bot.tepcott_database, reserve=reserve)
        reserve_assignments = await update_reserve_embed(
            msg=msg,
            database=bot.tepcott_database,
            spreadsheet=spreadsheet,
            drivers_by_discord_id=drivers_by_discord_id,
            old_reserve_assignments=old_reserve_assignments,
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
    reserve_assignments = await update_reserve_embed(
        msg=msg,
        database=bot.tepcott_database,
        spreadsheet=spreadsheet,
        drivers_by_discord_id=drivers_by_discord_id,
        old_reserve_assignments=old_reserve_assignments,
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

    embed.description = (
        "⠀• If you cannot race this round, click the 👋\n"
        "⠀• If you want to reserve this round, click the division emoji(s)\n"
        "⠀• Un-clicking will remove your request/availability.\n"
        "⠀• Reserves will be pinged upon (un)assignment.\n"
        "⠀• Channel closes an hour before the races.\n"
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
