from __future__ import annotations

import discord
from discord import app_commands
from discord.app_commands import checks
from discord.ext import commands


class Moderation(commands.Cog):
    """Moderation tools: kick, ban, unban, purge."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="Member to kick", reason="Reason for the audit log")
    @checks.has_permissions(kick_members=True)
    @checks.bot_has_permissions(kick_members=True)
    async def kick(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        await member.kick(reason=reason)
        await interaction.response.send_message(
            f"Kicked **{member}**{f': {reason}' if reason else ''}"
        )

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="Member to ban", reason="Reason for the audit log")
    @checks.has_permissions(ban_members=True)
    @checks.bot_has_permissions(ban_members=True)
    async def ban(
        self, interaction: discord.Interaction, member: discord.Member, reason: str | None = None
    ) -> None:
        await member.ban(reason=reason)
        await interaction.response.send_message(
            f"Banned **{member}**{f': {reason}' if reason else ''}"
        )

    @app_commands.command(name="unban", description="Unban a user by ID or name")
    @app_commands.describe(user="User to unban", reason="Reason for the audit log")
    @checks.has_permissions(ban_members=True)
    @checks.bot_has_permissions(ban_members=True)
    async def unban(
        self, interaction: discord.Interaction, user: discord.User, reason: str | None = None
    ) -> None:
        guild = interaction.guild
        assert guild is not None
        await guild.unban(user, reason=reason)
        await interaction.response.send_message(f"Unbanned **{user}**")

    @app_commands.command(name="purge", description="Delete recent messages")
    @app_commands.describe(count="How many messages to delete (1-100)")
    @checks.has_permissions(manage_messages=True)
    @checks.bot_has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, count: app_commands.Range[int, 1, 100]) -> None:
        channel = interaction.channel
        if channel is None or not isinstance(channel, discord.abc.Messageable):
            await interaction.response.send_message("I cannot delete messages here.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await channel.purge(limit=count)
        await interaction.followup.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
