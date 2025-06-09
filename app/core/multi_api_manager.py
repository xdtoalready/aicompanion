"""
Менеджер множественных OpenRouter API ключей
"""

import random
import logging
from typing import Dict, List, Optional
from enum import Enum
from openai import AsyncOpenAI
from datetime import datetime, timedelta

class APIUsageType(Enum):
    """Типы использования API"""
    DIALOGUE = "dialogue"           # Диалоги с пользователем + инициативы
    PLANNING = "planning"           # Планирование дня + изменения планов
    ANALYTICS = "analytics"         # Консолидация памяти + анализ эмоций

class MultiAPIManager:
    """Менеджер для работы с множественными API ключами"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Загружаем ключи из конфигурации
        self.api_pools = self._load_api_pools()
        
        # Статистика использования
        self.usage_stats = {
            APIUsageType.DIALOGUE: {"requests": 0, "tokens": 0, "errors": 0},
            APIUsageType.PLANNING: {"requests": 0, "tokens": 0, "errors": 0}, 
            APIUsageType.ANALYTICS: {"requests": 0, "tokens": 0, "errors": 0}
        }
        
        # Кэш клиентов OpenAI
        self.clients_cache = {}
        
        self.logger.info(f"Инициализированы API пулы: {list(self.api_pools.keys())}")
    
    def _load_api_pools(self) -> Dict[APIUsageType, List[str]]:
        """Загружает пулы API ключей из конфигурации"""
        pools = {}
        
        ai_config = self.config.get("ai", {})
        
        # Диалоги (основной приоритет)
        dialogue_keys = ai_config.get("dialogue_api_keys", [])
        if not dialogue_keys:
            # Fallback на основной ключ
            main_key = ai_config.get("openrouter_api_key")
            if main_key:
                dialogue_keys = [main_key]
        
        pools[APIUsageType.DIALOGUE] = dialogue_keys
        
        # Планирование
        planning_keys = ai_config.get("planning_api_keys", [])
        if not planning_keys:
            # Можем использовать диалоговые ключи как fallback
            planning_keys = dialogue_keys.copy()
        
        pools[APIUsageType.PLANNING] = planning_keys
        
        # Аналитика (наименьший приоритет)
        analytics_keys = ai_config.get("analytics_api_keys", [])
        if not analytics_keys:
            # Fallback на планировочные ключи
            analytics_keys = planning_keys.copy()
        
        pools[APIUsageType.ANALYTICS] = analytics_keys
        
        # Валидация
        for usage_type, keys in pools.items():
            if not keys:
                self.logger.error(f"Нет API ключей для {usage_type.value}")
                raise ValueError(f"Необходимо настроить ключи для {usage_type.value}")
            
            self.logger.info(f"{usage_type.value}: {len(keys)} ключей")
        
        return pools
    
    def get_client(self, usage_type: APIUsageType) -> AsyncOpenAI:
        """Получает клиента OpenAI для определенного типа использования"""
        
        # Выбираем ключ из соответствующего пула
        api_key = self._select_api_key(usage_type)
        
        # Кэшируем клиенты по ключам
        if api_key not in self.clients_cache:
            self.clients_cache[api_key] = AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            
        return self.clients_cache[api_key]
    
    def _select_api_key(self, usage_type: APIUsageType) -> str:
        """Выбирает API ключ для использования (round-robin + случайность)"""
        
        available_keys = self.api_pools[usage_type]
        
        if len(available_keys) == 1:
            return available_keys[0]
        
        # Простая ротация с элементом случайности
        # В будущем можно добавить балансировку по нагрузке
        return random.choice(available_keys)
    
    async def make_request(self, usage_type: APIUsageType, **kwargs) -> any:
        """Делает запрос к API с учетом типа использования"""
        
        client = self.get_client(usage_type)
        
        try:
            # Обновляем статистику
            self.usage_stats[usage_type]["requests"] += 1
            
            # Делаем запрос
            response = await client.chat.completions.create(**kwargs)
            
            # Подсчитываем токены (приблизительно)
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
                self.usage_stats[usage_type]["tokens"] += tokens_used
            
            self.logger.debug(f"API запрос {usage_type.value}: успех")
            return response
            
        except Exception as e:
            self.usage_stats[usage_type]["errors"] += 1
            self.logger.error(f"Ошибка API запроса {usage_type.value}: {e}")
            raise
    
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
                "pool_size": len(self.api_pools[usage_type]),
                "keys_available": len(self.api_pools[usage_type])
            }
        
        return total_stats
    
    def reset_daily_stats(self):
        """Сбрасывает дневную статистику (вызывать в полночь)"""
        for usage_type in self.usage_stats:
            self.usage_stats[usage_type] = {"requests": 0, "tokens": 0, "errors": 0}
        
        self.logger.info("Статистика API обнулена")

# Удобные функции для использования в коде
def create_api_manager(config: Dict) -> MultiAPIManager:
    """Создает менеджер API"""
    return MultiAPIManager(config)

async def make_dialogue_request(api_manager: MultiAPIManager, **kwargs):
    """Запрос для диалогов"""
    return await api_manager.make_request(APIUsageType.DIALOGUE, **kwargs)

async def make_planning_request(api_manager: MultiAPIManager, **kwargs):
    """Запрос для планирования"""
    return await api_manager.make_request(APIUsageType.PLANNING, **kwargs)

async def make_analytics_request(api_manager: MultiAPIManager, **kwargs):
    """Запрос для аналитики"""
    return await api_manager.make_request(APIUsageType.ANALYTICS, **kwargs)