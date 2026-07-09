import aiosqlite
from datetime import datetime
from typing import Optional

DB_PATH = "reminders.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                voice_file_id TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                is_sent INTEGER NOT NULL DEFAULT 0,
                content_type TEXT NOT NULL DEFAULT 'voice'
            )
            """
        )
        # Migratsiya: eski jadvalda content_type ustuni bo'lmasa qo'shamiz
        async with db.execute("PRAGMA table_info(reminders)") as cursor:
            columns = [row[1] async for row in cursor]
        if "content_type" not in columns:
            await db.execute(
                "ALTER TABLE reminders ADD COLUMN content_type TEXT NOT NULL DEFAULT 'voice'"
            )
        await db.commit()


async def add_reminder(
    user_id: int, content: str, reminder_time: datetime, content_type: str = "voice"
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO reminders (user_id, voice_file_id, reminder_time, is_sent, content_type) VALUES (?, ?, ?, 0, ?)",
            (user_id, content, reminder_time.isoformat(), content_type),
        )
        await db.commit()
        return cursor.lastrowid


async def mark_sent(reminder_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
        await db.commit()


async def get_reminder(reminder_id: int) -> Optional[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, user_id, voice_file_id, reminder_time, is_sent, content_type FROM reminders WHERE id = ?",
            (reminder_id,),
        ) as cursor:
            return await cursor.fetchone()


async def get_pending_reminders() -> list[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, user_id, voice_file_id, reminder_time, content_type FROM reminders WHERE is_sent = 0"
        ) as cursor:
            return await cursor.fetchall()
