from Bot import Bot
import discord

from servers.tepcott.spreadsheet import Spreadsheet
from servers.tepcott.tepcott import LIGHT_BLUE, get_div_emojis


async def handle_vehicles_command(ctx: discord.ApplicationContext) -> None:
    """ """

    interaction = await ctx.send_response(
        "Are you practicing science by not doubting? I'm getting the vehicles right now - KIFFLOM!",
    )

    ss = Spreadsheet()
    vehicles = ss.get_vehicles()

    embed = discord.Embed()
    embed.color = LIGHT_BLUE
    embed.title = f"**Round {ss.round_number} Vehicles**"
    embed.description = ""

    div_emojis = get_div_emojis(ctx.guild)
    for i, vehicle in enumerate(vehicles):
        embed.description += (
            f"{div_emojis[i]} **-** [{vehicle.name}]({vehicle.gtacars_search_link})\n"
        )

    await interaction.edit_original_response(content=None, embed=embed)
