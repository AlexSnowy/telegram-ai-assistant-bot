import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def setup_logging(level: str = 'INFO') -> logging.Logger:
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    # Отключение логирования httpx (HTTP запросы Telegram API)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    return logging.getLogger(__name__)

def ensure_directories(dirs: list):
    """Создание необходимых директорий"""
    for directory in dirs:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Директория создана/проверена: {directory}")

def get_user_identifier(update) -> str:
    """Получение идентификатора пользователя"""
    if update.message:
        user = update.message.from_user
        return f"{user.id}_{user.first_name or user.username}"
    elif update.callback_query:
        user = update.callback_query.from_user
        return f"{user.id}_{user.first_name or user.username}"
    return "unknown"

def truncate_text(text: str, max_length: int = 4000) -> str:
    """Обрезка текста до максимальной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_user_message(message: str) -> str:
    """Форматирование сообщения пользователя"""
    # Удаляем лишние пробелы и переносы
    message = ' '.join(message.split())
    return message.strip()

def is_uzbek_text(text: str) -> bool:
    """Простая проверка на узбекский текст"""
    # Узбекские специфические символы
    uzbek_chars = {'ў', 'қ', 'ғ', 'ш', 'ч', 'ў', 'ҳ', 'э', 'ё'}
    text_lower = text.lower()

    # Если есть узбекские символы, считаем узбекским
    for char in uzbek_chars:
        if char in text_lower:
            return True

    # Иначе проверяем на русские/английские слова
    # Если много русских слов - не узбекский
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    english_chars = set('abcdefghijklmnopqrstuvwxyz')

    russian_count = sum(1 for c in text_lower if c in russian_chars)
    english_count = sum(1 for c in text_lower if c in english_chars)

    # Если больше русских символов - не узбекский
    if russian_count > english_count and russian_count > 5:
        return False

    return True

def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]  # Ограничиваем длину

def markdown_to_html(text: str) -> str:
    """Преобразование простого Markdown разметки в HTML для Telegram"""
    import re
    
    # Жирный текст: **text** или __text__
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
    
    # Курсив: *text* или _text_
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    
    # Зачеркнутый: ~~text~~
    text = re.sub(r'~~(.*?)~~', r'<s>\1</s>', text)
    
    # Моноширинный: `text`
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    return text

# Импорт Path для ensure_directories
from pathlib import Path