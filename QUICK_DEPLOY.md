# 🚀 Быстрый старт: Деплой на Railway (рекомендуется)

## За 5 минут:

### 1. Подготовка
Убедитесь, что у вас есть:
- ✅ Telegram Bot Token от @BotFather
- ✅ API ключ Gemini от [Google AI Studio](https://makersuite.google.com/app/apikey) (бесплатно)

### 2. Загрузка на GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 3. Деплой на Railway
1. Зайдите на [railway.app](https://railway.app) и авторизуйтесь через GitHub
2. Нажмите **"New Project"** → **"Deploy from GitHub repo"**
3. Выберите ваш репозиторий
4. Railway автоматически обнаружит `railway.json` и начнет деплой

### 4. Настройка переменных окружения
После создания проекта:
1. Перейдите в **Dashboard** вашего проекта
2. **Variables** → **Add Variable**
3. Добавьте:
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен_бота
   GOOGLE_API_KEY=ваш_ключ_gemini
   ```
4. Нажмите **"Save"**

### 5. Установка Webhook
После успешного деплоя:
1. Скопируйте URL вашего сервиса (например: `https://your-project.up.railway.app`)
2. Откройте терминал и выполните:
```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-project.up.railway.app"
```
Замените `<YOUR_BOT_TOKEN>` на ваш токен и URL на ваш Railway URL.

### 6. Проверка
1. Отправьте сообщение вашему боту в Telegram
2. Проверьте логи в Railway Dashboard → Logs
3. Бот должен ответить!

---

## 📊 Сравнение хостингов

| Характеристика | Railway | Render | Cloud Functions |
|----------------|---------|--------|-----------------|
| **Бесплатно** | 500 часов/мес | 750 часов/мес | 2 млн вызовов/мес |
| **Автостоп** | Нет | Да (после 15 мин) | Да (между вызовами) |
| **Простота** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Холодный старт** | ~5-10 сек | ~10-15 сек | ~1-5 сек |
| **Webhook** | ✅ Да | ✅ Да | ✅ Да |
| **Документация** | [Docs](https://docs.railway.app/) | [Docs](https://render.com/docs) | [Docs](https://cloud.google.com/functions/docs) |

**Рекомендация:** Railway - лучший баланс простоты и надежности.

---

## 🔧 Если что-то не работает

### Проверьте логи
- **Railway**: Dashboard → Logs
- **Render**: Dashboard → Logs
- **Cloud Functions**: `gcloud functions logs read`

### Распространенные проблемы

1. **"Bot token is invalid"**
   - Проверьте `TELEGRAM_BOT_TOKEN` в переменных окружения
   - Убедитесь, что токен от @BotFather

2. **"No AI client initialized"**
   - Добавьте `GOOGLE_API_KEY` или `GROQ_API_KEY`
   - Проверьте, что ключ действителен

3. **Webhook не устанавливается**
   - Убедитесь, что URL правильный
   - Проверьте, что бот запущен
   - Удалите старый webhook: `setWebhook?url=""` перед установкой нового

4. **Бот не отвечает после сна**
   - Это нормально для бесплатных хостингов
   - Первый запрос будет медленным (холодный старт)
   - Если проблема длится >30 сек, проверьте логи

---

## 💡 Советы

1. **Используйте Firebase** для хранения пользователей:
   - Локальный файл `users_local.json` не работает на нескольких инстансах
   - Настройте Firebase Firestore (инструкция в `DEPLOY.md`)

2. **Мониторинг**:
   - Railway/Render показывают использование ресурсов
   - Настройте уведомления о падении сервиса

3. **Резервное копирование**:
   - Регулярно экспортируйте данные из Firestore
   - Или настройте автоматический бэкап

4. **Обновления**:
   - Railway/Render автоматически деплоят при пуше в main
   - Для Cloud Functions запускайте `./deploy.sh`

---

## 📚 Подробная документация

Смотрите `DEPLOY.md` для:
- Подробных инструкций по каждому хостингу
- Настройки Firebase
- Устранения неполадок
- Миграции данных

---

**Удачи!** 🎉