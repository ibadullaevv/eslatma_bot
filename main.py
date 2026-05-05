import asyncio
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

from db import init_db, add_reminder
from scheduler import schedule_reminder, restore_jobs, start_scheduler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida topilmadi")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DATE_FORMAT = "%d.%m.%Y %H:%M"


class ReminderStates(StatesGroup):
    waiting_for_time = State()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Assalomu alaykum! Menga ovozli xabar yuboring, men uni belgilangan vaqtda esingizga solaman."
    )


@dp.message(F.voice)
async def handle_voice(message: Message, state: FSMContext) -> None:
    await state.update_data(voice_file_id=message.voice.file_id)
    await state.set_state(ReminderStates.waiting_for_time)
    await message.answer(
        "Ovozli xabar qabul qilindi. Qachon eslatishim kerak? "
        "(Format: DD.MM.YYYY HH:mm, masalan: 05.05.2026 15:30)"
    )


@dp.message(ReminderStates.waiting_for_time, F.text)
async def handle_time(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    try:
        reminder_time = datetime.strptime(text, DATE_FORMAT)
    except ValueError:
        await message.answer(
            "Sana formati noto'g'ri. Iltimos, namunadagidek yozing: 05.05.2026 15:30"
        )
        return

    if reminder_time <= datetime.now():
        await message.answer(
            "Sana formati noto'g'ri. Iltimos, namunadagidek yozing: 05.05.2026 15:30"
        )
        return

    data = await state.get_data()
    voice_file_id = data.get("voice_file_id")
    if not voice_file_id:
        await state.clear()
        await message.answer(
            "Avval ovozli xabar yuboring."
        )
        return

    reminder_id = await add_reminder(message.from_user.id, voice_file_id, reminder_time)
    schedule_reminder(bot, reminder_id, reminder_time)
    await state.clear()
    await message.answer(
        f"Tushunarlu! {reminder_time.strftime(DATE_FORMAT)} vaqtida sizga ushbu xabarni yuboraman."
    )


@dp.message(ReminderStates.waiting_for_time)
async def handle_time_wrong_type(message: Message) -> None:
    await message.answer(
        "Sana formati noto'g'ri. Iltimos, namunadagidek yozing: 05.05.2026 15:30"
    )


@dp.message(F.text)
async def handle_other_text(message: Message) -> None:
    await message.answer(
        "Menga ovozli xabar yuboring, men uni belgilangan vaqtda esingizga solaman."
    )


async def main() -> None:
    await init_db()
    start_scheduler()
    await restore_jobs(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
