from aiogram import Router
from aiogram.types import Message
from datetime import datetime

router = Router()

@router.message(lambda m: m.text and m.text.lower() == "hi")
async def hello_handler(message: Message):
    await message.answer("Hello World!")

@router.message(lambda m: m.text and m.text.lower() == "time")
async def time_handler(message: Message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await message.answer(f"⏰ Current time: {now}")
