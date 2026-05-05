from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from aiogram import Bot

from db import get_reminder, get_pending_reminders, mark_sent

scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")


async def send_reminder(bot: Bot, reminder_id: int) -> None:
    row = await get_reminder(reminder_id)
    if not row:
        return
    _id, user_id, voice_file_id, _time, is_sent = row
    if is_sent:
        return
    try:
        await bot.send_voice(
            chat_id=user_id,
            voice=voice_file_id,
            caption="Vaqti keldi! Mana siz qoldirgan eslatma:",
        )
    finally:
        await mark_sent(reminder_id)


def schedule_reminder(bot: Bot, reminder_id: int, run_at: datetime) -> None:
    if run_at <= datetime.now():
        run_at = datetime.now()
    scheduler.add_job(
        send_reminder,
        trigger=DateTrigger(run_date=run_at),
        args=[bot, reminder_id],
        id=f"reminder_{reminder_id}",
        replace_existing=True,
    )


async def restore_jobs(bot: Bot) -> None:
    pending = await get_pending_reminders()
    for reminder_id, _user_id, _voice, time_str in pending:
        run_at = datetime.fromisoformat(time_str)
        schedule_reminder(bot, reminder_id, run_at)


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
