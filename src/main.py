import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import sqlite3
import datetime
import re
import asyncio

from aiogram.fsm.storage.memory import MemoryStorage


##logging.basicConfig(level=logging.INFO)
##logger = logging.getLogger(name)

BOT_TOKEN = "7627437523:AAH9VzKRBuocnfaNmnaYnDEU0DWg5cEnCqw"


# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()






# Подключение к базе данных
conn = sqlite3.connect('finance_olympiad.db')
cursor = conn.cursor()


# Создание таблицы для регистраций
cursor.execute('''
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    grade INTEGER NOT NULL,
    school TEXT NOT NULL,
    city TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    teacher_name TEXT,
    registration_date TEXT NOT NULL,
    UNIQUE(user_id)
)
''')
conn.commit()

# Состояния для FSM
class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_grade = State()
    waiting_for_school = State()
    waiting_for_city = State()
    waiting_for_email = State()
    waiting_for_phone = State()
    waiting_for_teacher = State()

# Меню команд
async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command="/start", description="Начало работы"),
        types.BotCommand(command="/register", description="Регистрация на олимпиаду"),
        types.BotCommand(command="/my_data", description="Мои данные"),
        types.BotCommand(command="/cancel", description="Отменить регистрацию"),
        types.BotCommand(command="/info", description="Информация об олимпиаде")
    ]
    await bot.set_my_commands(commands)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для регистрации на олимпиаду Финатлон.\n"
        "Чтобы начать регистрацию, введите команду /register."
    )

# Обработчик команды /register
@dp.message(Command("register"))
async def cmd_register(message: types.Message, state: FSMContext):
    # Проверяем, не зарегистрирован ли уже пользователь
    cursor.execute("SELECT * FROM registrations WHERE user_id = ?", (message.from_user.id,))
    if cursor.fetchone():
        await message.answer("Вы уже зарегистрированы на олимпиаду!")
        return
    
    await state.set_state(RegistrationStates.waiting_for_full_name)
    await message.answer(
        "📝 <b>Регистрация на олимпиаду по финансовой грамотности</b>\n\n"
        "Шаг 1 из 7\n"
        "Введите ваше <b>ФИО</b> (полностью, как в документах):",
        parse_mode="HTML"
    )

# Обработчик отмены
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        cursor.execute("DELETE FROM registrations WHERE user_id = ?", (message.from_user.id,))
        conn.commit()
        await message.answer("Ваша регистрация отменена.")
        return
    
    await state.clear()
    await message.answer("Регистрация прервана. Вы можете начать заново с /register")

# Обработчик ФИО
@dp.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    if len(message.text.split()) < 2:
        await message.answer("Пожалуйста, введите ФИО полностью (например: Иванов Иван Иванович)")
        return
    
    await state.update_data(full_name=message.text)
    await state.set_state(RegistrationStates.waiting_for_grade)
    
    # Создаем клавиатуру с классами
    builder = ReplyKeyboardBuilder()
    grades = ["8", "9", "10", "11"]
    for grade in grades:
        builder.add(KeyboardButton(text=grade))
    builder.adjust(2)
    
    await message.answer(
        "Шаг 2 из 7\n"
        "Выберите ваш <b>класс</b>:",
        parse_mode="HTML",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

# Обработчик класса
@dp.message(RegistrationStates.waiting_for_grade)
async def process_grade(message: types.Message, state: FSMContext):
    if message.text not in ["8", "9", "10", "11"]:
        await message.answer("Пожалуйста, выберите класс из предложенных вариантов (8-11)")
        return
    
    await state.update_data(grade=int(message.text))
    await state.set_state(RegistrationStates.waiting_for_school)
    await message.answer(
        "Шаг 3 из 7\n"
        "Введите полное название вашей <b>школы</b> (например: МБОУ Лицей №1 г. Москва):",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Обработчик школы
@dp.message(RegistrationStates.waiting_for_school)
async def process_school(message: types.Message, state: FSMContext):
    if len(message.text) < 5:
        await message.answer("Название школы слишком короткое. Введите полное название.")
        return
    
    await state.update_data(school=message.text)
    await state.set_state(RegistrationStates.waiting_for_city)
    await message.answer(
        "Шаг 4 из 7\n"
        "Введите ваш <b>город</b> проживания:",
        parse_mode="HTML"
    )

# Обработчик города
@dp.message(RegistrationStates.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(RegistrationStates.waiting_for_email)
    await message.answer(
        "Шаг 5 из 7\n"
        "Введите ваш <b>email</b> для связи (например: example@mail.ru):",
        parse_mode="HTML"
    )



# Обработчик email
@dp.message(RegistrationStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", message.text):
        await message.answer("Пожалуйста, введите корректный email (например: example@mail.ru)")
        return
    
    await state.update_data(email=message.text)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer(
        "Шаг 6 из 7\n"
        "Введите ваш <b>номер телефона</b> (в формате +7XXXXXXXXXX):",
        parse_mode="HTML"
    )

# Обработчик телефона
@dp.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text
    if not re.match(r"^\+7\d{10}$", phone):
        await message.answer("Пожалуйста, введите номер в формате +7XXXXXXXXXX (например: +79161234567)")
        return
    
    await state.update_data(phone=phone)
    await state.set_state(RegistrationStates.waiting_for_teacher)
    await message.answer(
        "Шаг 7 из 7\n"
        "Введите <b>ФИО вашего учителя</b> по экономике/обществознанию (если есть, или напишите 'нет'):",
        parse_mode="HTML"
    )

@dp.message(RegistrationStates.waiting_for_teacher)
async def process_teacher(message: types.Message, state: FSMContext):
    teacher_name = message.text
    if message.text.lower() != "нет":
         if len(message.text) > 50:
            await message.answer("Имя учителя слишком длинное. Пожалуйста, введите до 50 символов или введите 'нет'.")
            return

        

        
        
         teacher_name = message.text
    else:
        teacher_name = None
    
    data = await state.get_data()


    try:
        # Save registration to the database
        cursor.execute(
            "INSERT INTO registrations (user_id, full_name, grade, school, city, email, phone, teacher_name, registration_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                message.from_user.id,
                data['full_name'],
                data['grade'],
                data['school'],
                data['city'],
                data['email'],
                data['phone'],
                teacher_name,
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        conn.commit()

        await state.clear()

        # Retrieve user data for confirmation message
        cursor.execute(
            "SELECT * FROM registrations WHERE user_id = ?", (message.from_user.id,)
        )
        registration = cursor.fetchone()

        # Build the response message with user data
        response = (
            "Спасибо за регистрацию!\n"
            "Вот ваши данные:\n\n"
            f"ФИО: {registration[1]}\n"  # Corrected index from 2 to 1
            f"Класс: {registration[2]}\n"  # Corrected index from 3 to 2
            f"Школа: {registration[3]}\n"  # Corrected index from 4 to 3
            f"Город: {registration[4]}\n"  # Corrected index from 5 to 4
            f"Email: {registration[5]}\n"  # Corrected index from 6 to 5
            f"Телефон: {registration[6]}\n"  # Corrected index from 7 to 6
        )

        if registration[7]:  # Corrected index from 8 to 7
            response += f"Учитель: {registration[7]}\n"  # Corrected index from 8 to 7

        response += (
            f"Дата регистрации: {registration[8]}\n" #Date is 8
        )

        await message.answer(response) # Show user data after registration
    except Exception as e:
        logging.error(f"Error processing teacher information or storing data: {e}")
        await message.answer(
            "Произошла ошибка при обработке данных. Пожалуйста, попробуйте снова."
        )


# Обработчик команды /my_data
@dp.message(Command("my_data"))
async def cmd_my_data(message: types.Message):
    cursor.execute(
        "SELECT * FROM registrations WHERE user_id = ?",
        (message.from_user.id,)
    )
    registration = cursor.fetchone()
    
    if not registration:
        await message.answer("Вы еще не зарегистрированы. Используйте /register")
        return
    
    response = (
        "📋 <b>Ваши данные:</b>\n\n"
        f"👤 <b>ФИО:</b> {registration[2]}\n"
        f"🏫 <b>Класс:</b> {registration[3]}\n"
        f"📚 <b>Школа:</b> {registration[4]}\n"
        f"🌆 <b>Город:</b> {registration[5]}\n"
        f"📧 <b>Email:</b> {registration[6]}\n"
        f"📱 <b>Телефон:</b> {registration[7]}\n"
    )
    
    if registration[8]:
        response += f"👩‍🏫 <b>Учитель:</b> {registration[8]}\n"
    
    response += (
        f"\n📅 <b>Дата регистрации:</b> "
        f"{datetime.datetime.strptime(registration[9], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')}\n\n"
        "Если нужно изменить данные, отмените регистрацию (/cancel) и пройдите ее заново."
    )
    
    await message.answer(response, parse_mode="HTML")

async def main():
    logging.basicConfig(level=logging.INFO)  # Turn on logging

    try:
        await set_commands(bot)
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
