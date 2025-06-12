import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from datetime import datetime, timedelta
import re
import sqlite3
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 957041356  # замените на ваш Telegram ID

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

conn = sqlite3.connect("aura.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS aura (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    aura INTEGER DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    value INTEGER,
    timestamp TEXT
)
""")
conn.commit()

def get_user_aura(user_id):
    cursor.execute("SELECT aura FROM aura WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_user_aura(user_id, username, value):
    cursor.execute("INSERT OR IGNORE INTO aura (user_id, username, aura) VALUES (?, ?, ?)", (user_id, username, 0))
    cursor.execute("UPDATE aura SET aura = aura + ?, username = ? WHERE user_id = ?", (value, username, user_id))
    conn.commit()

def save_history(sender_id, receiver_id, value):
    cursor.execute("INSERT INTO history (sender_id, receiver_id, value, timestamp) VALUES (?, ?, ?, ?)",
                   (sender_id, receiver_id, value, datetime.utcnow().isoformat()))
    conn.commit()

def daily_limits(sender_id, receiver_id, value):
    today = datetime.utcnow().date()
    cursor.execute("""
    SELECT SUM(value) FROM history 
    WHERE sender_id = ? AND DATE(timestamp) = ?
    """, (sender_id, today))
    total = cursor.fetchone()[0] or 0

    cursor.execute("""
    SELECT SUM(value) FROM history 
    WHERE sender_id = ? AND receiver_id = ? AND DATE(timestamp) = ?
    """, (sender_id, receiver_id, today))
    to_one = cursor.fetchone()[0] or 0

    total_limit = abs(total + value) <= 500
    one_limit = abs(to_one + value) <= 200
    return total_limit, one_limit

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Привет! Используй `@username +100` или `-100` чтобы изменить ауру другим.\n\nПосмотреть ауру: /aura @username\nТоп: /top")

@dp.message(Command("aura"))
async def get_aura(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Используй /aura @username")
        return
    username = args[1].lstrip("@")
    cursor.execute("SELECT aura FROM aura WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        await message.answer(f"✨ Аура @{username}: {result[0]}")
    else:
        await message.answer("Пользователь не найден.")

@dp.message(Command("top"))
async def top(message: Message):
    cursor.execute("SELECT username, aura FROM aura ORDER BY aura DESC LIMIT 10")
    rows = cursor.fetchall()
    text = "<b>🏆 Топ по ауре:</b>\n\n"
    for i, (username, aura) in enumerate(rows, 1):
        text += f"{i}. @{username} — {aura}\n"
    await message.answer(text)

@dp.message(Command("setaura"))
async def set_aura(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет прав для этой команды.")
        return
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Используй: /setaura @username число")
        return
    username = args[1].lstrip("@")
    try:
        value = int(args[2])
    except:
        await message.answer("Значение должно быть числом.")
        return
    cursor.execute("SELECT user_id FROM aura WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        user_id = result[0]
        cursor.execute("UPDATE aura SET aura = ? WHERE user_id = ?", (value, user_id))
        conn.commit()
        await message.answer(f"✅ Аура @{username} установлена на {value}.")
    else:
        await message.answer("Пользователь не найден.")

@dp.message()
async def handle_aura_change(message: Message):
    if not message.entities:
        return
    mentioned = [e for e in message.entities if e.type == "mention"]
    if not mentioned:
        return
    match = re.search(r'([+-]\d+)', message.text)
    if not match:
        return
    value = int(match.group(1))
    if value == 0:
        return
    username = message.text[mentioned[0].offset+1:mentioned[0].offset+mentioned[0].length]
    cursor.execute("SELECT user_id FROM aura WHERE username = ?", (username,))
    user = cursor.fetchone()

    if username == message.from_user.username:
        await message.reply("❌ Нельзя менять свою ауру.")
        return

    if not user:
        # создаём если ещё нет
        cursor.execute("INSERT INTO aura (username, aura, user_id) VALUES (?, 0, ?)", (username, 999999999))
        conn.commit()
        cursor.execute("SELECT user_id FROM aura WHERE username = ?", (username,))
        user = cursor.fetchone()

    receiver_id = user[0]
    sender_id = message.from_user.id

    ok1, ok2 = daily_limits(sender_id, receiver_id, value)
    if not ok1:
        await message.reply("❌ Превышен дневной лимит +500 / -500.")
        return
    if not ok2:
        await message.reply("❌ Нельзя дать больше +200 или -200 одному человеку в день.")
        return

    update_user_aura(receiver_id, username, value)
    save_history(sender_id, receiver_id, value)
    await message.reply(f"{'✨' if value > 0 else '💢'} @{username} {'получает' if value > 0 else 'теряет'} {abs(value)} ауры!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
