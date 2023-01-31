from Bot import Bot
import discord

from src.servers.tepcott.spreadsheet import Spreadsheet, SpreadsheetDriver


async def startingorder(ctx: discord.ApplicationContext, bot: Bot) -> None:
    """ """
    print(
        f"{ctx.author.display_name} ({ctx.author.id}) from {ctx.guild.name} ({ctx.guild.id}) used ./{ctx.command.name}"
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
            starting_order: list[
                SpreadsheetDriver
            ] = self.spreadsheet.get_starting_order(division_number=self.number)

            embed = discord.Embed()
            embed.title = f"**Division {self.number} Starting Order**"
            embed.color = ctx.guild.get_member(bot.user.id).color
            embed.description = ""
            for i, driver in enumerate(starting_order):
                position = f"**{i + 1}.**"
                driver_name = f"{driver.social_club_name}".replace("_", "\\_")
                if driver.reserve.social_club_name != "":
                    driver_name = f"~~{driver_name}~~ {driver.reserve.social_club_name}"
                embed.description += f"{position} {driver_name}\n"

            await interaction.response.edit_message(embed=embed, content="", view=None)

    spreadsheet = Spreadsheet()
    view: discord.ui.View = discord.ui.View()
    for i in range(1, spreadsheet.bottom_division_number + 1):
        view.add_item(
            NumberButton(
                ctx=ctx,
                spreadsheet=spreadsheet,
                number=i,
                label=f"Division {i}",
                style=discord.ButtonStyle.blurple,
            )
        )

    await ctx.send_response(
        "Which division's starting order would you like to see?",
        view=view,
        ephemeral=False,
    )
