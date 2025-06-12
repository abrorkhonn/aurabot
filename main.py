import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor

# Загружаем переменные из .env
load_dotenv()

# Получаем токен бота из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Проверка: если токен не найден, выводим ошибку
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле!")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Обработка команды /start
@dp.message_handler(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Я бот, и я работаю 🎉")

# Запуск бота
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
