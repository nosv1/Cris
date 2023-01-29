import discord
import re

#########   DISCORD IDs   #########

GUILD_ID: int = 450289520009543690
DIVISION_CHANNELS_IDS: list[int] = [
    0,
    702242781946576936,
    702244420153638983,
    702244753038770207,
    702245227888640091,
    796751429636980746,
    796751528861237258,]
DIVISION_ROLE_IDS: list[int] = [
    0,
    702192471316103235,
    702192533765357670,
    702192563582402650,
    702192590560428173,
    702192621891747981,
    702192638341939240,]

#########   SPREADSHEET INFO   #########

SERVICE_ACCOUNT_KEY: str = "src/servers/tepcott/google_api/tepcott.json";
SPREADSHEET_KEY: str = "1axNs6RyCy8HE8AEtH5evzBt-cxQyI8YpGutiwY8zfEU"           # season 7
ROUND_TAB_PREFIX: str = "r"

MY_SHEET_NAME: str = "my sheet"
ROSTER_SHEET_NAME: str = "roster"

ROSTER_DRIVERS_NAMED_RANGE: str = "roster_drivers"
ROSTER_SOCIAL_CLUB_LINKS_NAMED_RANGE: str = "roster_sc_links"
ROSTER_DISCORD_IDS_NAMED_RANGE: str = "roster_discord_ids"
ROSTER_DIVS_NAMED_RANGE: str = "roster_divs"
ROSTER_STATUS_NAMED_RANGE: str = "roster_statuses"

MY_SHEET_BOTTOM_DIVISION_NAMED_RANGE: str = "my_sheet_bottom_division"
MY_SHEET_ROUND_NUMBER_NAMED_RANGE: str = "my_sheet_round_number"
MY_SHEET_ROUND_TAB_DIVISION_OFFSET: str = "my_sheet_round_tab_division_offset"
MY_SHEET_STARTING_ORDER_DRIVERS_RANGE_NAMED_RANGE: str = "my_sheet_starting_order_drivers_range"
MY_SHEET_STARTING_ORDER_RESERVES_RANGE_NAMED_RANGE: str = "my_sheet_starting_order_reserves_range"

#########   FUNCTIONS   #########

async def format_discord_name(
    member: discord.Member, 
    discord_name: str, 
    social_club_name: str) -> None:
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
