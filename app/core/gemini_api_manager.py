"""
Менеджер Gemini API - замена OpenRouter на Google Gemini 2.5 Flash
"""

import logging
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime

class APIUsageType(Enum):
    """Типы использования API"""
    DIALOGUE = "dialogue"           # Диалоги с пользователем + инициативы
    PLANNING = "planning"           # Планирование дня + изменения планов
    ANALYTICS = "analytics"         # Консолидация памяти + анализ эмоций


class GeminiAPIManager:
    """Менеджер для работы с Google Gemini API"""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Получаем API ключ
        self.api_key = config.get('ai', {}).get('gemini_api_key')
        if not self.api_key:
            raise ValueError("Gemini API key not found in config")

        # Настраиваем Gemini
        genai.configure(api_key=self.api_key)

        # Модель
        self.model_name = config.get('ai', {}).get('model', 'gemini-2.0-flash-exp')

        # Создаем модели для разных типов
        self.models = {}

        # Статистика использования
        self.usage_stats = {
            APIUsageType.DIALOGUE: {"requests": 0, "tokens": 0, "errors": 0},
            APIUsageType.PLANNING: {"requests": 0, "tokens": 0, "errors": 0},
            APIUsageType.ANALYTICS: {"requests": 0, "tokens": 0, "errors": 0}
        }

        self.logger.info(f"Gemini API Manager initialized with model: {self.model_name}")

    def _get_model(self, usage_type: APIUsageType):
        """Получает или создает модель для типа использования"""
        if usage_type not in self.models:
            # Создаем generation config в зависимости от типа
            generation_config = self._get_generation_config(usage_type)

            self.models[usage_type] = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )

        return self.models[usage_type]

    def _get_generation_config(self, usage_type: APIUsageType) -> Dict[str, Any]:
        """Возвращает конфигурацию генерации для типа"""
        ai_config = self.config.get('ai', {})

        # Базовая конфигурация
        config = {
            'temperature': ai_config.get('temperature', 0.85),
            'top_p': ai_config.get('top_p', 0.95),
            'top_k': ai_config.get('top_k', 40),
            'max_output_tokens': ai_config.get('max_tokens', 350),
        }

        # Настройки в зависимости от типа
        if usage_type == APIUsageType.DIALOGUE:
            config['temperature'] = 0.85
            config['max_output_tokens'] = 400
        elif usage_type == APIUsageType.PLANNING:
            config['temperature'] = 0.7  # Более детерминированное планирование
            config['max_output_tokens'] = 500
        elif usage_type == APIUsageType.ANALYTICS:
            config['temperature'] = 0.6  # Более точные анализы
            config['max_output_tokens'] = 300

        return config

    async def make_request(self, usage_type: APIUsageType, messages: List[Dict[str, str]], **kwargs) -> Any:
        """
        Делает запрос к Gemini API

        Args:
            usage_type: тип использования API
            messages: список сообщений в формате [{"role": "system"|"user"|"assistant", "content": "..."}]
            **kwargs: дополнительные параметры (игнорируются для совместимости)

        Returns:
            Объект ответа в формате совместимом с OpenAI API
        """
        import asyncio

        try:
            # Обновляем статистику
            self.usage_stats[usage_type]["requests"] += 1

            # Получаем модель
            model = self._get_model(usage_type)

            # Преобразуем messages в формат Gemini
            gemini_messages = self._convert_messages_to_gemini(messages)

            # Делаем запрос (синхронный вызов в отдельном потоке)
            response = await asyncio.to_thread(model.generate_content, gemini_messages)

            # Считаем токены (приблизительно)
            tokens_used = self._estimate_tokens(gemini_messages, response.text)
            self.usage_stats[usage_type]["tokens"] += tokens_used

            self.logger.debug(f"Gemini API request {usage_type.value}: success ({tokens_used} tokens)")

            # Возвращаем в формате совместимом с OpenAI
            return self._format_response(response)

        except Exception as e:
            self.usage_stats[usage_type]["errors"] += 1
            self.logger.error(f"Gemini API error {usage_type.value}: {e}")
            raise

    def _convert_messages_to_gemini(self, messages: List[Dict[str, str]]) -> str:
        """
        Преобразует messages из OpenAI формата в Gemini формат

        Gemini использует простую строку с контекстом, а не list of messages
        """
        # Объединяем system и user сообщения
        context_parts = []

        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')

            if role == 'system':
                context_parts.append(f"{content}")
            elif role == 'user':
                context_parts.append(f"\nUser: {content}")
            elif role == 'assistant':
                context_parts.append(f"\nAssistant: {content}")

        return "\n".join(context_parts)

    def _format_response(self, gemini_response) -> Any:
        """Форматирует ответ Gemini в формат совместимый с OpenAI API"""

        class Choice:
            def __init__(self, text):
                self.message = type('Message', (), {'content': text})()

        class Response:
            def __init__(self, text, tokens):
                self.choices = [Choice(text)]
                self.usage = type('Usage', (), {'total_tokens': tokens})()

        # Извлекаем текст из ответа
        text = gemini_response.text if hasattr(gemini_response, 'text') else str(gemini_response)

        # Оцениваем токены
        tokens = self._estimate_tokens("", text)

        return Response(text, tokens)

    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """Приблизительная оценка токенов (1 токен ≈ 4 символа для русского)"""
        total_chars = len(prompt) + len(response)
        return total_chars // 4

    def get_usage_stats(self) -> Dict:
        """Возвращает статистику использования API"""

        total_stats = {
            "total_requests": sum(stats["requests"] for stats in self.usage_stats.values()),
            "total_tokens": sum(stats["tokens"] for stats in self.usage_stats.values()),
            "total_errors": sum(stats["errors"] for stats in self.usage_stats.values()),
            "by_type": {}
        }

        for usage_type, stats in self.usage_stats.items():
            total_stats["by_type"][usage_type.value] = {
                **stats,
                "model": self.model_name
            }

        return total_stats

    def reset_daily_stats(self):
        """Сбрасывает дневную статистику"""
        for usage_type in self.usage_stats:
            self.usage_stats[usage_type] = {"requests": 0, "tokens": 0, "errors": 0}

        self.logger.info("Gemini API statistics reset")


# Удобная функция для создания менеджера
def create_gemini_api_manager(config: Dict) -> GeminiAPIManager:
    """Создает менеджер Gemini API"""
    return GeminiAPIManager(config)
