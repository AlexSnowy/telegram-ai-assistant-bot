import os
import logging
from typing import Optional, Dict, List
from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)


class GroqClient:
    """Клиент для работы с Groq API (бесплатно, быстрая модель)"""

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
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model_name = Config.GROQ_MODEL
        self.temperature = Config.GROQ_TEMPERATURE
        self.max_tokens = Config.GROQ_MAX_TOKENS

        if not self.api_key:
            raise ValueError("GROQ_API_KEY не установлен")

        # Groq uses OpenAI-compatible API with different base URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        logger.info(f"Groq клиент инициализирован с моделью: {self.model_name}")

    def _get_messages(self, system_prompt: str, user_message: str,
                      context: Optional[str] = None,
                      history: Optional[List[Dict]] = None) -> List[Dict]:
        """Формирование списка сообщений для API"""
        messages = []

        # Системный промт
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Контекст
        if context:
            messages.append({"role": "system", "content": f"Контекст из базы знаний:\n{context}"})

        # История
        if history:
            for msg in history[-10:]:
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })

        # Текущее сообщение
        messages.append({"role": "user", "content": user_message})

        return messages

    def generate_response(
            self,
            prompt: str,
            system_instruction: Optional[str] = None,
            context: Optional[str] = None,
            history: Optional[List[Dict]] = None,
            language: str = 'uz'
    ) -> str:
        try:
            messages = self._get_messages(system_instruction, prompt, context, history)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            if response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                logger.warning("Пустой ответ от Groq")
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

            messages = [
                {"role": "user", "content": formatted_prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            if response.choices[0].message.content:
                return response.choices[0].message.content.strip()
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

            messages = self._get_messages(full_system, user_message, None, chat_history)

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            if response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['empty_response']

        except Exception as e:
            logger.error(f"Ошибка в диалоге: {e}", exc_info=True)
            return self.ERROR_MESSAGES.get(language, self.ERROR_MESSAGES['uz'])['tech_error']
