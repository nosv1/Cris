from Bot import Bot
import discord


async def on_message(bot: Bot, message: discord.Message):
    """ """

    if bot.debug and bot.is_developer(message.author):
        if message.content.startswith("..t"):
            # embed = discord.Embed(
            #     title="**Reserve Assignment**",
            #     description="**Reserve Assignment**",
            #     color=0x00FF00,
            # )
            # await message.channel.send(embed=embed)

            pass

        elif message.content.startswith("..reload"):
            bot.reload_extension("servers.tepcott.SlashCommands")
