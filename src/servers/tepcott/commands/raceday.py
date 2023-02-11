from Bot import Bot
import discord
from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver
from servers.tepcott.tepcott import (
    DIVISION_ROLE_IDS,
    LIGHT_BLUE,
    RESERVE_DIVISION_ROLE_IDS,
    get_div_emojis,
    get_roles,
    get_starting_time_timetamps,
)


async def create_raceday_embed(
    guild: discord.Guild,
    spreadsheet: Spreadsheet,
    division_number: int,
    div_emoji: discord.Emoji,
) -> tuple[str, discord.Embed]:
    """ """
    track = spreadsheet.get_track()
    vehicle = spreadsheet.get_vehicles()[division_number - 1]
    starting_time_timestamp = get_starting_time_timetamps()[division_number]
    lap_count, pit_window = spreadsheet.get_lap_counts_pit_widows()[division_number - 1]
    pit_marshals = spreadsheet.get_pit_marshals()[division_number - 1]
    pit_marshal_members = [
        await guild.fetch_member(pm.discord_id) for pm in pit_marshals
    ]
    div_role = get_roles(guild=guild, role_ids=DIVISION_ROLE_IDS[1:])[
        division_number - 1
    ]
    reserve_div_role = get_roles(guild=guild, role_ids=RESERVE_DIVISION_ROLE_IDS[1:])[
        division_number - 1
    ]

    embed = discord.Embed()
    embed.color = LIGHT_BLUE
    embed.title = f"**{div_emoji} __Race Details__**"
    content = f"{div_role.mention} {reserve_div_role.mention} {' '.join(pm.mention for pm in pit_marshal_members)}"
    embed.description = (
        f"**Starting time:** <t:{starting_time_timestamp}:t> **|** <t:{starting_time_timestamp}:R>\n"
        f"**Track:** {track.name} [SC]({track.social_club_search_link}) **|** [GTALens]({track.gtalens_search_link})\n"
        f"**Vehicle:** [{vehicle.name}]({vehicle.gtavehicles_search_link})\n"
        f"**Laps:** {lap_count}\n"
        f"**Pit-window:** {pit_window}\n"
        f"**Pit-marshal(s):** {', '.join(f'[{pm.social_club_name}]({pm.social_club_link})' for pm in pit_marshals)}\n"
    )
    embed.set_footer(
        text="Be in the voice chat and ready to receive an invite 15 minutes before starting time."
    )

    return content, embed


async def handle_raceday_command(ctx: discord.ApplicationContext, bot: Bot) -> None:
    """ """

    author_is_not_admin = not ctx.author.guild_permissions.administrator
    if author_is_not_admin:
        await ctx.respond(
            content="You do not have permission to use this command.",
            ephemeral=True,
        )
        return

    interaction = await ctx.send_response(
        f"Happy race day! I'm just checking how many divisions are racing today - KIFFLOM!"
    )

    class DivisionNumberButton(discord.ui.Button):
        def __init__(self, spreadsheet: Spreadsheet, division_number: int, **kwargs):
            """ """

            super().__init__(**kwargs)

            self.spreadsheet = spreadsheet
            self.division_number = division_number

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.edit_message(
                content="Delighful, I'm getting the details *right now* - KIFFLOM!",
                view=None,
            )

            content, embed = await create_raceday_embed(
                guild=ctx.guild,
                spreadsheet=self.spreadsheet,
                division_number=self.division_number,
                div_emoji=self.emoji,
            )
            await interaction.message.edit(content=content, embed=embed)

    spreadsheet = Spreadsheet()
    view = discord.ui.View()
    div_emojis = get_div_emojis(guild=ctx.guild)
    for division_number in range(1, spreadsheet.bottom_division_number + 1):
        view.add_item(
            DivisionNumberButton(
                spreadsheet=spreadsheet,
                division_number=division_number,
                emoji=div_emojis[division_number - 1],
                style=discord.ButtonStyle.gray,
            )
        )

    await interaction.edit_original_response(
        content="Which division's details would you like to see?",
        view=view,
    )
