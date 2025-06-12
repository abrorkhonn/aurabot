import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Загрузка токена
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Создание таблицы, если нет
def init_db():
    conn = sqlite3.connect("aura.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            aura INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# Получить ауру
def get_aura(user_id: int) -> int:
    conn = sqlite3.connect("aura.db")
    cur = conn.cursor()
    cur.execute("SELECT aura FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0

# Изменить ауру
def change_aura(user_id: int, amount: int):
    conn = sqlite3.connect("aura.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cur.execute("UPDATE users SET aura = aura + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

# Кнопки "Добавить/Убавить"
def get_keyboard(user_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add Aura", callback_data=f"add:{user_id}")
    kb.button(text="➖ Remove Aura", callback_data=f"remove:{user_id}")
    kb.adjust(2)
    return kb

# Команда /start
@dp.message(F.text == "/start")
async def start_handler(message: Message):
    aura = get_aura(message.from_user.id)
    await message.answer(
        f"👋 Hello, {message.from_user.full_name}!\nYour aura: <b>{aura}</b>",
        reply_markup=get_keyboard(message.from_user.id).as_markup()
    )

# Обработка кнопок
@dp.callback_query(F.data.startswith("add:"))
async def add_aura(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    change_aura(target_id, +1)
    aura = get_aura(target_id)
    await callback.message.edit_text(
        f"🌟 Aura increased!\nCurrent aura: <b>{aura}</b>",
        reply_markup=get_keyboard(target_id).as_markup()
    )
    await callback.answer("Added aura!")

@dp.callback_query(F.data.startswith("remove:"))
async def remove_aura(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    change_aura(target_id, -1)
    aura = get_aura(target_id)
    await callback.message.edit_text(
        f"🌑 Aura decreased!\nCurrent aura: <b>{aura}</b>",
        reply_markup=get_keyboard(target_id).as_markup()
    )
    await callback.answer("Removed aura!")

# Основной запуск
async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot is polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
