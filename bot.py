import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect("finance.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT CHECK(type IN ('доход', 'расход')),
        category TEXT,
        amount REAL CHECK(amount >= 0),
        date TEXT DEFAULT CURRENT_DATE
    )
""")
conn.commit()

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("Добавить доход"))
keyboard.add(KeyboardButton("Добавить расход"))
keyboard.add(KeyboardButton("Показать баланс"))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Я бот для учета финансов. Выберите действие:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Добавить доход")
async def add_income(message: types.Message):
    await message.reply("Введите доход в формате: категория сумма (например, Зарплата 15000)")

@dp.message_handler(lambda message: message.text == "Добавить расход")
async def add_expense(message: types.Message):
    await message.reply("Введите расход в формате: категория сумма (например, Еда 500)")

@dp.message_handler(lambda message: message.text == "Показать баланс")
async def show_balance(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id=? AND type='доход'", (user_id,))
    total_income = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id=? AND type='расход'", (user_id,))
    total_expense = cursor.fetchone()[0]
    balance = total_income - total_expense
    await message.reply(f"Ваш баланс: {balance:.2f} ₽\nДоходы: {total_income:.2f} ₽\nРасходы: {total_expense:.2f} ₽")

@dp.message_handler()
async def handle_transaction(message: types.Message):
    user_id = message.from_user.id
    try:
        parts = message.text.rsplit(" ", 1)
        if len(parts) != 2:
            raise ValueError
        category, amount = parts
        amount = float(amount)
        transaction_type = "доход" if amount > 0 else "расход"
        cursor.execute("INSERT INTO transactions (user_id, type, category, amount) VALUES (?, ?, ?, ?)", (user_id, transaction_type, category, abs(amount)))
        conn.commit()
        await message.reply("Транзакция добавлена!")
    except ValueError:
        await message.reply("Неверный формат. Введите категорию и сумму, например: Еда 500")

if name == "main":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
