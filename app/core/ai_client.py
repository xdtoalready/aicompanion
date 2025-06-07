# Оптимизированная система запросов к AI

import json
import logging
import random
from datetime import datetime
from typing import List, Tuple, Dict, Any

class OptimizedAI:
    """Оптимизированная система запросов к AI"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.prompt_cache = {}
        self.batch_queue = []
        self.last_state_check = None
        self.cached_responses = {}
    
    async def get_batched_response(self, prompts: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Пакетная обработка нескольких запросов"""
        
        combined_prompt = "Ответь на несколько запросов в JSON формате:\n\n"
        
        for i, (prompt_type, prompt_text) in enumerate(prompts):
            combined_prompt += f"ЗАПРОС_{i+1} ({prompt_type}):\n{prompt_text}\n\n"
        
        combined_prompt += """
Ответь в JSON:
{
    "response_1": {...},
    "response_2": {...},
    ...
}"""
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": combined_prompt}],
                max_tokens=800,
                temperature=0.8
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logging.error(f"Ошибка пакетного запроса: {e}")
            return {}
    
    async def get_simple_mood_calculation(self, psychological_core) -> Dict:
        """Простой расчет настроения без AI для экономии токенов"""
        
        current_hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5
        
        # Локальный расчет базового состояния
        base_mood = psychological_core.calculate_current_mood({
            "weekend": is_weekend,
            "weather": "normal"  # можно интегрировать API погоды
        })
        
        # Определяем активности по времени
        if 6 <= current_hour <= 9:
            activity_context = "morning_routine"
            energy_mod = 0.8
        elif 9 <= current_hour <= 17:
            activity_context = "work_time"
            energy_mod = 0.9
        elif 17 <= current_hour <= 22:
            activity_context = "evening_time"
            energy_mod = 0.7
        else:
            activity_context = "night_time"
            energy_mod = 0.4
        
        return {
            "current_mood": self._mood_to_description(base_mood),
            "energy_level": int(psychological_core.physical_state["energy_base"] * energy_mod),
            "activity_context": activity_context,
            "dominant_emotion": psychological_core.emotional_momentum["current_emotion"],
            "initiative_desire": min(10, int(base_mood * 0.8 + random.uniform(-2, 2)))
        }
    
    async def generate_contextual_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Генерирует контекстуальный ответ с оптимизацией"""
        
        # Кэшируем похожие запросы
        cache_key = f"{user_message[:50]}_{context.get('current_mood', '')}"
        
        if cache_key in self.cached_responses:
            # Возвращаем кэшированный ответ с небольшими вариациями
            cached = self.cached_responses[cache_key]
            return self._add_variation(cached)
        
        # Создаем оптимизированный промпт
        prompt = self._build_optimized_prompt(user_message, context)
        
        try:
            response = await self.ai_client.chat.completions.create(
                model="deepseek/deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Кэшируем ответ
            self.cached_responses[cache_key] = ai_response
            
            return ai_response
            
        except Exception as e:
            logging.error(f"Ошибка генерации ответа: {e}")
            return self._get_fallback_response(context)
    
    def _build_optimized_prompt(self, user_message: str, context: Dict[str, Any]) -> str:
        """Строит оптимизированный промпт"""
        
        prompt = f"""Ты отвечаешь как живой человек.

СОСТОЯНИЕ: {context.get('current_mood', 'спокойная')}, энергия {context.get('energy_level', 50)}/100
ЭМОЦИЯ: {context.get('dominant_emotion', 'calm')}
СООБЩЕНИЕ: "{user_message}"

Ответь естественно, 1-2 предложения:"""
        
        return prompt
    
    def _mood_to_description(self, mood_value: float) -> str:
        """Конвертирует числовое настроение в описание"""
        if mood_value >= 8:
            return random.choice(["отличное", "прекрасное", "воодушевленная"])
        elif mood_value >= 6:
            return random.choice(["хорошее", "спокойная", "довольная"])
        elif mood_value >= 4:
            return random.choice(["нормальное", "задумчивая", "нейтральная"])
        else:
            return random.choice(["грустная", "уставшая", "подавленная"])
    
    def _add_variation(self, base_response: str) -> str:
        """Добавляет небольшие вариации к кэшированному ответу"""
        
        variations = [
            lambda x: x,  # без изменений
            lambda x: x + " 😊",
            lambda x: f"Хм, {x.lower()}",
            lambda x: x.replace(".", "!") if not x.endswith("!") else x
        ]
        
        return random.choice(variations)(base_response)
    
    def _get_fallback_response(self, context: Dict[str, Any]) -> str:
        """Резервный ответ при ошибках AI"""
        
        mood = context.get("current_mood", "нормальное")
        
        fallback_responses = {
            "отличное": ["Настроение супер! Что нового?", "День прекрасный! Делюсь позитивом ✨"],
            "хорошее": ["Дела хорошо, спасибо что спрашиваешь!", "Все отлично, как у тебя?"],
            "нормальное": ["Все идет своим чередом", "Обычный день, ничего особенного"],
            "грустная": ["Что-то загрустила сегодня...", "Настроение так себе, но ты меня подбодришь"]
        }
        
        responses = fallback_responses.get(mood, fallback_responses["нормальное"])
        return random.choice(responses)
    
    async def extract_facts_from_conversation(self, user_message: str, ai_response: str) -> List[Dict]:
        """Извлекает факты из разговора (упрощенная версия)"""
        
        facts = []
        user_lower = user_message.lower()
        
        # Простые паттерны для извлечения фактов
        patterns = {
            "работа": ["работаю", "работа", "офис", "коллеги", "проект"],
            "хобби": ["люблю", "увлекаюсь", "хобби", "интересуюсь"],
            "настроение": ["грустно", "весело", "устал", "рад", "злой"],
            "планы": ["планирую", "собираюсь", "хочу", "буду"],
            "семья": ["мама", "папа", "брат", "сестра", "семья", "родители"]
        }
        
        for fact_type, keywords in patterns.items():
            if any(keyword in user_lower for keyword in keywords):
                facts.append({
                    "type": fact_type,
                    "content": user_message[:100],  # первые 100 символов
                    "importance": 5,
                    "timestamp": datetime.now().isoformat()
                })
        
        return facts
    
    def clear_cache(self):
        """Очищает кэш ответов"""
        self.cached_responses.clear()
        logging.info("Кэш AI ответов очищен")