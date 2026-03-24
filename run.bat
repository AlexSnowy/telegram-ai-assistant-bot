@echo off
echo ========================================
echo    AI Assistant Telegram Bot
echo    Ishga tushirilmoqda...
echo ========================================
echo.

REM Активация виртуального окружения
call .venv\Scripts\activate

REM Запуск бота
echo Bot ishga tushirilmoqda...
echo Telegram bot token: %TELEGRAM_BOT_TOKEN%
echo.

python -m src.bot

pause