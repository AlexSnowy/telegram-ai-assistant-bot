#!/bin/bash

echo "========================================"
echo "   AI Assistant Telegram Bot"
echo "   Запуск..."
echo "========================================"
echo

# Активация виртуального окружения
source .venv/bin/activate

# Запуск бота
echo "Бот запускается..."
echo "Telegram bot token: $TELEGRAM_BOT_TOKEN"
echo

python -m src.bot