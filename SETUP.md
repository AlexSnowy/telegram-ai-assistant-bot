# Настройка и деплой AI Assistant Telegram Bot

## 📋 Содержание

1. [Предварительные требования](#предварительные-требования)
2. [Локальная настройка](#локальная-настройка)
3. [Настройка Google Cloud Platform](#настройка-google-cloud-platform)
4. [Деплой на Google Cloud Functions](#деплой-на-google-cloud-functions)
5. [Настройка Telegram бота](#настройка-telegram-бота)
6. [Загрузка документов и промтов](#загрузка-документов-и-промтов)
7. [Тестирование](#тестирование)
8. [Устранение неполадок](#устранение-неполадок)

---

## Предварительные требования

### 1. Учетная запись Google Cloud
- Создайте аккаунт на [Google Cloud Platform](https://cloud.google.com/)
- Включите биллинг (есть бесплатный tier с $300 кредита)

### 2. Установка Google Cloud SDK
```bash
# Windows: Скачайте и установите с https://cloud.google.com/sdk/docs/install
# Linux/Mac:
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### 3. Python 3.9+
```bash
python --version  # Должно быть 3.9 или выше
```

### 4. Токен Telegram бота
- Откройте @BotFather в Telegram
- Создайте нового бота: `/newbot`
- Сохраните токен (формат: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 5. Google Gemini API Key
- Перейдите на https://makersuite.google.com/app/apikey
- Создайте новый API ключ
- Сохраните его

---

## Локальная настройка

### 1. Клонируйте проект
```bash
cd D:/Python/ai-ibo
```

### 2. Создайте виртуальное окружение
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux/Mac:
source .venv/bin/activate
```

### 3. Установите зависимости
```bash
pip install -r requirements.txt
```

### 4. Настройте переменные окружения

Создайте файл `.env` в корне проекта:
```bash
TELEGRAM_BOT_TOKEN=8763371380:AAE3iA-rOEWrYzKtAYFB55XiUN5nlGZAoZo
GOOGLE_API_KEY=ваш_gemini_api_key
FIRESTORE_PROJECT_ID=ваш_project_id
```

ИЛИ установите переменные окружения в системе:
```bash
# Windows (PowerShell):
$env:TELEGRAM_BOT_TOKEN="ваш_токен"
$env:GOOGLE_API_KEY="ваш_ключ"
$env:FIRESTORE_PROJECT_ID="ваш_project_id"

# Linux/Mac:
export TELEGRAM_BOT_TOKEN="ваш_токен"
export GOOGLE_API_KEY="ваш_ключ"
export FIRESTORE_PROJECT_ID="ваш_project_id"
```

### 5. Локальный тестовый запуск
```bash
python -m src.bot
```

---

## Настройка Google Cloud Platform

### 1. Создайте новый проект
```bash
gcloud projects create ai-assistant-bot --name="AI Assistant Bot"
gcloud config set project ai-assistant-bot
```

### 2. Включите необходимые API
```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  firestore.googleapis.com \
  cloudbuild.googleapis.com
```

### 3. Создайте Firestore базу данных
```bash
gcloud firestore databases create --region=us-central
```

### 4. Получите Project ID
```bash
gcloud config get-value project
```
Запишите этот ID - он понадобится для `FIRESTORE_PROJECT_ID`

---

## Деплой на Google Cloud Functions

### 1. Настройте переменные окружения для деплоя
```bash
# Установите переменные для деплоя (опционально)
export GCF_REGION=us-central1
export GCF_FUNCTION_NAME=telegram-ai-assistant
export GCF_MEMORY=512MB
export GCF_TIMEOUT=60s
```

### 2. Запустите скрипт деплоя
```bash
chmod +x deploy.sh  # Linux/Mac
# Windows: просто запустите deploy.bat или выполните команды вручную

./deploy.sh
```

Скрипт автоматически:
- Проверит аутентификацию
- Включит необходимые API
- Создаст Firestore базу
- Задеплоит функцию

### 3. Установите переменные окружения функции
После деплоя установите секреты:
```bash
gcloud functions deploy telegram-ai-assistant \
  --region=us-central1 \
  --set-secrets "TELEGRAM_BOT_TOKEN=telegram-bot-token:latest" \
  --set-secrets "GOOGLE_API_KEY=gemini-api-key:latest" \
  --set-secrets "FIRESTORE_PROJECT_ID=project-id:latest"
```

ИЛИ используйте environment variables:
```bash
gcloud functions deploy telegram-ai-assistant \
  --region=us-central1 \
  --set-env-vars "TELEGRAM_BOT_TOKEN=ваш_токен,GOOGLE_API_KEY=ваш_ключ,FIRESTORE_PROJECT_ID=ваш_project_id"
```

### 4. Получите URL функции
```bash
gcloud functions describe telegram-ai-assistant --region=us-central1 --format='value(httpsTrigger.url)'
```

---

## Настройка Telegram бота

### 1. Установите webhook
```bash
curl -X POST "https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=<URL_ФУНКЦИИ>"
```

Пример:
```bash
curl -X POST "https://api.telegram.org/bot8763371380:AAE3iA-rOEWrYzKtAYFB55XiUN5nlGZAoZo/setWebhook?url=https://us-central1-ai-assistant-bot.cloudfunctions.net/telegram-ai-assistant"
```

### 2. Проверьте статус webhook
```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/getWebhookInfo"
```

### 3. Отправьте тестовое сообщение боту
Откройте Telegram и найдите своего бота по имени. Отправьте `/start`

---

## Загрузка документов и промтов

### 1. Подготовьте документы для базы знаний
Поддерживаемые форматы: `.txt`, `.docx`, `.xlsx`, `.pdf`

Отправьте файлы боту как документы (не как текст). Бот автоматически добавит их в базу знаний.

### 2. Добавьте промты
Отправьте `.txt` файл с промтом боту. Или используйте команду:
```
/promptname ваш промт текст
```

Пример промта (сохраните как `china_trade.txt`):
```
Siz Xitoy-Turkiston savdo bo'yicha mutaxassis yordamchisiz.

{query} savoliga javob bering, quyidagi kontekstni hisobga olgan holda:

{context}

Javob o'zbek tilida, aniq va amaliy bo'lishi kerak.
```

---

## Тестирование

### Локальное тестирование
```bash
# Активируйте виртуальное окружение
.venv\Scripts\activate  # Windows

# Установите переменные окружения
set TELEGRAM_BOT_TOKEN=ваш_токен
set GOOGLE_API_KEY=ваш_ключ

# Запустите бота
python -m src.bot
```

### Проверка через ngrok (альтернатива Cloud Functions)
```bash
# Установите ngrok
# Запустите туннель
ngrok http 8080

# Установите webhook на ngrok URL
curl -X POST "https://api.telegram.org/bot<ТОКЕН>/setWebhook?url=<NGROK_URL>/telegram-webhook"
```

---

## Устранение неполадок

### Ошибка: "Missing required environment variable"
Проверьте, что все переменные окружения установлены:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $GOOGLE_API_KEY
echo $FIRESTORE_PROJECT_ID
```

### Ошибка: "Function deployment failed"
Проверьте логи:
```bash
gcloud functions logs read telegram-ai-assistant --region=us-central1
```

### Webhook не работает
1. Проверьте URL webhook:
```bash
curl "https://api.telegram.org/bot<ТОКЕН>/getWebhookInfo"
```

2. Удалите и установите заново:
```bash
curl "https://api.telegram.org/bot<ТОКЕН>/deleteWebhook"
curl -X POST "https://api.telegram.org/bot<ТОКЕН>/setWebhook?url=<URL>"
```

### Ошибки с Firestore
Убедитесь, что Firestore база создана:
```bash
gcloud firestore databases list
```

### Бот не отвечает
Проверьте:
1. Логи Cloud Functions
2. Квоты Google Cloud (бесплатный tier)
3. Баланс Gemini API

---

## Мониторинг и логи

### Просмотр логов
```bash
# Логи Cloud Functions
gcloud functions logs read telegram-ai-assistant --region=us-central1 --limit=50

# Логи в реальном времени
gcloud functions logs tail telegram-ai-assistant --region=us-central1
```

### Статистика использования
```bash
# Cloud Functions статистика
gcloud functions describe telegram-ai-assistant --region=us-central1

# Firestore статистика
gcloud firestore databases describe --region=us-central
```

---

## Обновление бота

1. Внесите изменения в код
2. Задеплойте заново:
```bash
./deploy.sh
```

3. Перезапустите функцию (если нужно):
```bash
gcloud functions deploy telegram-ai-assistant --region=us-central1 --trigger-http
```

---

## Бесплатные лимиты GCP (Free Tier)

- **Cloud Functions**: ~43,000 вызовов/месяц
- **Firestore**: 50,000 операций чтения/день, 20,000 записей/день
- **Gemini API**: 60 запросов/минуту (бесплатно)

Этого достаточно для небольшого бота с ~1000 пользователями.

---

## Поддержка

При возникновении проблем:
1. Проверьте логи: `gcloud functions logs read`
2. Убедитесь, что все API включены
3. Проверьте квоты в Google Cloud Console
4. Свяжитесь с администратором

---

## 📝 Чек-лист настройки

- [ ] Установлен Google Cloud SDK
- [ ] Создан проект в GCP
- [ ] Включены API (Cloud Functions, Firestore)
- [ ] Создана Firestore база
- [ ] Получен Telegram Bot Token
- [ ] Получен Google Gemini API Key
- [ ] Установлены Python зависимости
- [ ] Настроены переменные окружения
- [ ] Бот локально запускается
- [ ] Бот задеплоен на Cloud Functions
- [ ] Установлен webhook
- [ ] Бот отвечает на сообщения
- [ ] Загружены документы в базу знаний
- [ ] Добавлены промты

✅ Все готово! Бот работает на бесплатном tier Google Cloud!