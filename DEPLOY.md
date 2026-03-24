# Развертывание бота на бесплатные хостинги

## 📋 Требования

Перед развертыванием убедитесь, что у вас есть:
- **Telegram Bot Token** - получен от @BotFather
- **API ключи** для AI сервисов (хотя бы один):
  - `GOOGLE_API_KEY` - для Gemini (рекомендуется, бесплатно)
  - `GROQ_API_KEY` - для Groq (быстро, бесплатно)
  - `OPENAI_API_KEY` - для OpenAI (платно)
- **Firebase проект** (опционально, для хранения пользователей):
  - `FIRESTORE_PROJECT_ID`
  - `FIREBASE_CREDENTIALS` (JSON ключ сервисного аккаунта)

## 🚀 Варианты бесплатного хостинга

### 1. Railway (рекомендуется)

**Преимущества:**
- Простая настройка
- Бесплатные 5$ кредита ежемесячно (~500 часов)
- Автоматические деплои из GitHub

**Шаги:**

1. Создайте аккаунт на [railway.app](https://railway.app)
2. Подключите ваш GitHub репозиторий
3. Создайте новый проект → Deploy from GitHub
4. Выберите репозиторий с ботом
5. Настройте переменные окружения в Railway Dashboard:
   - Перейдите в проект → Variables
   - Добавьте:
     ```
     TELEGRAM_BOT_TOKEN=ваш_токен_бота
     GOOGLE_API_KEY=ваш_ключ_gemini
     GROQ_API_KEY=ваш_ключ_groq (опционально)
     OPENAI_API_KEY=ваш_ключ_openai (опционально)
     FIRESTORE_PROJECT_ID=ваш_project_id (опционально)
     FIREBASE_CREDENTIALS=содержимое_JSON_ключа (опционально)
     ```
6. Деплой начнется автоматически
7. После успешного деплоя скопируйте URL вашего сервиса
8. Установите webhook для Telegram:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_RAILWAY_URL>"
   ```

**Примечание:** Railway использует `railway.json` и `Procfile` из репозитория.

---

### 2. Render

**Преимущества:**
- Бесплатный веб-сервис (750 часов/месяц)
- Автоматические деплои из GitHub/GitLab
- Встроенный health check

**Шаги:**

1. Создайте аккаунт на [render.com](https://render.com)
2. Создайте новый Web Service
3. Подключите ваш GitHub репозиторий
4. Настройте:
   - **Name**: telegram-ai-assistant
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free
5. Добавьте Environment Variables (в разделе Advanced):
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   GOOGLE_API_KEY=ваш_ключ_gemini
   GROQ_API_KEY=ваш_ключ_groq (опционально)
   OPENAI_API_KEY=ваш_ключ_openai (опционально)
   FIRESTORE_PROJECT_ID=ваш_project_id (опционально)
   FIREBASE_CREDENTIALS=содержимое_JSON_ключа (опционально)
   ```
6. Создайте сервис
7. После деплоя скопируйте URL сервиса
8. Установите webhook:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_RENDER_URL>"
   ```

**Примечание:** Render использует `render.yaml` для автоматической настройки.

---

### 3. Google Cloud Functions (serverless)

**Преимущества:**
- Бесплатный лимит: 2 млн вызовов/месяц
- Автоматическое масштабирование
- Не нужно держать процесс running

**Шаги:**

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com)
2. Установите [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. Аутентифицируйтесь: `gcloud auth login`
4. Установите проект: `gcloud config set project YOUR_PROJECT_ID`
5. Включите необходимые API:
   ```bash
   gcloud services enable cloudfunctions.googleapis.com
   gcloud services enable firestore.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```
6. Создайте Firestore базу:
   ```bash
   gcloud firestore databases create --region=us-central
   ```
7. Установите переменные окружения:
   ```bash
   export TELEGRAM_BOT_TOKEN="ваш_токен"
   export GOOGLE_API_KEY="ваш_ключ"
   export FIRESTORE_PROJECT_ID="YOUR_PROJECT_ID"
   ```
8. Запустите скрипт деплоя:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
9. Скопируйте URL функции из вывода
10. Установите webhook:
    ```bash
    curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_FUNCTION_URL>"
    ```

---

## 🔧 Настройка переменных окружения

### Обязательные:
- `TELEGRAM_BOT_TOKEN` - токен от @BotFather

### Рекомендуемые (выберите хотя бы один AI сервис):
- `GOOGLE_API_KEY` - [Gemini API](https://makersuite.google.com/app/apikey) (бесплатно)
- `GROQ_API_KEY` - [Groq Cloud](https://console.groq.com/keys) (бесплатно, быстро)
- `OPENAI_API_KEY` - [OpenAI Platform](https://platform.openai.com/api-keys) (платно)

### Опциональные:
- `FIRESTORE_PROJECT_ID` - ID Firebase проекта
- `FIREBASE_CREDENTIALS` - JSON ключ сервисного аккаунта Firebase

---

## 📝 Проверка работы

1. Проверьте статус webhook:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```

2. Отправьте сообщение боту в Telegram

3. Проверьте логи:
   - **Railway**: Dashboard → Logs
   - **Render**: Dashboard → Logs
   - **Cloud Functions**: `gcloud functions logs read FUNCTION_NAME`

---

## ⚠️ Важные замечания

1. **Бесплатные лимиты:**
   - Railway: 5$ кредита/месяц (~500 часов)
   - Render: 750 часов/месяц
   - Cloud Functions: 2 млн вызовов/месяц

2. **Процесс простаивает при бездействии:**
   - Railway/Render могут "засыпать" после периода неактивности
   - Первый запрос после сна будет медленным (холодный старт)
   - Cloud Functions всегда "засыпают" между вызовами

3. **База данных:**
   - Локальный `users_local.json` не сохраняется между инстансами
   - Для постоянного хранения используйте Firebase Firestore
   - При использовании нескольких инстансов локальный файл будет разным

4. **Файлы знаний:**
   - Папка `knowledge_base/` должна быть в репозитории
   - При деплое файлы копируются автоматически

---

## 🔄 Миграция с локального запуска

Если вы уже использовали бота локально:

1. Экспортируйте данные пользователей из `users_local.json`
2. Настройте Firebase Firestore
3. Импортируйте данные в Firestore через Firebase Console или скрипт

---

## 🆘 Поддержка

При проблемах:
1. Проверьте логи на хостинге
2. Убедитесь, что все переменные окружения заданы
3. Проверьте, что бот получил webhook URL
4. Убедитесь, что AI API ключи действительны

Удачи! 🚀