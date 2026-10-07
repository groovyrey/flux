from __future__ import annotations

import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "flux.db"


async def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_keys (
                user_id INTEGER PRIMARY KEY,
                key TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def set_user_key(user_id: int, key: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_keys (user_id, key, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (user_id, key),
        )
        await db.commit()


async def get_user_key(user_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT key FROM user_keys WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return row["key"] if row else None
