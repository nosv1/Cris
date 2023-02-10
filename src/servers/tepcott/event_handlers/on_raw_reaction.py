import asyncio
from Bot import Bot
import discord
import re

from servers.tepcott.reserves import (
    handle_reserve_available_reaction,
    handle_reserve_needed_reaction,
    reset_reserve_msg,
    update_reserve_embed,
)
from servers.tepcott.tepcott import RESERVE_EMBED_MESSAGE_ID, get_cris_emoji


async def fetch_guild(payload: discord.RawReactionActionEvent, bot: Bot):
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        guild = await bot.fetch_guild(payload.guild_id)
    return guild


async def fetch_member(
    payload: discord.RawReactionActionEvent, bot: Bot, guild: discord.Guild
):
    if not guild:
        guild = await fetch_guild(payload, bot)
    member = guild.get_member(payload.user_id)
    if not member:
        member = await guild.fetch_member(payload.user_id)
    return member


async def fetch_channel(
    payload: discord.RawReactionActionEvent, bot: Bot, guild: discord.Guild
):
    if not guild:
        guild = await fetch_guild(payload, bot)
    channel = await guild.fetch_channel(payload.channel_id)
    return channel


async def fetch_message(
    payload: discord.RawReactionActionEvent,
    bot: Bot,
    channel: discord.TextChannel,
):
    if not channel:
        channel = await fetch_channel(payload, bot)
    msg = await channel.fetch_message(payload.message_id)
    return msg


async def on_raw_reaction(
    payload: discord.RawReactionActionEvent, bot: Bot, reaction_added=True
):
    """ """

    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    msg = channel.get_partial_message(payload.message_id)
    member = guild.get_member(payload.user_id)

    if not member:
        member = await fetch_member(payload, bot, guild)

    if member.bot:
        return

    is_reserve_message = payload.message_id == RESERVE_EMBED_MESSAGE_ID
    member_is_admin = member.guild_permissions.administrator

    if is_reserve_message:
        if not isinstance(msg, discord.Message):
            msg = await fetch_message(payload, bot, channel)

        is_wave_emoji = payload.emoji.name == "👋"
        is_div_emoji = re.match(r"D\d", payload.emoji.name)
        is_x_emoji = payload.emoji.name == "❌"
        is_counterclockwise_arrow_emoji = payload.emoji.name == "🔄"

        if is_x_emoji and member_is_admin:
            await reset_reserve_msg(msg)
            return

        cris_emoji = get_cris_emoji(bot)

        # little checker to see if cris is busy doing things
        # if cris is busy wait a bit then check again
        # wait a max of 30 seconds until giving up
        count = 0
        while True:
            if cris_emoji not in [r.emoji for r in msg.reactions]:
                break

            await asyncio.sleep(3)
            msg = await fetch_message(payload, bot, channel)

            if count > 10:
                if reaction_added:
                    await msg.remove_reaction(payload.emoji, member)
                return

        # start work
        await msg.add_reaction(cris_emoji)

        if is_wave_emoji:
            await handle_reserve_needed_reaction(
                payload=payload,
                bot=bot,
                msg=msg,
                driver_member=member,
                reaction_added=reaction_added,
            )

        elif is_div_emoji:
            await handle_reserve_available_reaction(
                payload=payload,
                bot=bot,
                msg=msg,
                reserve_member=member,
                reaction_added=reaction_added,
            )

        elif is_counterclockwise_arrow_emoji and member_is_admin:
            await update_reserve_embed(msg=msg, database=bot.tepcott_database)
            await msg.remove_reaction(payload.emoji, member)

        # end work
        await msg.remove_reaction(cris_emoji, bot.user)
