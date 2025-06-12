import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
import sqlite3
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 957041356  # <--- замени на свой ID

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Подключение к БД
conn = sqlite3.connect("aura.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        aura INTEGER DEFAULT 0
    )
""")
conn.commit()

def change_aura(user_id, username, delta):
    cursor.execute("SELECT aura FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        cursor.execute("UPDATE users SET aura = aura + ?, username = ? WHERE user_id = ?", (delta, username, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, username, aura) VALUES (?, ?, ?)", (user_id, username, delta))
    conn.commit()

@dp.message()
async def handle_aura_messages(message: Message):
    if not message.reply_to_message:
        return

    text = message.text.strip()
    if text == "++":
        target = message.reply_to_message.from_user
        change_aura(target.id, target.username or target.full_name, 1)
        await message.reply(f"👍 +1 к ауре для {target.full_name}")
    elif text == "--":
        target = message.reply_to_message.from_user
        change_aura(target.id, target.username or target.full_name, -1)
        await message.reply(f"👎 -1 от ауры для {target.full_name}")

@dp.message(Command("top"))
async def top_users(message: Message):
    cursor.execute("SELECT username, aura FROM users ORDER BY aura DESC LIMIT 10")
    rows = cursor.fetchall()
    if not rows:
        await message.reply("Пока нет данных.")
        return
    text = "<b>🏆 Топ по ауре:</b>\n\n"
    for i, (username, aura) in enumerate(rows, start=1):
        name = f"@{username}" if username else "Без имени"
        text += f"{i}. {name} — {aura}\n"
    await message.reply(text)

@dp.message(Command("set_aura"))
async def set_aura(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("У тебя нет прав на выполнение этой команды.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError
        username = parts[1].lstrip('@')
        new_value = int(parts[2])
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            cursor.execute("UPDATE users SET aura = ? WHERE username = ?", (new_value, username))
            conn.commit()
            await message.reply(f"✅ Аура пользователя @{username} установлена на {new_value}.")
        else:
            await message.reply("Пользователь не найден.")
    except:
        await message.reply("Используй формат: /set_aura @username 10")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
