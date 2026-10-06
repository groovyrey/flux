from __future__ import annotations

import logging

import discord
from discord.ext import commands

log = logging.getLogger("flux.events")


class Listeners(commands.Cog):
    """Bot lifecycle events."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        user = self.bot.user
        assert user is not None
        log.info("Signed in as %s (%s) | %d guild(s)", user, user.id, len(self.bot.guilds))

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        log.info("Joined guild %s (%s) with %d member(s)", guild.name, guild.id, guild.member_count)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        log.info("Left guild %s (%s)", guild.name, guild.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Listeners(bot))
