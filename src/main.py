from Bot import Bot

import discord

import event_handlers.on_message as eh_on_message
import event_handlers.on_raw_reaction as eh_on_raw_reaction
import event_handlers.on_ready as eh_on_ready

import os

from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot: Bot = Bot(debug=os.getenv("DEBUG").lower() == "true", intents=intents)
# bot.load_extension("servers.tepcott.SlashCommands")

########################    EVENT HANDLERS    ########################


@bot.event
async def on_ready():
    """ """

    await eh_on_ready.on_ready(bot)


@bot.event
async def on_message(message: discord.Message):
    """ """

    await eh_on_message.on_message(bot, message)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """ """

    await eh_on_raw_reaction.on_raw_reaction(payload, bot, reaction_added=True)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """ """

    await eh_on_raw_reaction.on_raw_reaction(payload, bot, reaction_added=False)


########################    MAIN    ########################

if __name__ == "__main__":
    # token: str = os.getenv("PROTO_DISCORD_TOKEN")
    token: str = os.getenv("CRIS_DISCORD_TOKEN")
    # token: str = os.getenv("MOBOT_DISCORD_TOKEN")
    bot.run(token)
