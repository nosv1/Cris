from datetime import datetime
import discord
import os
import re

#########   DISCORD IDs   #########

GUILD_ID: int = 450289520009543690
DIVISION_CHANNEL_IDS: list[int] = [
    0,
    702242781946576936,
    702244420153638983,
    702244753038770207,
    702245227888640091,
    796751429636980746,
    796751528861237258,
]
DIVISION_ROLE_IDS: list[int] = [
    0,
    702192471316103235,
    702192533765357670,
    702192563582402650,
    702192590560428173,
    702192621891747981,
    702192638341939240,
]
RACER_ROLE_ID = 450401326472495105
RESERVE_ROLE_ID = 696070455194419280
SPREADSHEET_CHANNEL_ID = 894284840520802384
LATE_JOINERS_AND_RESERVES_CHANNEL_ID = 932340228277039164
RESERVE_MESSAGE_ID = 1071877411534286949

#########   COLORS   #########

LIGHT_BLUE = 5672919

#########   EMOJI STUFF   #########

DIV_EMOJI_NAME_PATTERN = r"^D\d$"
SPACE_CHAR = "⠀"
CRIS_EMOJI_ID = 450402431227002886

#########   TIME STUFF   #########

STARTING_TIMES: dict[str, list[int]] = {  # UK time, divisions
    "17:00": [2, 4, 6],
    "18:00": [1, 3, 5],
}

#########   DATABASE INFO   #########
DATABASE_NAME = "TEPCOTT"

RESERVE_REQUESTS_TABLE_NAME = "reserve_requests"
RESERVE_REQUESTS_REQUEST_IDS_COLUMN = "request_id"
RESERVE_REQUESTS_DISCORD_IDS_COLUMN = "discord_id"
RESERVE_REQUESTS_DIVISIONS_COLUMN = "division"

RESERVES_AVAILABLE_TABLE_NAME = "reserves_available"
RESERVES_AVAILABLE_AVAILABLE_IDS_COLUMN = "available_id"
RESERVES_AVAILABLE_DISCORD_IDS_COLUMN = "discord_id"
RESERVES_AVAILABLE_DIVISIONS_COLUMN = "division"  # quali div or current div of driver
RESERVES_AVAILABLE_RESERVE_DIVISIONS_COLUMN = "reserve_division"  # div button clicked

#########   SPREADSHEET INFO   #########

SERVICE_ACCOUNT_KEY = os.path.join(
    os.path.dirname(__file__), "google_api/tepcott.json"
).replace("/", os.sep)
SPREADSHEET_KEY = "1axNs6RyCy8HE8AEtH5evzBt-cxQyI8YpGutiwY8zfEU"  # season 7
ROUND_TAB_PREFIX = "r"
RESERVE_NEEDED_STRING = "RESERVE NEEDED"

MY_SHEET_NAME = "my sheet"
ROSTER_SHEET_NAME = "roster"

ROSTER_DRIVERS_NAMED_RANGE = "roster_drivers"
ROSTER_SOCIAL_CLUB_LINKS_NAMED_RANGE = "roster_sc_links"
ROSTER_DISCORD_IDS_NAMED_RANGE = "roster_discord_ids"
ROSTER_DIVS_NAMED_RANGE = "roster_divs"
ROSTER_QUALIFYING_DIVISIONS_NAMED_RANGE = "roster_qualifying_divisions"
ROSTER_STATUS_NAMED_RANGE = "roster_statuses"

MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE = "my_sheet_bottom_division"
MY_SHEET_RESERVE_REQUESTS_DISCORD_IDS_NAMED_RANGE = (
    "my_sheet_reserve_requests_discord_ids"
)
MY_SHEET_RESERVE_REQUESTS_DIVISIONS_NAMED_RANGE = "my_sheet_reserve_requests_divisions"
MY_SHEET_RESERVE_REQUESTS_RESERVES_NAMED_RANGE = "my_sheet_reserve_requests_reserves"
MY_SHEET_RESERVE_REQUESTS_ROUND_NUMBERS_NAMED_RANGE = (
    "my_sheet_reserve_requests_round_numbers"
)
MY_SHEET_ROUND_NUMBER_NAMED_RANGE = "my_sheet_round_number"
MY_SHEET_ROUND_TAB_DIVISION_OFFSET = "my_sheet_round_tab_division_offset"
MY_SHEET_STARTING_ORDER_DRIVERS_RANGE_NAMED_RANGE = (
    "my_sheet_starting_order_drivers_range"
)
MY_SHEET_STARTING_ORDER_RESERVES_RANGE_NAMED_RANGE = (
    "my_sheet_starting_order_reserves_range"
)

#########   FUNCTIONS   #########


def get_cris_emoji(guild: discord.Guild) -> discord.Emoji:
    """ """
    return discord.utils.get(guild.emojis, id=CRIS_EMOJI_ID)


def get_div_channels(channels: list[discord.TextChannel]) -> list[discord.TextChannel]:
    """div - 1"""
    div_channels = [c for c in channels if c.id in DIVISION_CHANNEL_IDS]
    div_channels.sort(key=lambda c: DIVISION_CHANNEL_IDS.index(c.id))
    return div_channels


def get_div_emojis(guild: discord.Guild) -> list[discord.Emoji]:
    """only includes active divisions"""

    div_emojis = [e for e in guild.emojis if re.match(DIV_EMOJI_NAME_PATTERN, e.name)]
    div_emojis.sort(key=lambda e: e.name)

    return div_emojis


async def format_discord_name(
    member: discord.Member, discord_name: str, social_club_name: str
) -> None:
    """ """

    re_pattern = re.compile(r"\(.*\)")
    match = re_pattern.search(discord_name)
    if match:
        inside = match.group()
        outside = discord_name.replace(inside, "").strip()
    else:
        outside = discord_name

    if outside.strip() == social_club_name:
        return

    new_name = f"{social_club_name} ({outside})".replace("()", "")
    try:
        await member.edit(nick=new_name)
        print(f"Changed nickname for {discord_name} to {new_name}")
    except Exception as e:
        print(f"Error changing nickname for {discord_name} to {new_name}: {e}")
