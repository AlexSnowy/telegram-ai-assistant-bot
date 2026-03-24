"""
Simple Telegram Bot Web Server for Railway/Render
"""

import os
import sys
import logging
from flask import Flask, request, jsonify

# Настройка логирования в stdout для Railway
logging.basicConfig(
    level=logging.DEBUG,  # Более детальное логирование
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_instance = None

@app.route('/', methods=['GET', 'POST'])
def health():
    return jsonify({'status': 'ok', 'service': 'telegram-bot'}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Импортируем и инициализируем при первом вызове
        global bot_instance
        if bot_instance is None:
            logger.info("Bot not initialized yet. Initializing...")
            try:
                from src.bot import AssistantBot
                from config import Config
                logger.info(f"Config loaded: TELEGRAM_BOT_TOKEN={Config.TELEGRAM_BOT_TOKEN[:10]}...")
                bot_instance = AssistantBot()
                logger.info("Bot initialized successfully")
            except Exception as init_error:
                logger.error(f"Failed to initialize bot: {init_error}", exc_info=True)
                return jsonify({'error': f'Bot initialization failed: {str(init_error)}'}), 500
        
        from telegram import Update
        import asyncio
        
        update_data = request.get_json()
        if not update_data:
            logger.warning("Received empty update data")
            return jsonify({'error': 'No data'}), 400
        
        logger.info(f"Processing update: {update_data.get('update_id')}")
        update = Update.de_json(update_data, bot_instance.get_application().bot)
        
        async def process():
            # Убедимся, что Application инициализирован
            await bot_instance.ensure_initialized()
            await bot_instance.get_application().process_update(update)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process())
            logger.info("Update processed successfully")
        finally:
            loop.close()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    
    # Логируем информацию о запуске
    logger.info("=" * 60)
    logger.info("Telegram AI Assistant Bot starting...")
    logger.info(f"Port: {port}")
    logger.info(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")
    
    # Проверяем наличие обязательных переменных окружения
    required_vars = ['TELEGRAM_BOT_TOKEN', 'GOOGLE_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        logger.error("Please set these variables in Railway Dashboard → Variables")
    else:
        logger.info("All required environment variables are set")
    
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)