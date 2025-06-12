import asyncio
import logging
import re
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.markdown import hbold
from os import getenv
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv("BOT_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# === БАЗА ДАННЫХ ===
conn = sqlite3.connect("aura.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS aura (
    username TEXT PRIMARY KEY,
    value INTEGER DEFAULT 0
)
""")
conn.commit()

# === ХЕЛПЕРЫ ===
def change_aura(username: str, delta: int) -> int:
    cursor.execute("SELECT value FROM aura WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row:
        new_value = row[0] + delta
        cursor.execute("UPDATE aura SET value = ? WHERE username = ?", (new_value, username))
    else:
        new_value = delta
        cursor.execute("INSERT INTO aura (username, value) VALUES (?, ?)", (username, new_value))
    conn.commit()
    return new_value

# === ОБРАБОТКА ++ и -- ===
@dp.message()
async def aura_handler(message: Message):
    pattern = r'@(\w+)\s*(\+\+|--)'
    match = re.search(pattern, message.text)

    if not match:
        return

    target_username, operation = match.groups()

    if not target_username:
        await message.reply("Укажите Telegram username через @")
        return

    if message.from_user.username == target_username:
        await message.reply("Ты не можешь менять свою собственную ауру 😅")
        return

    delta = 1 if operation == "++" else -1
    new_value = change_aura(target_username, delta)

    sign = "🔺" if delta > 0 else "🔻"
    await message.reply(f"{sign} {hbold('@' + target_username)} теперь имеет ауру: {new_value}")

# === СТАРТ ===
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
