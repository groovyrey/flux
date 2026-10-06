from __future__ import annotations

import platform

import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    """Everyday commands: ping, about, server."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.started_at = discord.utils.utcnow()

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! `{latency} ms`")

    @app_commands.command(name="about", description="Show info about the bot")
    async def about(self, interaction: discord.Interaction) -> None:
        user = self.bot.user
        assert user is not None
        uptime = discord.utils.format_dt(self.started_at, style="R")

        embed = discord.Embed(title=user.name, color=discord.Color.blurple())
        if user.display_avatar:
            embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.add_field(name="Started", value=uptime, inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.set_footer(text=f"ID: {user.id}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="server", description="Show info about this server")
    @app_commands.guild_only()
    async def server(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        assert guild is not None

        embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>", inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, style="D"), inline=True)
        embed.set_footer(text=f"ID: {guild.id}")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
