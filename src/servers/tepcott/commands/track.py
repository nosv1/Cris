from Bot import Bot
import discord

from servers.tepcott.spreadsheet import Spreadsheet
from servers.tepcott.tepcott import LIGHT_BLUE, get_div_emojis


async def handle_track_command(ctx: discord.ApplicationContext) -> None:
    """ """

    interaction = await ctx.send_response(
        "Making the assult on happiness every week. I'm getting the track right now - KIFFLOM!",
    )

    ss = Spreadsheet()
    track = ss.get_track()

    embed = discord.Embed()
    embed.color = LIGHT_BLUE
    embed.title = f"**Round {ss.round_number} Track**"
    embed.description = f"{track.name} - [SC]({track.social_club_search_link}) **|** [GTALens]({track.gtalens_search_link})"

    await interaction.edit_original_response(content=None, embed=embed)
