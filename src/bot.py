import os
import logging
from typing import Optional, Dict, List
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import Config
# Импорты AI клиентов будут выполняться лениво при необходимости
from .knowledge_manager import KnowledgeManager
from .prompt_manager import PromptManager
from .user_manager import UserManager
from .utils import setup_logging, get_user_identifier, format_user_message

logger = logging.getLogger(__name__)


class AssistantBot:
    """Основной класс Telegram бота-ассистента"""

    def __init__(self):
        # Настройка логирования
        self.logger = setup_logging()

        # Проверка конфигурации
        if not Config.validate():
            raise ValueError("Ошибка конфигурации. Проверьте переменные окружения.")

        # Инициализация AI клиента с fallback логикой
        self.ai_client = self._initialize_ai_client()
        
        # Инициализация остальных компонентов
        self.knowledge_manager = KnowledgeManager(Config.KNOWLEDGE_BASE_DIR)
        self.prompt_manager = PromptManager(Config.PROMPTS_DIR)
        self.user_manager = UserManager(Config.FIRESTORE_PROJECT_ID)

        # Создание приложения
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Регистрация обработчиков
        self._register_handlers()

        self._application_initialized = False

        logger.info("Бот инициализирован успешно (Application будет инициализирован при первом использовании)")

    async def ensure_initialized(self):
        """Инициализация Application для webhook режима"""
        if not self._application_initialized:
            await self.application.initialize()
            self._application_initialized = True
            logger.info("Telegram Application инициализирован")

    def _initialize_ai_client(self):
        """Инициализация AI клиента с приоритетом: Groq > Gemini > OpenAI"""
        logger.info("=== Инициализация AI клиента ===")
        logger.info(f"GROQ_API_KEY: {'✅ задан' if Config.GROQ_API_KEY and Config.GROQ_API_KEY != 'gsk_your_key_here' else '❌ не задан'}")
        logger.info(f"GOOGLE_API_KEY: {'✅ задан' if Config.GOOGLE_API_KEY else '❌ не задан'}")
        logger.info(f"OPENAI_API_KEY: {'✅ задан' if Config.OPENAI_API_KEY else '❌ не задан'}")
        
        # Try Groq first (free, fast)
        if Config.GROQ_API_KEY and Config.GROQ_API_KEY != 'gsk_your_key_here':
            try:
                logger.info("Попытка инициализации Groq клиента...")
                from .groq_client import GroqClient
                client = GroqClient(Config.GROQ_API_KEY)
                logger.info(f"✅ Используется Groq с моделью: {Config.GROQ_MODEL}")
                return client
            except Exception as e:
                logger.error(f"❌ Groq клиент не удалось инициализировать: {e}", exc_info=True)
        
        # Try Gemini next
        if Config.GOOGLE_API_KEY:
            try:
                logger.info("Попытка инициализации Gemini клиента...")
                from .gemini_client import GeminiClient
                client = GeminiClient(Config.GOOGLE_API_KEY)
                logger.info(f"✅ Используется Gemini с моделью: {Config.GEMINI_MODEL}")
                return client
            except Exception as e:
                logger.error(f"❌ Gemini клиент не удалось инициализировать: {e}", exc_info=True)
        
        # Try OpenAI as last resort
        if Config.OPENAI_API_KEY:
            try:
                logger.info("Попытка инициализации OpenAI клиента...")
                from .openai_client import OpenAIClient
                client = OpenAIClient(Config.OPENAI_API_KEY)
                logger.info(f"✅ Используется OpenAI с моделью: {Config.OPENAI_MODEL}")
                return client
            except Exception as e:
                logger.error(f"❌ OpenAI клиент не удалось инициализировать: {e}", exc_info=True)
        
        logger.error("❌ Не удалось инициализировать ни один AI клиент!")
        raise ValueError("Не удалось инициализировать ни один AI клиент. Проверьте API ключи.")

    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("language", self.language_command))

        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))

    # ========== Вспомогательные методы ==========

    def _get_main_menu_keyboard(self, language: str) -> ReplyKeyboardMarkup:
        """Создание клавиатуры главного меню"""
        buttons = {
            'uz': [
                ["🆘 Yordam", "🌐 Tilni o'zgartirish"],
                ["ℹ️ Bot haqida"]
            ],
            'ru': [
                ["🆘 Помощь", "🌐 Сменить язык"],
                ["ℹ️ О боте"]
            ],
            'en': [
                ["🆘 Help", "🌐 Change language"],
                ["ℹ️ About"]
            ]
        }

        keyboard = buttons.get(language, buttons['uz'])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    def _get_user_language(self, update: Update) -> str:
        user_id = get_user_identifier(update)
        return self.user_manager.get_language(user_id)

    def _get_user_name(self, update: Update) -> str:
        user = update.effective_user
        return user.first_name or user.username or "Пользователь"

    def _get_localized_text(self, update: Update, key: str, default: str = None) -> str:
        """Получение локализованного текста"""
        lang = self._get_user_language(update)
        texts = {
            'uz': {
                'start_unknown': "Assalomu alaykum! Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.",
                'start_registered': "Assalomu alaykum, {name}! Botimizga xush kelibsiz.",
                'help': "Yordam\n\nSavolingizni yozing, men sizga Xitoy bilan savdo qilish bo'yicha maslahat beraman.",
                'not_registered': "Iltimos, avval ro'yxatdan o'ting: /start",
                'error': "Kechirasiz, xatolik yuz berdi.",
                'about': "AI yordamchi - Xitoy bilan savdo bo'yicha maslahatchi\n\nVersiya: 1.0",
                'language_changed': "Til muvaffaqiyatli o'zgartirildi! Endi men sizga o'zbek tilida javob beraman.",
                'select_language': "Tilni tanlang:"
            },
            'ru': {
                'start_unknown': "Здравствуйте! Для использования бота необходимо зарегистрироваться.",
                'start_registered': "Здравствуйте, {name}! Добро пожаловать в нашего бота.",
                'help': "Помощь\n\nНапишите свой вопрос, я помогу с консультацией по торговле с Китаем.",
                'not_registered': "Пожалуйста, сначала зарегистрируйтесь: /start",
                'error': "Извините, произошла ошибка.",
                'about': "AI помощник - консультант по торговле с Китаем\n\nВерсия: 1.0",
                'language_changed': "Язык успешно изменен! Теперь я буду отвечать вам на русском языке.",
                'select_language': "Выберите язык:"
            },
            'en': {
                'start_unknown': "Hello! You need to register to use the bot.",
                'start_registered': "Hello, {name}! Welcome to our bot.",
                'help': "Help\n\nWrite your question, I'll help with consulting on trading with China.",
                'not_registered': "Please register first: /start",
                'error': "Sorry, an error occurred.",
                'about': "AI assistant - consultant on trading with China\n\nVersion: 1.0",
                'language_changed': "Language successfully changed! I will now respond to you in English.",
                'select_language': "Select language:"
            }
        }
        if default is None:
            default = key
        return texts.get(lang, texts['uz']).get(key, default)

    async def _send_message_with_menu(self, chat_id: int, text: str, language: str,
                                      reply_markup: ReplyKeyboardMarkup = None):
        """Отправка сообщения с клавиатурой меню"""
        if reply_markup is None:
            reply_markup = self._get_main_menu_keyboard(language)
        # Преобразуем Markdown в HTML и устанавливаем parse_mode
        from .utils import markdown_to_html
        formatted_text = markdown_to_html(text)
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=formatted_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    # ========== Обработчики команд ==========

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = get_user_identifier(update)

        if not self.user_manager.is_registered(user_id):
            await self._show_language_selection(update, context, is_registration=True)
        else:
            lang = self.user_manager.get_language(user_id)
            name = self._get_user_name(update)
            text = self._get_localized_text(update, 'start_registered').format(name=name)
            await self._send_message_with_menu(update.effective_chat.id, text, lang)

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для смены языка"""
        user_id = get_user_identifier(update)

        if not self.user_manager.is_registered(user_id):
            await update.message.reply_text(self._get_localized_text(update, 'not_registered'))
            return

        await self._show_language_selection(update, context, is_registration=False)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = get_user_identifier(update)
        if not self.user_manager.is_registered(user_id):
            await update.message.reply_text(self._get_localized_text(update, 'not_registered'))
            return

        language = self.user_manager.get_language(user_id)
        help_text = self._get_localized_text(update, 'help')
        await self._send_message_with_menu(update.effective_chat.id, help_text, language)

    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка кнопки О боте"""
        user_id = get_user_identifier(update)
        if not self.user_manager.is_registered(user_id):
            await update.message.reply_text(self._get_localized_text(update, 'not_registered'))
            return

        language = self.user_manager.get_language(user_id)
        about_text = self._get_localized_text(update, 'about')
        await self._send_message_with_menu(update.effective_chat.id, about_text, language)

    async def _show_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       is_registration: bool = True):
        """Показ выбора языка"""
        keyboard = [
            [InlineKeyboardButton("🇷🇺 Русский", callback_data=f"lang_ru_{'reg' if is_registration else 'change'}")],
            [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data=f"lang_uz_{'reg' if is_registration else 'change'}")],
            [InlineKeyboardButton("🇺🇸 English", callback_data=f"lang_en_{'reg' if is_registration else 'change'}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if is_registration:
            text = "🌐 Iltimos, tilni tanlang / Please select your language / Пожалуйста, выберите язык:"
        else:
            text = self._get_localized_text(update, 'select_language')

        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора языка"""
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        if callback_data.startswith('lang_'):
            parts = callback_data.split('_')
            language = parts[1]
            action = parts[2] if len(parts) > 2 else 'reg'

            user_id = get_user_identifier(update)

            if action == 'change' and self.user_manager.is_registered(user_id):
                success = self.user_manager.set_language(user_id, language)

                if success:
                    # Тексты на каждом языке (правильные)
                    success_texts = {
                        'uz': "✅ Til muvaffaqiyatli o'zgartirildi! Endi men sizga o'zbek tilida javob beraman.",
                        'ru': "✅ Язык успешно изменен! Теперь я буду отвечать вам на русском языке.",
                        'en': "✅ Language successfully changed! I will now respond to you in English."
                    }
                    await query.edit_message_text(success_texts.get(language, success_texts['uz']))

                    # Показываем меню на выбранном языке
                    help_texts = {
                        'uz': "Yordam\n\nSavolingizni yozing, men sizga Xitoy bilan savdo qilish bo'yicha maslahat beraman.",
                        'ru': "Помощь\n\nНапишите свой вопрос, я помогу с консультацией по торговле с Китаем.",
                        'en': "Help\n\nWrite your question, I'll help with consulting on trading with China."
                    }
                    await self._send_message_with_menu(
                        query.message.chat_id,
                        help_texts.get(language, help_texts['uz']),
                        language
                    )
                else:
                    error_texts = {
                        'uz': "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
                        'ru': "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                        'en': "❌ An error occurred. Please try again."
                    }
                    await query.edit_message_text(error_texts.get(language, error_texts['uz']))

            elif action == 'reg':
                context.user_data['selected_language'] = language
                await query.edit_message_reply_markup(reply_markup=None)
                await self._request_phone_number(update, context)

    async def _request_phone_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запрос номера телефона"""
        language = context.user_data.get('selected_language', 'uz')
        display_name = self._get_user_name(update)

        button_texts = {
            'uz': "📱 Telefon raqamni ulashish",
            'ru': "📱 Поделиться номером телефона",
            'en': "📱 Share phone number"
        }

        message_texts = {
            'uz': f"{display_name}, iltimos, quyidagi tugmani bosib telefon raqamingizni ulashing:",
            'ru': f"{display_name}, пожалуйста, нажмите кнопку ниже, чтобы поделиться номером телефона:",
            'en': f"{display_name}, please press the button below to share your phone number:"
        }

        button = KeyboardButton(
            text=button_texts.get(language, button_texts['uz']),
            request_contact=True
        )
        keyboard = [[button]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.callback_query.message.reply_text(
            text=message_texts.get(language, message_texts['uz']),
            reply_markup=reply_markup
        )

    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка полученного номера телефона"""
        user_id = get_user_identifier(update)
        contact = update.message.contact
        phone_number = contact.phone_number

        language = context.user_data.get('selected_language', 'uz')

        success = self.user_manager.create_user(
            user_id=user_id,
            phone_number=phone_number,
            language=language
        )

        if success:
            context.user_data.clear()
            display_name = self._get_user_name(update)

            texts = {
                'uz': f"✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n\nXush kelibsiz, {display_name}!",
                'ru': f"✅ Вы успешно зарегистрированы!\n\nДобро пожаловать, {display_name}!",
                'en': f"✅ You have been successfully registered!\n\nWelcome, {display_name}!"
            }

            await update.message.reply_text(
                texts.get(language, texts['uz']),
                reply_markup=ReplyKeyboardRemove()
            )

            help_texts = {
                'uz': "Yordam\n\nSavolingizni yozing, men sizga Xitoy bilan savdo qilish bo'yicha maslahat beraman.",
                'ru': "Помощь\n\nНапишите свой вопрос, я помогу с консультацией по торговле с Китаем.",
                'en': "Help\n\nWrite your question, I'll help with consulting on trading with China."
            }
            await self._send_message_with_menu(
                update.effective_chat.id,
                help_texts.get(language, help_texts['uz']),
                language
            )
        else:
            error_texts = {
                'uz': "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
                'ru': "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз.",
                'en': "❌ An error occurred. Please try again."
            }
            await update.message.reply_text(error_texts.get(language, error_texts['uz']))

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        start_time = datetime.now()
        user_id = get_user_identifier(update)
        user_message = format_user_message(update.message.text)
        
        logger.info(f"[{user_id}] Получено сообщение: {user_message[:100]}...")

        # Обработка кнопок меню
        if self.user_manager.is_registered(user_id):
            language = self.user_manager.get_language(user_id)
            logger.debug(f"[{user_id}] Пользователь зарегистрирован, язык: {language}")
        else:
            language = 'uz'
            logger.debug(f"[{user_id}] Пользователь не зарегистрирован, язык по умолчанию: uz")

        button_handlers = {
            'uz': {
                "🆘 Yordam": self.help_command,
                "🌐 Tilni o'zgartirish": self.language_command,
                "ℹ️ Bot haqida": self.about_command
            },
            'ru': {
                "🆘 Помощь": self.help_command,
                "🌐 Сменить язык": self.language_command,
                "ℹ️ О боте": self.about_command
            },
            'en': {
                "🆘 Help": self.help_command,
                "🌐 Change language": self.language_command,
                "ℹ️ About": self.about_command
            }
        }

        # Проверяем, не является ли сообщение нажатием кнопки меню
        handler = button_handlers.get(language, button_handlers['uz']).get(user_message)
        if handler:
            logger.info(f"[{user_id}] Обнаружена кнопка меню: {user_message}")
            await handler(update, context)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{user_id}] Обработка кнопки меню завершена за {elapsed:.2f}с")
            return

        if not self.user_manager.is_registered(user_id):
            logger.warning(f"[{user_id}] Пользователь не зарегистрирован, отправка сообщения о регистрации")
            await update.message.reply_text(self._get_localized_text(update, 'not_registered'))
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{user_id}] Обработка завершена (не зарегистрирован) за {elapsed:.2f}с")
            return

        # Проверяем, относится ли сообщение к теме закупок из Китая
        logger.debug(f"[{user_id}] Проверка релевантности темы...")
        is_relevant = self._is_topic_relevant(user_message)
        logger.debug(f"[{user_id}] Результат проверки релевантности: {is_relevant}")
        
        if not is_relevant:
            logger.info(f"[{user_id}] Тема нерелевантна, отправка сообщения о выходе за тему")
            off_topic_messages = {
                'uz': "Kechirasiz, men faqat Xitoydan xarid qilish bilan bog'liq masalalarda yordam bera olaman. Sizning savolingiz bu mavzuga tegishli emas. Agar Xitoy bilan savdo haqida savolingiz bo'lsa, menga murojaat qiling!",
                'ru': "Извините, я могу помогать только по вопросам закупок из Китая. Ваш вопрос не относится к этой теме. Если у вас есть вопросы о торговле с Китаем, обращайтесь!",
                'en': "Sorry, I can only assist with questions related to procurement from China. Your question is not related to this topic. If you have questions about trade with China, feel free to ask!"
            }
            await update.message.reply_text(off_topic_messages.get(language, off_topic_messages['uz']))
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{user_id}] Обработка завершена (нерелевантная тема) за {elapsed:.2f}с")
            return

        # Показываем статус "печатает"
        logger.debug(f"[{user_id}] Отправка статуса 'печатает'...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        try:
            logger.info(f"[{user_id}] Начало генерации ответа AI...")
            
            # Получаем контекст из базы знаний
            knowledge_context = self.knowledge_manager.get_context_for_query(user_message)
            knowledge_len = len(knowledge_context) if knowledge_context else 0
            logger.debug(f"[{user_id}] Получен контекст из базы знаний ({knowledge_len} символов)")

            # Ищем подходящий промт
            prompt_text = None
            prompts = self.prompt_manager.get_all_prompts()
            logger.debug(f"[{user_id}] Доступно промтов: {len(prompts)}")
            
            for p in prompts:
                if p['name'].lower() in user_message.lower() or len(prompts) == 1:
                    prompt_text = self.prompt_manager.get_prompt(p['name'])
                    logger.debug(f"[{user_id}] Используется промт: {p['name']}")
                    break

            # Формируем системный промт
            system_prompt = Config.SYSTEM_PROMPTS.get(language, Config.SYSTEM_PROMPTS['uz'])
            system_prompt_len = len(system_prompt) if system_prompt else 0
            logger.debug(f"[{user_id}] Системный промт загружен ({system_prompt_len} символов)")

            # Получаем историю
            history = context.user_data.get('chat_history', [])
            history_len = len(history) if history else 0
            logger.debug(f"[{user_id}] История чата: {history_len} сообщений")

            # Генерируем ответ через AI клиента (Groq/Gemini/OpenAI)
            ai_start = datetime.now()
            if prompt_text:
                logger.info(f"[{user_id}] Генерация ответа с промтом...")
                response = self.ai_client.generate_response_with_prompt_template(
                    user_query=user_message,
                    prompt_template=prompt_text,
                    context=knowledge_context,
                    language=language
                )
            else:
                logger.info(f"[{user_id}] Генерация ответа с контекстом...")
                response = self.ai_client.chat_with_context(
                    user_message,
                    system_prompt,
                    knowledge_context,
                    history[-5:] if history else None,
                    language
                )
            
            ai_elapsed = (datetime.now() - ai_start).total_seconds()
            response_len = len(response) if response else 0
            logger.info(f"[{user_id}] Ответ сгенерирован за {ai_elapsed:.2f}с ({response_len} символов)")

            # Сохраняем в историю
            if 'chat_history' not in context.user_data:
                context.user_data['chat_history'] = []
                logger.debug(f"[{user_id}] Создана новая история чата")

            context.user_data['chat_history'].append({'role': 'user', 'content': user_message})
            context.user_data['chat_history'].append({'role': 'assistant', 'content': response})

            if len(context.user_data['chat_history']) > 20:
                context.user_data['chat_history'] = context.user_data['chat_history'][-20:]
                logger.debug(f"[{user_id}] История обрезана до 20 сообщений")

            # Отправляем ответ с меню
            logger.info(f"[{user_id}] Отправка ответа пользователю...")
            await self._send_message_with_menu(update.effective_chat.id, response, language)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{user_id}] Обработка сообщения завершена за {elapsed:.2f}с")

        except Exception as e:
            logger.error(f"[{user_id}] Ошибка обработки сообщения: {e}", exc_info=True)
            error_messages = {
                'uz': "Kechirasiz, texnik xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
                'ru': "Извините, произошла техническая ошибка. Пожалуйста, попробуйте позже.",
                'en': "Sorry, a technical error occurred. Please try again later."
            }
            try:
                await self._send_message_with_menu(
                    update.effective_chat.id,
                    error_messages.get(language, error_messages['uz']),
                    language
                )
            except Exception as send_error:
                logger.error(f"[{user_id}] Не удалось отправить сообщение об ошибке: {send_error}", exc_info=True)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"[{user_id}] Обработка завершена с ошибкой за {elapsed:.2f}с")

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка inline кнопок"""
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        if callback_data.startswith('lang_'):
            await self.handle_language_selection(update, context)

    def _is_topic_relevant(self, message: str) -> bool:
        """Проверка, относится ли сообщение к теме закупок из Китая"""
        message_lower = message.lower()
        
        logger.debug(f"Проверка релевантности сообщения: '{message[:50]}...'")

        # Сначала проверяем базовые вопросы о боте - они всегда релевантны
        basic_questions_ru = [
            'кто ты', 'что ты', 'как тебя зовут', 'твоё имя', 'имя',
            'что умеешь', 'чем можешь помочь', 'как ты можешь помочь',
            'как купить', 'как заказать', 'как сделать заказ',
            'помощь', 'help', 'что ты можешь', 'твои возможности',
            'что ты знаешь', 'какие есть', 'расскажи о себе', 'кто ты',
            'как работает', 'как пользоваться', 'инструкция'
        ]
        
        for phrase in basic_questions_ru:
            if phrase in message_lower:
                logger.info(f"✅ Обнаружен базовый вопрос (релевантен): '{phrase}'")
                return True

        # Ключевые слова на русском (основная тема)
        ru_keywords = [
            'китай', 'китай', 'china', 'chinese',
            'закупк', 'покупк', 'поставк', 'импорт', 'экспорт',
            'торговл', 'бизнес', 'сайт', 'магазин', 'alibaba', 'aliexpress',
            '1688', 'taobao', 'jd', 'pinduoduo',
            'логистик', 'доставк', 'таможен', 'растаможив',
            'проверк', 'верификац', 'компан', 'поставщик', 'производител',
            'завод', 'фабрик', 'опт', 'оптов',
            'переговор', 'договариван', 'оплат', 'платеж',
            'качеств', 'контрол', 'инспекц', 'образец',
            'упаковк', 'маркировк', 'сертификат',
            'документ', 'инвойс', 'счет', 'контракт',
            'деньг', 'срок', 'гарант', 'возврат',
            'упаковк', 'фрахт', 'incoterms',
            'дд', 'дду', 'fob', 'cif', 'exw',
            'yuan', 'доллар', 'юан', 'валют',
            'банк', 'карт', 'перевод', 'western union',
            'транспорт', 'авиа', 'море', 'ж/д', 'авто',
            'склад', 'сг', 'бонд', 'пост',
            'агент', 'брокер', 'посредник',
            'образец', 'sample', 'прототип',
            'минимум', 'мооп', 'моп', 'шт', 'штук',
            'цена', 'стоимост', 'расцен', 'тариф',
            'срок', 'врем', 'дата', 'дедлайн',
            'гарант', 'warranty', 'возврат', 'refund',
            'alipay', 'wechat', 'weixin', 'qq', 'регистрац', 'аккаунт',
            'верификац', 'подтвержден', 'идентификац', 'проверка'
        ]

        # Ключевые слова на узбекском
        uz_keywords = [
            'xitoy', 'xarid', 'sotib', 'olish',
            'yetkazib', 'berish', 'logistika', 'tashish',
            'bojxona', 'rasmiylashtirish', 'tekshirish',
            'kompaniya', 'tashkilot', 'ishlab', 'chiqarish',
            'zavod', 'fabrika', 'optovik', 'optom',
            'muzokara', 'kelishuv', 'to\'lov', 'pul',
            'sifat', 'nazorat', 'namunalar', 'sample',
            'hujjat', 'invoice', 'hisob', 'shartnoma',
            'pul', 'valyuta', 'yuan', 'dollar',
            'bank', 'karta', 'transfer', 'chegirma',
            'transport', 'avia', 'dengiz', 'temir', 'yo\'l',
            'ombor', 'sklad', 'baza',
            'agent', 'broker', 'vositachi',
            'narx', 'bahosi', 'qiymat', 'tarif',
            'muddat', 'vaqt', 'sana', 'chegarasi',
            'kafolat', 'qaytarish', 'return',
            'alipay', 'wechat', 'weixin', 'qq', 'royxatdan', 'hisob'
        ]

        # Ключевые слова на английском
        en_keywords = [
            'china', 'chinese', 'procurement', 'purchase', 'buy', 'sourcing',
            'supplier', 'manufacturer', 'factory', 'wholesale',
            'shipping', 'delivery', 'logistics', 'freight',
            'customs', 'clearance', 'documentation',
            'verification', 'check', 'audit', 'due diligence',
            'negotiation', 'contract', 'agreement',
            'payment', 'pay', 'transfer', 'wire',
            'quality', 'control', 'inspection', 'qc',
            'sample', 'prototype', 'testing',
            'certificate', 'certification', 'iso',
            'incoterms', 'fob', 'cif', 'exw', 'dap', 'ddu',
            'currency', 'usd', 'cny', 'rmb', 'yuan',
            'bank', 'letter', 'l/c', 'lc',
            'agent', 'broker', 'forwarder',
            'price', 'cost', 'quotation', 'quote',
            'lead time', 'timeline', 'deadline',
            'warranty', 'guarantee', 'refund', 'return',
            'packaging', 'labeling', 'marking',
            'alibaba', 'aliexpress', '1688', 'taobao', 'jd',
            'made-in-china', 'global sources',
            'alipay', 'wechat', 'weixin', 'qq', 'register', 'account',
            'verification', 'confirm', 'identity', 'check'
        ]

        # Проверяем наличие ключевых слов
        all_keywords = ru_keywords + uz_keywords + en_keywords
        
        found_keywords = []
        for keyword in all_keywords:
            if keyword in message_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            logger.debug(f"Найдены ключевые слова: {found_keywords[:10]}")  # Log first 10
            return True

        # Дополнительная проверка: если сообщение слишком короткое (менее 3 символов) или содержит только эмодзи/знаки препинания
        stripped_len = len(message_lower.strip(' .,!?;:()[]{}«»"\'\\|/@#$%^&*~`+-=<>'))
        if stripped_len < 3:
            logger.debug(f"Сообщение слишком короткое после stripping: {stripped_len} символов")
            return False

        # Если ни одно ключевое слово не найдено, считаем тему нерелевантной
        logger.warning(f"⚠️ Тема нерелевантна, нет ключевых слов: '{message[:50]}...'")
        return False

    def run(self):
        logger.info("Запуск бота...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    def get_application(self):
        return self.application