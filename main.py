from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Command
from aiogram.types import Message
from aiogram.utils import executor
import sqlite3
import logging
import os

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создание БД
conn = sqlite3.connect("aura.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS aura (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        aura INTEGER DEFAULT 0
    )
""")
conn.commit()

# --- Хелперы ---
def change_aura(user_id: int, username: str, delta: int):
    cursor.execute("SELECT aura FROM aura WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE aura SET aura = aura + ?, username = ? WHERE user_id = ?", (delta, username, user_id))
    else:
        cursor.execute("INSERT INTO aura (user_id, username, aura) VALUES (?, ?, ?)", (user_id, username, delta))
    conn.commit()

def get_aura(user_id: int) -> int:
    cursor.execute("SELECT aura FROM aura WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0

# --- Команды ---
@dp.message(Command("give"))
async def handle_give(msg: Message):
    if not msg.reply_to_message:
        await msg.reply("Эта команда работает только в ответ на сообщение.")
        return
    target = msg.reply_to_message.from_user
    change_aura(target.id, target.username or target.full_name, +1)
    await msg.reply(f"✨ Аура +1 для {target.full_name}!")

@dp.message(Command("take"))
async def handle_take(msg: Message):
    if not msg.reply_to_message:
        await msg.reply("Эта команда работает только в ответ на сообщение.")
        return
    target = msg.reply_to_message.from_user
    change_aura(target.id, target.username or target.full_name, -1)
    await msg.reply(f"⚠️ Аура -1 у {target.full_name}!")

@dp.message(Command("aura"))
async def handle_aura(msg: Message):
    aura = get_aura(msg.from_user.id)
    await msg.reply(f"🔮 Ваша аура: {aura}")

# --- Старт ---
@dp.message(Command("start"))
async def start_handler(msg: Message):
    await msg.reply("Бот запущен. Используйте /give, /take и /aura!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
