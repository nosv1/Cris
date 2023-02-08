from Bot import Bot
import discord

from servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver
from servers.tepcott.tepcott import get_div_emojis


async def startingorder(ctx: discord.ApplicationContext, bot: Bot) -> None:
    """ """
    print(
        f"{ctx.author.display_name} ({ctx.author.id}) from {ctx.guild.name} ({ctx.guild.id}) used ./{ctx.command.name}"
    )

    interaction = await ctx.send_response(
        "My friend, please wait, as I determine which divisions are racing - KIFFLOM!"
    )

    class NumberButton(discord.ui.Button):
        def __init__(
            self,
            ctx: discord.ApplicationContext,
            spreadsheet: Spreadsheet,
            number: int,
            **kwargs,
        ) -> None:
            """ """

            super().__init__(**kwargs)

            self.spreadsheet = spreadsheet
            self.number = number

        async def callback(self, interaction: discord.Interaction):
            """ """
            await interaction.response.edit_message(
                content="Almost there. I'm getting the starting order *right now* - KIFFLOM!",
                view=None,
            )

            starting_order: list[
                SpreadsheetDriver
            ] = self.spreadsheet.get_starting_order(division_number=self.number)

            embed = discord.Embed()
            embed.title = f"**Division {self.number} Starting Order**"
            embed.color = ctx.guild.get_member(bot.user.id).color
            embed.description = ""
            for i, driver in enumerate(starting_order):
                position = f"**{i + 1}.**"
                driver_name = f"[{driver.social_club_name}]({driver.social_club_link})"
                driver_needs_reserve = driver.reserve.social_club_name != ""
                if driver_needs_reserve:
                    reserve_is_driver = driver.reserve.discord_id is not None
                    reserve_in_division = driver.reserve.division.isnumeric()
                    if reserve_is_driver:
                        reserve_division_str = f"d{driver.reserve.interpreted_division}"
                        if not reserve_in_division:
                            reserve_division_str = f"r{reserve_division_str}"
                        driver_name = f"~~{driver_name}~~ **>>** [({reserve_division_str}) {driver.reserve.social_club_name}]({driver.reserve.social_club_link})"
                        # ~~driver~~ reserve
                    else:
                        driver_name = (
                            f"~~{driver_name}~~ **>>** {driver.reserve.social_club_name}"
                            # ~~driver~~ RESERVE NEEDED
                        )
                embed.description += f"{position} {driver_name}\n"

            await interaction.message.edit(content=None, embed=embed)

    spreadsheet = Spreadsheet()
    view: discord.ui.View = discord.ui.View()
    div_emojis = get_div_emojis(guild=ctx.guild)
    for i in range(1, spreadsheet.bottom_division_number + 1):
        view.add_item(
            NumberButton(
                ctx=ctx,
                spreadsheet=spreadsheet,
                number=i,
                # label=f"Division {i}",
                emoji=div_emojis[i-1],
                style=discord.ButtonStyle.gray,
            )
        )

    await interaction.edit_original_response(
        content="Which division's starting order would you like to see?",
        view=view,
    )
