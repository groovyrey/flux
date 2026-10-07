from __future__ import annotations

import base64

import discord
from discord import app_commands
from discord.ext import commands

from storage.db import set_user_key


class Keys(commands.Cog):
    """Key management for encryption."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setupkey", description="Set your encryption key (DMs only)")
    @app_commands.describe(key="The encryption key to use")
    async def setupkey(self, interaction: discord.Interaction, key: str) -> None:
        if interaction.guild is not None:
            await interaction.response.send_message(
                "Use `/setupkey` in DMs only.", ephemeral=True
            )
            return

        key = key.strip()
        if not key:
            await interaction.response.send_message("Key cannot be empty.", ephemeral=True)
            return

        await set_user_key(interaction.user.id, key)
        await interaction.response.send_message("Your key has been saved.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Keys(bot))
