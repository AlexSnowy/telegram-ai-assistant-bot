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

def initialize_bot():
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

@app.route('/')
def health_check():
    """Health check endpoint для Railway/Render"""
    return {'status': 'ok', 'message': 'Bot is running'}, 200

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
        logger.error(f"Ошибка обработки запроса: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/set-webhook', methods=['GET'])
def set_webhook_info():
    """Информация об установке webhook"""
    bot_token = Config.TELEGRAM_BOT_TOKEN
    webhook_url = f"{request.url_root}webhook"
    return jsonify({
        'message': 'Use this URL as webhook endpoint',
        'webhook_url': webhook_url,
        'setup_command': f"curl -X POST 'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}'"
    }), 200

if __name__ == '__main__':
    # Получаем порт из переменной окружения (Railway/Render устанавливают автоматически)
    port = int(os.getenv('PORT', 8080))

    # Инициализируем бота
    try:
        bot = initialize_bot()
        logger.info(f"Запуск сервера на порту {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Ошибка запуска сервера: {e}")
        raise