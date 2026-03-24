"""
Simple Telegram Bot Web Server for Railway/Render
"""

import os
import logging
from flask import Flask, request, jsonify

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_instance = None

@app.route('/')
def health():
    return jsonify({'status': 'ok', 'service': 'telegram-bot'}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Импортируем и инициализируем при первом вызове
        global bot_instance
        if bot_instance is None:
            from src.bot import AssistantBot
            from config import Config
            logger.info("Initializing bot...")
            bot_instance = AssistantBot()
            logger.info("Bot initialized")
        
        from telegram import Update
        import asyncio
        
        update_data = request.get_json()
        if not update_data:
            return jsonify({'error': 'No data'}), 400
        
        update = Update.de_json(update_data, bot_instance.get_application().bot)
        
        async def process():
            await bot_instance.get_application().process_update(update)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process())
        finally:
            loop.close()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)