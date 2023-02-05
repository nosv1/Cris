from Bot import Bot
from datetime import datetime, timedelta, timezone
import discord
import pytz
import re

from servers.tepcott.spreadsheet import Spreadsheet
from servers.tepcott.tepcott import STARTING_TIMES, get_div_emojis


def get_starting_times_string(
    tepcott_guild: discord.Guild, bottom_division_number: int
) -> str:
    """ """

    div_emojis = get_div_emojis(tepcott_guild)

    timezone = pytz.timezone("Europe/London")
    dt = datetime.now(timezone)

    is_sunday_in_london = dt.weekday() == 6
    if not is_sunday_in_london:
        dt += timedelta(days=6 - dt.weekday())

    # **Starting Times**
    # **D2, D4, D6:** 17:00 UTC **/** HH:MM local
    # *8D1, D3, D5:** 18:00 UTC **/** HH:MM local
    # HH:MM is a discord timestamp <:epoch:t>
    starting_times_string = "**Starting Times**:\n"

    for starting_time, divisions in STARTING_TIMES.items():
        starting_time = datetime.strptime(starting_time, "%H:%M")
        starting_time = starting_time.replace(year=dt.year, month=dt.month, day=dt.day)
        starting_time = timezone.localize(starting_time)
        # start time in london time

        starting_time_utc = starting_time.astimezone(pytz.utc)
        starting_time_utc = starting_time_utc.strftime("%H:%M UTC")
        # start time in UTC

        # join div emojis: utc / local
        starting_times_string += f"**{', '.join([f'{div_emojis[d-1]}' for d in divisions if d <= bottom_division_number])}:** {starting_time_utc} **/** <t:{starting_time.timestamp():.0f}:t> local\n"

    return starting_times_string


async def startingtimes(ctx: discord.ApplicationContext, bot: Bot) -> None:
    """ """
    print(
        f"{ctx.author.display_name} ({ctx.author.id}) from {ctx.guild.name} ({ctx.guild.id}) used ./{ctx.command.name}"
    )

    interaction = await ctx.respond(
        content="Hi there... I'm just figuring out how many divisions are active real quick. - KIFFLOM!"
    )
    spreadsheet = Spreadsheet()

    await interaction.edit_original_response(
        content=get_starting_times_string(
            tepcott_guild=ctx.guild,
            bottom_division_number=spreadsheet.bottom_division_number,
        )
    )
