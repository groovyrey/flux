from __future__ import annotations

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import discord
from discord import app_commands
from discord.ext import commands

SALT = b"flux_encryption_salt_v1"


def _derive_fernet_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=390000,
    )
    derived = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(derived)


def _strip_code_fence(content: str) -> str:
    content = content.strip()
    if content.startswith("```") and content.endswith("```"):
        inner = content[3:-3].strip()
        lines = inner.splitlines()
        return lines[0] if len(lines) == 1 else inner
    return content


def _encrypt(text: str, key: str) -> str:
    fernet = Fernet(_derive_fernet_key(key))
    return fernet.encrypt(text.encode("utf-8")).decode("utf-8")


def _decrypt(content: str, key: str) -> str:
    fernet = Fernet(_derive_fernet_key(key))
    return fernet.decrypt(content.encode("utf-8")).decode("utf-8")


class _DecryptModal(discord.ui.Modal):
    def __init__(self, content: str) -> None:
        super().__init__(title="Decrypt message")
        self.content = content
        self.key = discord.ui.TextInput(label="Key", max_length=2000, required=True)
        self.add_item(self.key)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            decrypted = _decrypt(self.content, self.key.value.strip())
        except (InvalidToken, ValueError, TypeError):
            await interaction.response.send_message(
                "Cannot decrypt. Check that the message and key are correct.",
                ephemeral=True,
            )
            return
        except Exception:
            await interaction.response.send_message(
                "Failed to decrypt that message.", ephemeral=True
            )
            return

        await interaction.response.send_message(decrypted, ephemeral=True)


class Crypto(commands.Cog):
    """Encrypt and decrypt messages with a shared key. Nothing is stored."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="encrypt", description="Encrypt a message with a key")
    @app_commands.describe(
        message="The message to encrypt",
        key="The shared key others need to decrypt it",
    )
    async def encrypt(
        self, interaction: discord.Interaction, message: str, key: str
    ) -> None:
        text = message.strip()
        secret = key.strip()
        if not text:
            await interaction.response.send_message(
                "The message cannot be empty.", ephemeral=True
            )
            return
        if not secret:
            await interaction.response.send_message(
                "The key cannot be empty.", ephemeral=True
            )
            return

        try:
            encrypted = _encrypt(text, secret)
        except Exception:
            await interaction.response.send_message(
                "Failed to encrypt that message.", ephemeral=True
            )
            return

        await interaction.response.send_message(encrypted)

    @app_commands.command(name="decrypt", description="Decrypt an encrypted message with a key")
    @app_commands.describe(
        message="The encrypted text",
        key="The shared key used to encrypt it",
    )
    async def decrypt(
        self, interaction: discord.Interaction, message: str, key: str
    ) -> None:
        content = _strip_code_fence(message)
        secret = key.strip()
        if not content:
            await interaction.response.send_message(
                "There is no text to decrypt.", ephemeral=True
            )
            return
        if not secret:
            await interaction.response.send_message(
                "The key cannot be empty.", ephemeral=True
            )
            return

        try:
            decrypted = _decrypt(content, secret)
        except (InvalidToken, ValueError, TypeError):
            await interaction.response.send_message(
                "Cannot decrypt. Check that the message and key are correct.",
                ephemeral=True,
            )
            return
        except Exception:
            await interaction.response.send_message(
                "Failed to decrypt that message.", ephemeral=True
            )
            return

        await interaction.response.send_message(decrypted, ephemeral=True)


async def decrypt_message(
    interaction: discord.Interaction, message: discord.Message
) -> None:
    content = _strip_code_fence(message.content)
    if not content:
        await interaction.response.send_message(
            "That message has no text to decrypt.", ephemeral=True
        )
        return

    await interaction.response.send_modal(_DecryptModal(content))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Crypto(bot))
    bot.tree.add_command(
        app_commands.ContextMenu(name="Decrypt Message", callback=decrypt_message)
    )
