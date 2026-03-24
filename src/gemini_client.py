import os
import logging
from typing import Optional, Dict, List
from google import genai
from google.genai import types

from config import Config

logger = logging.getLogger(__name__)


class GeminiClient:
    """Клиент для работы с Google Gemini API"""

    ERROR_MESSAGES = {
        'uz': {
            'empty_response': 'Kechirib ko\'ring, menda javob topilmadi.',
            'tech_error': 'Kechirasiz, texnik xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko\'ring.',
            'prompt_error': 'Kechirasiz, texnik xatolik yuz berdi.'
        },
        'ru': {
            'empty_response': 'Попробуйте еще раз, я не нашел ответа.',
            'tech_error': 'Извините, произошла техническая ошибка. Пожалуйста, попробуйте позже.',
            'prompt_error': 'Извините, произошла техническая ошибка.'
        },
        'en': {
            'empty_response': 'Try again, I could not find an answer.',
            'tech_error': 'Sorry, a technical error occurred. Please try again later.',
            'prompt_error': 'Sorry, a technical error occurred.'
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.GOOGLE_API_KEY
        self.model_name = Config.GEMINI_MODEL
        self.temperature = Config.GEMINI_TEMPERATURE
        self.max_output_tokens = Config.GEMINI_MAX_OUTPUT_TOKENS

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY не установлен")

        self.client = genai.Client(api_key=self.api_key)

        self.generation_config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens
        )

        logger.info(f"Gemini клиент инициализирован с моделью: {self.model_name}")

    def generate_response(
            self,
            prompt: str,
            system_instruction: Optional[str] = None,
            context: Optional[str] = None,
            history: Optional[List[Dict]] = None,
            language: str = 'uz'
    ) -> str:
        try:
            # Формируем содержимое запроса
            contents = []

            if system_instruction:
                contents.append(system_instruction)

            if context:
                contents.append(f"Контекст:\n{context}")

            # Добавляем историю, если есть
            if history:
                for msg in history[-10:]:  # Последние 10 сообщений
                    role = "User" if msg.get('role') == 'user' else "Assistant"
                    contents.append(f"{role}: {msg.get('content', '')}")

            # Добавляем текущий запрос
            contents.append(prompt)

            full_prompt = "\n\n".join(contents)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=self.generation_config
            )

            if response.text:
                return response.text.strip()
            else:
                logger.warning("Пустой ответ от Gemini")
                return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['empty_response']

        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['tech_error']

    def generate_response_with_prompt_template(
            self,
            user_query: str,
            prompt_template: str,
            context: Optional[str] = None,
            language: str = 'uz'
    ) -> str:
        try:
            formatted_prompt = prompt_template.replace('{query}', user_query)

            if context and '{context}' in prompt_template:
                formatted_prompt = formatted_prompt.replace('{context}', context)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=formatted_prompt,
                config=self.generation_config
            )

            if response.text:
                return response.text.strip()
            else:
                return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['empty_response']

        except Exception as e:
            logger.error(f"Ошибка генерации ответа с шаблоном: {e}")
            return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['prompt_error']

    def chat_with_context(
            self,
            user_message: str,
            system_prompt: str,
            knowledge_context: str,
            chat_history: List[Dict] = None,
            language: str = 'uz'
    ) -> str:
        try:
            # Формируем полный системный промт с локализованной подсказкой
            context_headers = {
                'uz': "Quyidagi ma'lumotlar asosida javob bering:",
                'ru': "Ответьте, опираясь на следующие данные:",
                'en': "Answer using the following information:"
            }
            header = context_headers.get(language, context_headers['uz'])
            full_system = f"{system_prompt}\n\n{header}\n{knowledge_context}"

            # Создаем чат с конфигурацией
            chat = self.client.chats.create(
                model=self.model_name,
                config=self.generation_config
            )

            # Отправляем системный промт как первое сообщение (role user)
            chat.send_message(full_system)

            # Если есть история, добавляем её
            if chat_history:
                for msg in chat_history[-5:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        chat.send_message(content)
                    # Сообщения ассистента не нужно добавлять, так как они уже в ответах

            # Отправляем текущее сообщение
            response = chat.send_message(user_message)

            if response.text:
                return response.text.strip()
            else:
                return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['empty_response']

        except Exception as e:
            logger.error(f"Ошибка в диалоге: {e}", exc_info=True)
            return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['tech_error']
