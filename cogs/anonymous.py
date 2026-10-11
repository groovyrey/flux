from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from storage.anon import Conversation, create_conversation, get_conversation

REPLY_PREFIX = "anon:reply:"
MODAL_PREFIX = "anon:modal:"


def _anon_embed(text: str) -> discord.Embed:
    embed = discord.Embed(description=text, color=discord.Color.blurple())
    embed.set_footer(text="Sent anonymously via Flux")
    return embed


async def _deliver(
    user: discord.abc.User, conversation: Conversation, text: str
) -> str | None:
    try:
        await user.send(embed=_anon_embed(text), view=_reply_view(conversation.id))
    except discord.Forbidden:
        return "Could not deliver the message. They may have DMs closed or haven't added the app."
    except discord.HTTPException:
        return "Something went wrong delivering the message."
    return None


class _ReplyModal(discord.ui.Modal):
    def __init__(self, conversation_id: int) -> None:
        super().__init__(
            title="Anonymous reply", custom_id=f"{MODAL_PREFIX}{conversation_id}"
        )
        self.conversation_id = conversation_id
        self.message = discord.ui.TextInput(
            label="Your reply",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=True,
        )
        self.add_item(self.message)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        conversation = get_conversation(self.conversation_id)
        if conversation is None:
            await interaction.response.send_message(
                "This conversation is no longer available.", ephemeral=True
            )
            return

        recipient_id = conversation.other(interaction.user.id)
        if recipient_id is None:
            await interaction.response.send_message(
                "You are not part of this conversation.", ephemeral=True
            )
            return

        try:
            recipient = await interaction.client.fetch_user(recipient_id)
        except discord.HTTPException:
            await interaction.response.send_message(
                "Could not reach that user.", ephemeral=True
            )
            return

        error = await _deliver(recipient, conversation, self.message.value)
        if error is not None:
            await interaction.response.send_message(
                error.replace("message", "reply"), ephemeral=True
            )
            return

        await interaction.response.send_message("Sent anonymously.", ephemeral=True)


class _ReplyButton(discord.ui.Button):
    def __init__(self, conversation_id: int) -> None:
        super().__init__(
            label="Reply",
            style=discord.ButtonStyle.primary,
            custom_id=f"{REPLY_PREFIX}{conversation_id}",
        )
        self.conversation_id = conversation_id

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(_ReplyModal(self.conversation_id))


def _reply_view(conversation_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    view.add_item(_ReplyButton(conversation_id))
    return view


class Anonymous(commands.Cog):
    """Send and receive anonymous DMs between members."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="anon", description="Send an anonymous DM to a user")
    @app_commands.describe(
        user="Who receives the anonymous message",
        message="The message to send",
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def anon(
        self,
        interaction: discord.Interaction,
        user: discord.User,
        message: app_commands.Range[str, 1, 2000],
    ) -> None:
        if user.bot:
            await interaction.response.send_message(
                "You cannot message a bot.", ephemeral=True
            )
            return
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "You cannot message yourself.", ephemeral=True
            )
            return

        text = message.strip()
        if not text:
            await interaction.response.send_message(
                "The message cannot be empty.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        conversation = create_conversation(interaction.user.id, user.id)
        error = await _deliver(user, conversation, text)
        if error is not None:
            await interaction.followup.send(error, ephemeral=True)
            return

        await interaction.followup.send("Delivered anonymously.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Anonymous(bot))
