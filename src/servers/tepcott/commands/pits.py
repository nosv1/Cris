import discord

from servers.tepcott.spreadsheet import Spreadsheet


async def handle_pits_command(ctx: discord.ApplicationContext) -> None:
    """ """

    interaction = await ctx.send_response(
        f"You're happy, you just don't know it yet. I'm getting the pit demo *right now* - KIFFLOM!",
    )

    spreadsheet = Spreadsheet()
    pit_demo_link = spreadsheet.get_pit_demo_link()

    await interaction.edit_original_response(content=pit_demo_link)
