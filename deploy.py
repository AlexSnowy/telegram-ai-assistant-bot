#!/usr/bin/env python3
"""
Автоматический деплой Telegram бота на бесплатный хостинг
Поддерживает: Railway, Render, Google Cloud Functions
"""

import os
import sys
import json
import subprocess
import webbrowser
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def run_command(cmd, cwd=None, capture_output=True):
    """Выполнение команды с выводом"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=capture_output,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if capture_output:
            return result.returncode == 0, result.stdout, result.stderr
        return result.returncode == 0, None, None
    except Exception as e:
        return False, None, str(e)

def check_command(cmd):
    """Проверка наличия команды"""
    success, _, _ = run_command(f"where {cmd}" if sys.platform == "win32" else f"which {cmd}")
    return success

def check_git():
    """Проверка Git"""
    if not check_command("git"):
        print_error("Git не установлен. Установите с https://git-scm.com/")
        return False
    print_success("Git найден")
    return True

def check_python():
    """Проверка Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Требуется Python 3.8+, у вас {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor} найден")
    return True

def get_input(prompt, default=None, password=False):
    """Безопасный ввод с возможностью значения по умолчанию"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    if password:
        try:
            import getpass
            value = getpass.getpass(full_prompt)
        except:
            value = input(full_prompt)
    else:
        value = input(full_prompt)

    return value if value else default

def confirm(question, default=True):
    """Подтверждение действия"""
    suffix = " [Y/n]: " if default else " [y/N]: "
    answer = input(f"{question}{suffix}").strip().lower()
    if not answer:
        return default
    return answer in ['y', 'yes', 'д', 'да']

def setup_git():
    """Настройка Git и отправка на GitHub"""
    print_header("Настройка Git")

    if not check_git():
        return False

    # Проверяем, инициализирован ли репозиторий
    success, stdout, _ = run_command("git status")
    if not success:
        print_warning("Git репозиторий не инициализирован")
        if confirm("Инициализировать git репозиторий?"):
            run_command("git init", capture_output=False)
            print_success("Git инициализирован")
        else:
            return False
    else:
        print_info("Git репозиторий уже инициализирован")

    # Настройка пользователя (если не настроен)
    success, stdout, _ = run_command("git config user.name")
    if not success or not stdout.strip():
        name = get_input("Введите ваше имя для Git", "Deployer")
        run_command(f'git config user.name "{name}"', capture_output=False)
        print_success(f"Установлено имя Git: {name}")

    success, stdout, _ = run_command("git config user.email")
    if not success or not stdout.strip():
        email = get_input("Введите email для Git", "deploy@example.com")
        run_command(f'git config user.email "{email}"', capture_output=False)
        print_success(f"Установлен email Git: {email}")

    # Добавление удаленного репозитория
    github_url = get_input("Введите URL GitHub репозитория (или нажмите Enter чтобы создать новый)",
                          "https://github.com/username/repo.git")

    if github_url and github_url != "https://github.com/username/repo.git":
        # Проверяем, есть ли уже удаленный репозиторий
        success, stdout, _ = run_command("git remote -v")
        if "origin" not in stdout:
            run_command(f'git remote add origin "{github_url}"', capture_output=False)
            print_success(f"Добавлен удаленный репозиторий: {github_url}")
        else:
            print_info("Удаленный репозиторий 'origin' уже существует")
            if confirm("Перезаписать удаленный репозиторий?"):
                run_command('git remote remove origin', capture_output=False)
                run_command(f'git remote add origin "{github_url}"', capture_output=False)
                print_success("Удаленный репозиторий обновлен")

    # Коммит и пушим
    print_info("Добавление файлов в git...")
    run_command("git add .", capture_output=False)

    print_info("Создание коммита...")
    run_command('git commit -m "Deploy to free hosting"', capture_output=False)

    print_info("Отправка на GitHub...")
    success, stdout, stderr = run_command("git push -u origin main")

    if success:
        print_success("Код отправлен на GitHub")
    else:
        print_error(f"Ошибка при отправке: {stderr}")
        print_warning("Возможно, нужно аутентифицироваться в GitHub")
        print_info("Попробуйте выполнить вручную: git push -u origin main")
        return False

    return True

def deploy_railway():
    """Деплой на Railway"""
    print_header("Деплой на Railway")

    print_info("1. Открываю Railway.app...")
    print_warning("Вам нужно:")
    print("   - Авторизоваться через GitHub")
    print("   - Выбрать репозиторий с ботом")
    print("   - Настроить переменные окружения")
    print()

    if confirm("Открыть Railway в браузере?"):
        webbrowser.open("https://railway.app")
        input("\nПосле создания проекта нажмите Enter чтобы продолжить...")

    print_info("\n2. Настройка переменных окружения на Railway:")
    print("   В Dashboard вашего проекта → Variables → Add Variable")
    print()

    bot_token = get_input("Введите TELEGRAM_BOT_TOKEN", password=True)
    google_key = get_input("Введите GOOGLE_API_KEY (рекомендуется)", password=True)
    groq_key = get_input("Введите GROQ_API_KEY (опционально)", password=True)
    openai_key = get_input("Введите OPENAI_API_KEY (опционально)", password=True)

    print_info("\nДобавьте эти переменные на Railway:")
    print(f"   TELEGRAM_BOT_TOKEN={bot_token or 'ВАШ_ТОКЕН'}")
    print(f"   GOOGLE_API_KEY={google_key or 'ВАШ_КЛЮЧ'}")
    if groq_key:
        print(f"   GROQ_API_KEY={groq_key}")
    if openai_key:
        print(f"   OPENAI_API_KEY={openai_key}")

    print_success("\n✅ Railway конфигурация готова!")
    print_info("\nСледующие шаги:")
    print("   1. Дождитесь завершения деплоя в Railway")
    print("   2. Скопируйте URL вашего сервиса (например: https://xxx.up.railway.app)")
    print("   3. Установите webhook:")
    print(f"      curl -X POST \"https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=<ВАШ_URL>\"")

    return True

def deploy_render():
    """Деплой на Render"""
    print_header("Деплой на Render")

    print_info("1. Открываю Render.com...")
    print_warning("Вам нужно:")
    print("   - Создать новый Web Service")
    print("   - Подключить GitHub репозиторий")
    print("   - Настроить переменные окружения")
    print()

    if confirm("Открыть Render в браузере?"):
        webbrowser.open("https://render.com")
        input("\nПосле создания сервиса нажмите Enter чтобы продолжить...")

    print_info("\n2. Настройка Web Service на Render:")
    print("   - Name: telegram-ai-assistant")
    print("   - Environment: Python 3")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: python main.py")
    print("   - Plan: Free")
    print()

    bot_token = get_input("Введите TELEGRAM_BOT_TOKEN", password=True)
    google_key = get_input("Введите GOOGLE_API_KEY (рекомендуется)", password=True)
    groq_key = get_input("Введите GROQ_API_KEY (опционально)", password=True)
    openai_key = get_input("Введите OPENAI_API_KEY (опционально)", password=True)

    print_info("\nДобавьте Environment Variables в Render:")
    print(f"   TELEGRAM_BOT_TOKEN={bot_token or 'ВАШ_ТОКЕН'}")
    print(f"   GOOGLE_API_KEY={google_key or 'ВАШ_КЛЮЧ'}")
    if groq_key:
        print(f"   GROQ_API_KEY={groq_key}")
    if openai_key:
        print(f"   OPENAI_API_KEY={openai_key}")

    print_success("\n✅ Render конфигурация готова!")
    print_info("\nСледующие шаги:")
    print("   1. Дождитесь завершения деплоя в Render")
    print("   2. Скопируйте URL вашего сервиса (например: https://xxx.onrender.com)")
    print("   3. Установите webhook:")
    print(f"      curl -X POST \"https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=<ВАШ_URL>\"")

    return True

def deploy_gcloud():
    """Деплой на Google Cloud Functions"""
    print_header("Деплой на Google Cloud Functions")

    print_warning("Требуется установленный Google Cloud SDK")
    print()

    if not check_command("gcloud"):
        print_error("Google Cloud SDK не найден")
        print_info("Установите с https://cloud.google.com/sdk/docs/install")
        if confirm("Продолжить с другими хостингами?"):
            return True
        return False

    print_info("Настройка Google Cloud...")

    # Проверка аутентификации
    print("\n1. Проверка аутентификации...")
    success, stdout, stderr = run_command("gcloud auth list")
    if not success or "ACTIVE" not in stdout:
        print_warning("Необходимо аутентифицироваться")
        print_info("Выполните: gcloud auth login")
        if confirm("Открыть инструкцию?"):
            webbrowser.open("https://cloud.google.com/sdk/docs/install")
        input("После аутентификации нажмите Enter...")
    else:
        print_success("Аутентификация подтверждена")

    # Настройка проекта
    print("\n2. Настройка проекта...")
    project_id = get_input("Введите PROJECT_ID (или нажмите Enter чтобы использовать текущий)")
    if project_id:
        run_command(f'gcloud config set project {project_id}', capture_output=False)
        print_success(f"Проект установлен: {project_id}")
    else:
        success, stdout, _ = run_command("gcloud config get-value project")
        project_id = stdout.strip()
        print_info(f"Используется текущий проект: {project_id}")

    # Включение API
    print("\n3. Включение необходимых API...")
    apis = [
        "cloudfunctions.googleapis.com",
        "firestore.googleapis.com",
        "cloudbuild.googleapis.com"
    ]
    for api in apis:
        print(f"   Включаю {api}...")
        run_command(f"gcloud services enable {api} --project={project_id}", capture_output=False)
    print_success("API включены")

    # Создание Firestore
    print("\n4. Создание Firestore базы данных...")
    run_command(f"gcloud firestore databases create --region=us-central --project={project_id}", capture_output=False)
    print_success("Firestore готов")

    # Настройка переменных окружения
    print("\n5. Настройка переменных окружения...")
    bot_token = get_input("TELEGRAM_BOT_TOKEN", password=True)
    google_key = get_input("GOOGLE_API_KEY", password=True)
    firestore_project = get_input("FIRESTORE_PROJECT_ID", project_id)

    # Создаем .env файл для Cloud Functions
    env_content = f"""TELEGRAM_BOT_TOKEN={bot_token}
GOOGLE_API_KEY={google_key}
FIRESTORE_PROJECT_ID={firestore_project}
"""
    with open(".env.gcloud", "w") as f:
        f.write(env_content)
    print_success("Создан файл .env.gcloud с переменными окружения")

    print_info("\n6. Запуск деплоя...")
    print_warning("Вам нужно будет ввести переменные окружения вручную при деплое")
    print_info("Или используйте скрипт deploy.sh с переменными окружения")

    if confirm("Запустить deploy.sh сейчас?"):
        # Устанавливаем переменные окружения
        os.environ['TELEGRAM_BOT_TOKEN'] = bot_token
        os.environ['GOOGLE_API_KEY'] = google_key
        os.environ['FIRESTORE_PROJECT_ID'] = firestore_project

        success, _, stderr = run_command("chmod +x deploy.sh && ./deploy.sh", capture_output=False)
        if success:
            print_success("Деплой завершен!")
        else:
            print_error(f"Ошибка деплоя: {stderr}")

    return True

def main():
    print_header("🤖 Автоматический деплой Telegram AI Assistant")

    print_info("Этот скрипт поможет развернуть бота на бесплатный хостинг")
    print()

    # Проверки
    if not check_python():
        input("\nНажмите Enter для выхода...")
        return 1

    # Выбор хостинга
    print_header("Выбор хостинга")
    print("Доступные варианты:")
    print("  1. Railway (рекомендуется) - 500 часов/мес, нет автостопа")
    print("  2. Render - 750 часов/мес, простой интерфейс")
    print("  3. Google Cloud Functions - serverless, 2 млн вызовов/мес")
    print("  4. Только подготовить код (ручная настройка)")
    print()

    choice = get_input("Выберите вариант (1-4)", "1")

    # Подготовка кода
    if not os.path.exists("requirements.txt"):
        print_error("Файл requirements.txt не найден!")
        print_info("Убедитесь, что вы запускаете скрипт из корня проекта")
        input("\nНажмите Enter для выхода...")
        return 1

    # Настройка Git
    if not confirm("Настроить Git и отправить код на GitHub?"):
        print_warning("Пропуск настройки Git")
        print_info("Вы можете сделать это вручную:")
        print("   git init")
        print("   git add .")
        print("   git commit -m 'Deploy'")
        print("   git remote add origin <URL>")
        print("   git push -u origin main")
    else:
        if not setup_git():
            print_error("Ошибка настройки Git")
            if not confirm("Продолжить с деплоем?"):
                return 1

    # Деплой в зависимости от выбора
    if choice == "1":
        deploy_railway()
    elif choice == "2":
        deploy_render()
    elif choice == "3":
        deploy_gcloud()
    elif choice == "4":
        print_info("\nФайлы для ручного деплоя готовы:")
        print("  - Procfile (для Railway/Render)")
        print("  - railway.json (для Railway)")
        print("  - render.yaml (для Render)")
        print("  - deploy.sh (для Cloud Functions)")
        print("\nСмотрите DEPLOY.md и QUICK_DEPLOY.md для инструкций")

    print_header("✅ Готово!")
    print_info("Бот подготовлен к развертыванию на бесплатном хостинге")
    print()
    print("📚 Полезные ссылки:")
    print("  - DEPLOY.md - подробное руководство")
    print("  - QUICK_DEPLOY.md - быстрый старт")
    print("  - setup_webhook.py - скрипт для установки webhook")
    print()

    if confirm("Открыть документацию деплоя?"):
        webbrowser.open(f"file://{os.path.abspath('QUICK_DEPLOY.md')}")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)