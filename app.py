"""
Telegram AI Assistant Bot - Web Server for Railway/Render
Запускает бота в режиме webhook с Flask сервером
"""

import os
import logging
from flask import Flask, request, jsonify

from config import Config
from src.bot import AssistantBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Глобальная переменная для хранения экземпляра бота
_bot_instance = None
_bot_initialized = False

def initialize_bot():
    """Инициализация бота (вызывается один раз при холодном старте)"""
    global _bot_instance, _bot_initialized

    if not _bot_initialized:
        try:
            logger.info("Инициализация бота...")
            _bot_instance = AssistantBot()
            _bot_initialized = True
            logger.info("Бот успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации бота: {e}", exc_info=True)
            _bot_instance = None
            raise

    return _bot_instance

@app.route('/')
def health_check():
    """Health check endpoint для Railway/Render"""
    try:
        # Пытаемся инициализировать бота если еще не инициализирован
        if not _bot_initialized:
            logger.info("Health check: попытка инициализации бота...")
            initialize_bot()
        
        return jsonify({
            'status': 'ok',
            'message': 'Bot is running',
            'initialized': _bot_initialized
        }), 200
    except Exception as e:
        logger.error(f"Ошибка в health check: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Webhook endpoint для Telegram"""
    try:
        # Инициализируем бота при первом вызове
        bot = initialize_bot()
        application = bot.get_application()

        # Обрабатываем входящий update от Telegram
        update_data = request.get_json()

        if not update_data:
            return jsonify({'error': 'No data'}), 400

        # Создаем Update объект
        from telegram import Update
        update = Update.de_json(update_data, application.bot)

        # Обрабатываем update асинхронно
        import asyncio

        async def process_update():
            await application.process_update(update)

        # Запускаем асинхронную задачу
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process_update())
        finally:
            loop.close()

        return jsonify({'status': 'ok'}), 200

    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/set-webhook', methods=['GET'])
def set_webhook_info():
    """Информация об установке webhook"""
    try:
        bot_token = Config.TELEGRAM_BOT_TOKEN
        webhook_url = f"{request.url_root}webhook"
        return jsonify({
            'message': 'Use this URL as webhook endpoint',
            'webhook_url': webhook_url,
            'setup_command': f"curl -X POST 'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}'"
        }), 200
    except Exception as e:
        logger.error(f"Ошибка в set_webhook_info: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Получаем порт из переменной окружения (Railway/Render устанавливают автоматически)
    port = int(os.getenv('PORT', 8080))

    # Настраиваем логирование в stdout для Railway
    import sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info(f"Запуск сервера на порту {port}...")
    logger.info(f"Health check: http://localhost:{port}/")
    logger.info(f"Webhook: http://localhost:{port}/webhook")

    try:
        # Запускаем Flask приложение
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Критическая ошибка запуска сервера: {e}", exc_info=True)
        raise