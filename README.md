# AI Assistant Telegram Bot

Узбекский AI-ассистент для работы с китайскими продавцами/производителями.

## 🚀 Новое: Бесплатный Groq API

Бот теперь поддерживает **Groq** - бесплатный и сверхбыстрый AI API!

- ✅ **Бесплатно** без ограничений
- ⚡ **Скорость** ~200ms (в 5-10 раз быстрее Gemini)
- 🎯 **Качество** Llama 3.3 70B (на уровне GPT-4)
- 🔄 **Автоматический fallback** на Gemini/OpenAI

**Настройка за 2 минуты**: [GROQ_SETUP.md](GROQ_SETUP.md)

## Особенности

- Полностью на узбекском языке
- База знаний из документов (doc, docx, xlsx, txt)
- Возможность добавления промтов через текстовые файлы
- Развертывание на Google Cloud Platform (бесплатный tier)
- Поддержка **множества AI провайдеров**: Groq, Gemini, OpenAI
- Автоматический выбор лучшего доступного AI

## Поддерживаемые AI провайдеры

| Провайдер | Стоимость | Лимиты | Скорость | Модель по умолчанию |
|-----------|-----------|--------|----------|---------------------|
| **Groq** | **Бесплатно** | **Без лимитов** | **~200ms** | `llama-3.3-70b-versatile` |
| Gemini | Бесплатно* | Квота может быть 0 | ~1-2s | `gemini-2.0-flash` |
| OpenAI | Платно | По тарифу | ~500ms | `gpt-3.5-turbo` |

*Gemini free tier часто имеет квоту 0. Рекомендуется Groq.

## Структура проекта

```
ai-ibo/
├── main.py                 # Entry point для Google Cloud Functions
├── requirements.txt        # Python зависимости
├── config.py              # Конфигурация
├── knowledge_base/        # Обработанные документы базы знаний
├── prompts/              # Промты в формате .txt
├── src/
│   ├── __init__.py
│   ├── document_processor.py  # Обработка документов
│   ├── knowledge_manager.py   # Управление базой знаний
│   ├── prompt_manager.py     # Управление промтами
│   ├── gemini_client.py      # Клиент Gemini API
│   ├── groq_client.py        # Клиент Groq API ✨ НОВОЕ
│   ├── openai_client.py      # Клиент OpenAI API
│   ├── bot.py                # Логика Telegram бота
│   └── utils.py              # Вспомогательные функции
├── deploy.sh              # Скрипт деплоя на GCP
├── GROQ_SETUP.md          # Инструкция по настройке Groq ✨ НОВОЕ
├── FREE_AI_APIS.md        # Сравнение всех бесплатных AI API ✨ НОВОЕ
├── test_groq.py           # Тест Groq подключения ✨ НОВОЕ
└── .gitignore
```

## Настройка

### Быстрая настройка с Groq (рекомендуется)

1. **Получите бесплатный API ключ**:
   - Перейдите: https://console.groq.com/keys
   - Войдите через Google/GitHub
   - Нажмите "Create API Key"
   - Скопируйте ключ (начинается с `gsk_`)

2. **Добавьте ключ в `.env`**:
   ```env
   GROQ_API_KEY=gsk_ваш_ключ_здесь
   ```

3. **Запустите бота**:
   ```bash
   python -m src.bot
   ```

Готово! Бот автоматически использует Groq.

### Полная настройка (все провайдеры)

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения в `.env`:
   - `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather (обязательно)
   - `GROQ_API_KEY` - API ключ Groq (рекомендуется, бесплатно)
   - `GOOGLE_API_KEY` - API ключ Google Gemini (опционально)
   - `FIRESTORE_PROJECT_ID` - ID проекта Firestore (если используете)

3. Локальный запуск для тестирования:
```bash
python -m src.bot
```

4. Проверьте работу Groq:
```bash
python test_groq.py
```

## Как это работает

Бот использует **приоритетный выбор AI клиента**:

1. **Groq** - если указан `GROQ_API_KEY` (первый приоритет)
2. **Gemini** - если указан `GOOGLE_API_KEY` (второй приоритет)
3. **OpenAI** - если указан `OPENAI_API_KEY` (третий приоритет)

Если выбранный клиент недоступен, бот попытается использовать следующий.

Логика в `src/bot.py::_initialize_ai_client()`.

## Настройка моделей

В `config.py` можно изменить модели:

```python
# Groq (рекомендуется)
GROQ_MODEL = 'llama-3.3-70b-versatile'  # Лучшая
# GROQ_MODEL = 'llama-3.1-8b-instant'   # Быстрая

# Gemini
GEMINI_MODEL = 'gemini-1.5-flash'  # Бесплатная версия

# OpenAI
OPENAI_MODEL = 'gpt-3.5-turbo'
```

Список всех моделей Groq: https://console.groq.com/docs/models

## Деплой на Google Cloud Functions

1. Установите Google Cloud SDK
2. Выполните:
```bash
chmod +x deploy.sh
./deploy.sh
```

## Команды бота

- `/start` - Начало работы
- `/help` - Помощь
- `/addprompt` - Добавить промт (загрузите .txt файл)
- `/listprompts` - Список доступных промтов
- `/knowledge` - Поиск в базе знаний

## Язык

Бот полностью работает на узбекском языке (ўзбекча).

## Документация

- [GROQ_SETUP.md](GROQ_SETUP.md) - Подробная настройка Groq
- [FREE_AI_APIS.md](FREE_AI_APIS.md) - Сравнение всех бесплатных AI API
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [SETUP.md](SETUP.md) - Полная инструкция по настройке

## Лицензия

[Смотрите LICENSE](LICENSE)

## Деплой на Google Cloud Functions

1. Установите Google Cloud SDK
2. Выполните:
```bash
chmod +x deploy.sh
./deploy.sh
```

## Команды бота

- `/start` - Начало работы
- `/help` - Помощь
- `/addprompt` - Добавить промт (загрузите .txt файл)
- `/listprompts` - Список доступных промтов
- `/knowledge` - Поиск в базе знаний

## Язык

Бот полностью работает на узбекском языке (ўзбекча).