#!/bin/bash

# Скрипт для деплоя Telegram бота на Google Cloud Functions

set -e  # Выход при ошибке

echo "🚀 Начинаем деплой Telegram AI Assistant на Google Cloud Functions..."

# Проверяем, установлен ли gcloud
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK не найден. Установите его с https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Проверяем аутентификацию
echo "🔐 Проверка аутентификации в GCP..."
gcloud auth list

# Устанавливаем проект
PROJECT_ID=${FIRESTORE_PROJECT_ID:-$(gcloud config get-value project)}
if [ -z "$PROJECT_ID" ]; then
    echo "❌ PROJECT_ID не задан. Установите переменную FIRESTORE_PROJECT_ID или выполните:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📦 Проект: $PROJECT_ID"

# Включаем необходимые API
echo "🔧 Включаем необходимые API..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Создаем Firestore базу данных (если не создана)
echo "🗄️  Проверяем Firestore..."
gcloud firestore databases create --region=us-central --project=$PROJECT_ID || echo "Firestore уже создан или в процессе"

# Устанавливаем region
REGION=${GCF_REGION:-us-central1}
echo "🌍 Region: $REGION"

# Устанавливаем имя функции
FUNCTION_NAME=${GCF_FUNCTION_NAME:-telegram-ai-assistant}
echo "📛 Имя функции: $FUNCTION_NAME"

# Устанавливаем runtime
RUNTIME=python311
echo "🐍 Runtime: $RUNTIME"

# Устанавливаем memory
MEMORY=${GCF_MEMORY:-512MB}
echo "💾 Memory: $MEMORY"

# Устанавливаем timeout
TIMEOUT=${GCF_TIMEOUT:-60s}
echo "⏱️  Timeout: $TIMEOUT"

# Устанавливаем entry point
ENTRY_POINT=telegram_webhook
echo "🎯 Entry point: $ENTRY_POINT"

# Удаляем старую функцию (если есть)
echo "🗑️  Удаляем старую функцию (если существует)..."
gcloud functions delete $FUNCTION_NAME --region=$REGION --quiet 2>/dev/null || echo "Функция не найдена или уже удалена"

# Деплой функции
echo "🚀 Деплой функции..."
gcloud functions deploy $FUNCTION_NAME \
    --region=$REGION \
    --runtime=$RUNTIME \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point=$ENTRY_POINT \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --project=$PROJECT_ID \
    --verbosity=info

# Получаем URL функции
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format='value(httpsTrigger.url)' --project=$PROJECT_ID)

echo ""
echo "✅ Деплой завершен!"
echo ""
echo "🔗 URL функции: $FUNCTION_URL"
echo ""
echo "📝 Следующие шаги:"
echo "1. Установите webhook для Telegram бота:"
echo "   curl -X POST \"https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=$FUNCTION_URL\""
echo ""
echo "2. Проверьте статус webhook:"
echo "   curl \"https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo\""
echo ""
echo "3. Установите переменные окружения для функции:"
echo "   gcloud functions deploy $FUNCTION_NAME ... --set-env-vars TELEGRAM_BOT_TOKEN=xxx,GOOGLE_API_KEY=yyy,FIRESTORE_PROJECT_ID=$PROJECT_ID"
echo ""
echo "📚 Логи функции можно посмотреть командой:"
echo "   gcloud functions logs read $FUNCTION_NAME --region=$REGION"
echo ""
echo "🎉 Готово! Бот работает на Google Cloud Functions!"