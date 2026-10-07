from __future__ import annotations

import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import discord
from discord import app_commands
from discord.ext import commands

from storage.db import get_user_key

SALT = b"flux_encryption_salt_v1"


def _derive_fernet_key(password: str) -> bytes:
    password_bytes = password.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=390000,
    )
    derived = kdf.derive(password_bytes)
    return base64.urlsafe_b64encode(derived)


class Crypto(commands.Cog):
    """Encrypt/decrypt messages privately using per-user keys."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="encrypt", description="Encrypt a message privately")
    @app_commands.describe(message="The message to encrypt")
    async def encrypt(self, interaction: discord.Interaction, message: str) -> None:
        user_key = await get_user_key(interaction.user.id)
        if user_key is None:
            await interaction.response.send_message(
                "You haven't set a key yet. DM me `/setupkey <your-key>` first.",
                ephemeral=True,
            )
            return

        try:
            fernet = Fernet(_derive_fernet_key(user_key))
            encrypted = fernet.encrypt(message.encode("utf-8")).decode("utf-8")
        except (ValueError, TypeError, InvalidToken):
            await interaction.response.send_message(
                "Your saved key is invalid. DM me `/setupkey <new-key>` to fix it.",
                ephemeral=True,
            )
            return
        except Exception:
            await interaction.response.send_message(
                "Failed to encrypt that message.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Here is your encrypted text:\n```{encrypted}```\nCopy and share it. Only people with the same key can decrypt it.",
            ephemeral=True,
        )


async def decrypt_message(
    interaction: discord.Interaction, message: discord.Message
) -> None:
    content = message.content.strip()
    if not content:
        await interaction.response.send_message(
            "That message has no text to decrypt.", ephemeral=True
        )
        return

    if content.startswith("```") and content.endswith("```"):
        inner = content[3:-3].strip()
        lines = inner.splitlines()
        if len(lines) == 1:
            content = lines[0]
        else:
            content = inner

    user_key = await get_user_key(interaction.user.id)
    if user_key is None:
        await interaction.response.send_message(
            "You haven't set a key yet. DM me `/setupkey <your-key>` first.",
            ephemeral=True,
        )
        return

    try:
        fernet = Fernet(_derive_fernet_key(user_key))
        decrypted = fernet.decrypt(content.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        await interaction.response.send_message(
            "Cannot decrypt. Either this isn't encrypted text or you and the sender have different keys.",
            ephemeral=True,
        )
        return
    except Exception:
        await interaction.response.send_message(
            "Failed to decrypt that message.", ephemeral=True
        )
        return

    await interaction.response.send_message(f"Decrypted:\n{decrypted}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Crypto(bot))
    bot.tree.add_command(
        app_commands.ContextMenu(name="Decrypt Message", callback=decrypt_message)
    )
