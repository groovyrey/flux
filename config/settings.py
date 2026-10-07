from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class MissingTokenError(RuntimeError):
    """Raised when DISCORD_TOKEN is not set."""


class MissingEncryptionKeyError(RuntimeError):
    """Raised when ENCRYPTION_KEY is not set."""


@dataclass(frozen=True, slots=True)
class Settings:
    token: str
    test_guild_id: int | None
    encryption_key: bytes

    @classmethod
    def load(cls) -> Settings:
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token or token.startswith("put-"):
            raise MissingTokenError("DISCORD_TOKEN is missing or still a placeholder. Edit .env")

        raw_guild = os.getenv("TEST_GUILD_ID", "").strip()
        test_guild_id = int(raw_guild) if raw_guild.isdigit() else None

        enc_key = os.getenv("ENCRYPTION_KEY", "").strip()
        if not enc_key:
            raise MissingEncryptionKeyError("ENCRYPTION_KEY is missing. Generate one with Fernet.generate_key()")
        encryption_key = enc_key.encode()

        return cls(token=token, test_guild_id=test_guild_id, encryption_key=encryption_key)
