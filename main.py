import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor
from db import init_db, change_aura, get_aura

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

init_db()

@dp.message_handler(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот, и я работаю 🎉")

@dp.message_handler(lambda m: m.text.startswith("+аура") or m.text.startswith("-аура"))
async def aura_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2 or not message.entities:
        await message.reply("Укажи пользователя: +аура @username или -аура @username")
        return

    target = message.entities[1]
    if target.type != "mention":
        await message.reply("Нужен @username")
        return

    username = message.text[target.offset+1:target.offset+target.length]
    # Ищем ID по username (на основе реплая или сохранённых ранее данных)
    if not message.reply_to_message:
        await message.reply("Пока поддерживается только через ответ на сообщение")
        return

    user = message.reply_to_message.from_user
    delta = 1 if message.text.startswith("+аура") else -1
    change_aura(user.id, user.username or username, delta)
    current = get_aura(user.id)

    await message.reply(f"✨ Аура пользователя @{user.username or username}: {current}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
