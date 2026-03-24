#!/usr/bin/env python3
"""
Скрипт для установки webhook после деплоя
"""
import os
import sys
import requests

def set_webhook(bot_token: str, webhook_url: str):
    """Установка webhook для Telegram бота"""
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    params = {"url": webhook_url}

    response = requests.post(url, json=params)
    data = response.json()

    if data.get("ok"):
        print("✅ Webhook успешно установлен!")
        print(f"   URL: {webhook_url}")
    else:
        print("❌ Ошибка установки webhook:")
        print(f"   {data.get('description')}")

    # Проверяем статус
    info_response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
    info = info_response.json()
    print("\n📊 Текущая информация:")
    print(f"   URL: {info['result'].get('url', 'Не установлен')}")
    print(f"   Ожидающие обновления: {info['result'].get('pending_update_count', 0)}")
    print(f"   Последняя ошибка: {info['result'].get('last_error_message', 'Нет')}")

if __name__ == "__main__":
    print("🔧 Настройка Telegram Webhook\n")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or input("Введите TELEGRAM_BOT_TOKEN: ").strip()
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN обязателен")
        sys.exit(1)

    print("\nВыберите хостинг:")
    print("1. Railway")
    print("2. Render")
    print("3. Google Cloud Functions")
    print("4. Другой (ввести URL вручную)")

    choice = input("\nВаш выбор (1-4): ").strip()

    webhook_url = None

    if choice == "1":
        project_name = input("Введите имя проекта Railway: ").strip()
        webhook_url = f"https://{project_name}.up.railway.app"
    elif choice == "2":
        service_name = input("Введите имя сервиса Render: ").strip()
        webhook_url = f"https://{service_name}.onrender.com"
    elif choice == "3":
        region = input("Введите region (например, us-central1): ").strip() or "us-central1"
        function_name = input("Введите имя функции: ").strip()
        webhook_url = f"https://{region}-{function_name}.cloudfunctions.net"
    elif choice == "4":
        webhook_url = input("Введите полный URL webhook: ").strip()
    else:
        print("Неверный выбор")
        sys.exit(1)

    if webhook_url:
        set_webhook(bot_token, webhook_url)