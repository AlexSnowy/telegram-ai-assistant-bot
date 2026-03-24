"""
Telegram AI Assistant Bot - Google Cloud Functions Entry Point

Этот файл служит entry point для развертывания на Google Cloud Functions.
"""

import os
import logging
from typing import Dict, Any

from telegram import Update
from telegram.ext import Application

from config import Config
from src.bot import AssistantBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра бота
_bot_instance = None

def initialize_bot() -> AssistantBot:
    """Инициализация бота (вызывается один раз при холодном старте)"""
    global _bot_instance

    if _bot_instance is None:
        try:
            logger.info("Инициализация бота...")
            _bot_instance = AssistantBot()
            logger.info("Бот успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации бота: {e}")
            raise

    return _bot_instance

def telegram_webhook(request):
    """
    Entry point для Google Cloud Functions

    Args:
        request: Flask request объект от Google Cloud Functions

    Returns:
        Response объект
    """
    try:
        # Инициализируем бота при первом вызове
        bot = initialize_bot()
        application = bot.get_application()

        # Обрабатываем входящий update от Telegram
        if request.method == 'POST':
            update_data = request.get_json()

            if not update_data:
                return ('No data', 400)

            # Создаем Update объект
            update = Update.de_json(update_data, application.bot)

            # Обрабатываем update асинхронно
            # В Cloud Functions мы не можем использовать asyncio.run напрямую
            # Поэтому используем синхронный вызов через asyncio
            import asyncio

            async def process_update():
                # Инициализируем приложение в текущем event loop
                await bot.ensure_initialized()
                await application.process_update(update)

            # Запускаем асинхронную задачу
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_update())
            finally:
                loop.close()

            return ('OK', 200)

        else:
            # GET запрос - для проверки health
            return ('Bot is running', 200)

    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}", exc_info=True)
        return (f'Error: {str(e)}', 500)

# Для локального тестирования
if __name__ == '__main__':
    bot = AssistantBot()
    bot.run()