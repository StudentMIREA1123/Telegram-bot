import logging

from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from utils import (BREEDS, MOSCOW, ApiError, build_avatar_url, get_cat,
                   get_rates, get_user_info, get_weather)

logger = logging.getLogger(__name__)

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ['Фото котика', 'Сгенери аватар'],
        ['Мой ID', 'Курс валют'],
        ['Погода сегодня'],
    ],
    resize_keyboard=True,
)

BREED_MENU = ReplyKeyboardMarkup(
    [
        ['Абиссинская', 'Бенгальская'],
        ['Сиамская', 'Сибирская'],
        ['Рэгдолл', 'Мейн-кун'],
        ['Персидская', 'Британская'],
        ['Случайная порода'],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def log_action(update: Update, action: str):
    logger.info('Пользователь %s: %s', update.effective_user.id, action)


async def wake_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_action(update, '/start')
    info = get_user_info(update)
    await update.message.reply_text(
        f"Привет, {info['full_name']}! Спасибо, что присоединился!",
        reply_markup=MAIN_MENU,
    )


async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_action(update, 'запрос ID')
    info = get_user_info(update)
    username = f"@{info['username']}" if info['username'] else 'не указан'
    await update.message.reply_text(
        f"🆔 Твой ID: {info['user_id']}\n"
        f"💬 ID чата: {info['chat_id']}\n"
        f"👤 Имя: {info['full_name']}\n"
        f"🔗 Username: {username}\n"
        f"🌐 Язык: {info['language']}\n"
        f"📂 Тип чата: {info['chat_type']}"
    )


async def ask_breed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Выбери породу котика:', reply_markup=BREED_MENU)


async def send_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = get_user_info(update)
    chosen = update.message.text
    breed_id = BREEDS.get(chosen)
    breed_name = chosen if breed_id else None
    try:
        url, breed = await get_cat(breed_id, breed_name)
        await context.bot.send_photo(
            chat_id=info['chat_id'],
            photo=url,
            caption=f"🐱 Порода: {breed}\nСпециально для {info['first_name']}",
        )
    except ApiError as e:
        logger.warning('Не удалось получить котика: %s', e)
        await update.message.reply_text('Не удалось получить котика 😿 Попробуй позже')
    except TelegramError:
        logger.exception('Telegram не смог отправить фото котика')
        await update.message.reply_text('Telegram не смог загрузить фото, попробуй ещё раз')
    await update.message.reply_text('👇', reply_markup=MAIN_MENU)


async def send_avatar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info = get_user_info(update)
    try:
        await context.bot.send_photo(
            chat_id=info['chat_id'],
            photo=build_avatar_url(info),
            caption='Твой аватар 🤖',
        )
    except TelegramError:
        logger.exception('Telegram не смог отправить аватар')
        await update.message.reply_text('Не удалось создать аватар, попробуй ещё раз')


async def send_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(await get_rates())
    except ApiError as e:
        logger.warning('Не удалось получить курсы: %s', e)
        await update.message.reply_text('Не удалось получить курс валют')


async def request_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton('Отправить координаты 📍', request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        'Пожалуйста, поделитесь своей геолокацией:',
        reply_markup=keyboard,
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_action(update, 'отправил геолокацию')
    try:
        location = update.message.location
        if location:
            latitude, longitude = location.latitude, location.longitude
        else:
            logger.info('Геолокация не пришла, используется Москва')
            latitude, longitude = MOSCOW
        context.user_data['location'] = (latitude, longitude)
        report = await get_weather(latitude, longitude)
    except ApiError as e:
        logger.warning('Не удалось получить погоду: %s', e)
        report = f'Не удалось получить погоду: {e}'
    except Exception:
        logger.exception('Непредвиденная ошибка при обработке геолокации')
        report = 'Ошибка при обработке геолокации'
    await update.message.reply_text(report)
    await update.message.reply_text('👇', reply_markup=MAIN_MENU)


ACTIONS = {
    'Фото котика': ask_breed,
    'Сгенери аватар': send_avatar,
    'Мой ID': my_id,
    'Курс валют': send_rates,
    'Погода сегодня': request_location,
    'Случайная порода': send_cat,
}
for _name in BREEDS:
    ACTIONS[_name] = send_cat


async def say_hi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    action = ACTIONS.get(text)
    if action:
        log_action(update, f'кнопка «{text}»')
        await action(update, context)
    else:
        logger.debug('Пользователь %s прислал обычный текст', update.effective_user.id)
        info = get_user_info(update)
        await update.message.reply_text(f"{info['first_name']}, как твои дела?")