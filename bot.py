from __future__ import annotations

import importlib
import logging
import pkgutil

import discord
from discord import app_commands
from discord.ext import commands

from config import Settings

log = logging.getLogger("flux")

PACKAGES = ("cogs", "events")


class FluxBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents, help_command=None)
        self.settings = settings

    async def setup_hook(self) -> None:
        from storage.db import init_db

        for package in PACKAGES:
            module = importlib.import_module(package)
            for info in pkgutil.iter_modules(module.__path__):
                if info.name.startswith("_"):
                    continue
                await self.load_extension(f"{package}.{info.name}")

        await init_db()

        self.tree.on_error = self._on_app_command_error

        if self.settings.test_guild_id is not None:
            self.tree.copy_global_to(guild=discord.Object(id=self.settings.test_guild_id))

        synced = await self.tree.sync()
        log.info("Synced %d application command(s)", len(synced))

    async def _on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        command = getattr(interaction.command, "name", "unknown")
        original = getattr(error, "original", error)
        log.error("Command %r failed", command, exc_info=original)

        if interaction.response.is_done():
            send = interaction.followup.send
        else:
            send = interaction.response.send_message

        await send(_friendly(error), ephemeral=True)


def _friendly(error: app_commands.AppCommandError) -> str:
    if isinstance(error, app_commands.BotMissingPermissions):
        return "I do not have the permissions needed for that."
    if isinstance(error, app_commands.MissingPermissions):
        return "You do not have permission to use this command."
    if isinstance(error, app_commands.MissingRole | app_commands.MissingAnyRole):
        return "You do not have the required role for that."
    if isinstance(error, app_commands.NoPrivateMessage):
        return "That command cannot be used in DMs."
    if isinstance(error, app_commands.CommandOnCooldown):
        return f"Slow down, try again in {error.retry_after:.1f}s."
    if isinstance(error, app_commands.CheckFailure):
        return "You cannot use that command here."
    return "Something went wrong running that command."


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    settings = Settings.load()
    FluxBot(settings).run(settings.token, log_handler=None)


if __name__ == "__main__":
    main()
