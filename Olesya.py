import logging
import sqlite3
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import BadRequest
from dotenv import load_dotenv


load_dotenv()

# Ваши данные

API_TOKEN = os.getenv("API_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# Логгирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Подключение к базе данных
conn = sqlite3.connect("subscriptions.db")
cursor = conn.cursor()

# Создание таблицы, если она не существует
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    subscription_status TEXT,
    first_checked TIMESTAMP
)
""")
conn.commit()

# Кнопка "🚀 Старт"
start_button = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🚀 Старт", callback_data="start_check_subscription")
)

# Кнопка подписки и проверки подписки
subscribe_and_check_button = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
    InlineKeyboardButton("🔄 Я подписался!", callback_data="check_subscription")
)

# Функция для сохранения информации о пользователе в базу данных
def save_user_to_db(user_id, username, first_name, last_name, status):
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, subscription_status, first_checked)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, first_name, last_name, status, datetime.now()))
    conn.commit()

# Обработка команды /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    # Удаляем старое сообщение
    await message.delete()

    # Сохраняем информацию о пользователе в базу данных
    save_user_to_db(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        status="started"
    )

    # Отправляем только кнопку "Старт"
    await message.answer(
        "👋 Привет! Нажми «🚀 Старт», чтобы получить подарок 🎁",
        reply_markup=start_button
    )

# Обработка нажатия кнопки "Старт"
@dp.callback_query_handler(text="start_check_subscription")
async def start_check_subscription(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "Чтобы получить подарок, подпишись на канал и нажми кнопку «🔄 Я подписался!».",
        reply_markup=subscribe_and_check_button
    )

# Обработка нажатия кнопки "Проверить подписку"
@dp.callback_query_handler(text="check_subscription")
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    try:
        # Проверяем статус подписки
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)

        if chat_member.status in ['member', 'administrator', 'owner']:
            # Если пользователь подписан
            save_user_to_db(
                user_id=user_id,
                username=callback_query.from_user.username,
                first_name=callback_query.from_user.first_name,
                last_name=callback_query.from_user.last_name,
                status="subscribed"
            )

            await callback_query.message.edit_text(
                "Спасибо за подписку! 🎉\n\nВот твой подарок:\nhttps://youtu.be/tR_bGpJTkTw?si=W2jexfGgviuYcepk"
            )
        else:
            # Если не подписан
            save_user_to_db(
                user_id=user_id,
                username=callback_query.from_user.username,
                first_name=callback_query.from_user.first_name,
                last_name=callback_query.from_user.last_name,
                status="not_subscribed"
            )

            await callback_query.message.edit_text(
                "Вы еще не подписались на канал! Подпишитесь и нажмите кнопку ниже.",
                reply_markup=subscribe_and_check_button
            )
    except BadRequest:
        await callback_query.message.answer(
            "Ошибка доступа к списку участников канала.\n"
            "Проверьте, что бот добавлен в администраторы канала."
        )

# Запуск бота
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
