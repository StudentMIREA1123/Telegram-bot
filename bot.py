import logging
import os

from dotenv import load_dotenv
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          filters)

from handlers import handle_location, my_id, say_hi, wake_up
from logger_config import setup_logging

logger = logging.getLogger(__name__)


async def error_handler(update, context):
    logger.error('Необработанная ошибка при обработке обновления',
                 exc_info=context.error)


def run_bot():
    load_dotenv()
    setup_logging()

    token = os.getenv('TOKEN')
    if not token:
        logger.critical('Не найден TOKEN. Проверьте файл .env рядом с main.py')
        raise RuntimeError('Не найден TOKEN. Проверьте файл .env рядом с main.py')

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('start', wake_up))
    app.add_handler(CommandHandler('myid', my_id))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, say_hi))
    app.add_error_handler(error_handler)

    logger.info('Бот запущен, ожидаю сообщения')
    app.run_polling(drop_pending_updates=True)
    logger.info('Бот остановлен')