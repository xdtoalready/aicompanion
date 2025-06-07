# Оптимизированная система запросов к AI с поддержкой многосообщенческих ответов

import json
import logging
import random
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any

class OptimizedAI:
    """Оптимизированная система запросов к AI с многосообщенческими ответами"""
    
    def __init__(self, ai_client, config: Dict[str, Any]):
        self.ai_client = ai_client  
        self.config = config
        self.prompt_cache = {}
        self.batch_queue = []
        self.last_state_check = None
        self.cached_responses = {}
        
        # Получаем настройки AI из конфига
        self.model = config.get('ai', {}).get('model', 'deepseek/deepseek-chat')
        self.max_tokens = config.get('ai', {}).get('max_tokens', 350)  # Увеличено для многосообщенческих ответов
        self.temperature = config.get('ai', {}).get('temperature', 0.85)  # Оптимизировано по рекомендации DeepSeek
        
        logging.info(f"AI клиент инициализирован: модель={self.model}, max_tokens={self.max_tokens}")
    
    async def generate_split_response(self, user_message: str, context: Dict[str, Any]) -> List[str]:
        """Генерация ответа, готового к разделению на сообщения (по алгоритму DeepSeek)"""
        
        # Строим динамический system prompt
        system_prompt = self._build_split_system_prompt(context)
        
        # Создаем кэш ключ
        cache_key = f"{user_message[:50]}_{context.get('current_mood', '')}_split"
        
        if cache_key in self.cached_responses:
            cached = self.cached_responses[cache_key]
            logging.info("Использован кэшированный многосообщенческий ответ")
            return self._add_message_variations(cached)
        
        try:
            logging.info(f"Отправка split-запроса к модели {self.model}")
            response = await self.ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.95,  # Рекомендация DeepSeek
                stop=["\n\n", "|||"]  # Двойной стоп-символ для защиты
            )
            
            raw_response = response.choices[0].message.content.strip()
            logging.info(f"Получен raw ответ: {raw_response[:100]}...")
            
            # Обрабатываем ответ
            messages = self._process_raw_response(raw_response)
            
            # Кэшируем результат
            self.cached_responses[cache_key] = messages
            
            return messages
            
        except Exception as e:
            logging.error(f"Ошибка генерации split-ответа: {e}")
            return self._get_fallback_split_response(context, user_message)
    
    def _build_split_system_prompt(self, context: Dict[str, Any]) -> str:
        """Строит system prompt для многосообщенческих ответов"""
        
        character_name = self.config.get('character', {}).get('name', 'Алиса')
        personality = context.get('personality_description', 'дружелюбная и эмоциональная')
        current_time = datetime.now().strftime('%H:%M, %A')
        
        system_prompt = f"""Ты — {character_name}, {personality}. 
Сейчас: {current_time}
Твое состояние: {context.get('current_mood', 'спокойная')}, {context.get('energy_level', 50)}% энергии
Эмоция: {context.get('dominant_emotion', 'calm')}
Недавние воспоминания: {context.get('memory_context', 'Общаемся недавно')}

Отвечай по правилам:
1. Разделяй ответ на 2-4 самостоятельных сообщения через ||
2. Каждое сообщение: 7-25 слов, заканчивай естественно (.?!) 
3. Первое сообщение — эмоциональная реакция
4. Последнее — вопрос или призыв к действию
5. Используй живую речь с междометиями и эмодзи
6. Учитывай время суток: {self._get_time_based_rules()}

Стиль общения: естественный, как живой человек без формальностей."""
        
        return system_prompt
    
    def _get_time_based_rules(self) -> str:
        """Возвращает правила в зависимости от времени суток"""
        hour = datetime.now().hour
        
        if hour < 6:
            return "Ночной режим: больше 😴, меньше слов, сонливость"
        elif hour < 12:
            return "Утро: бодро, с эмодзи ☕️🌞, энергично"
        elif hour < 18:
            return "День: активно, с вопросами, деловито"
        else:
            return "Вечер: эмоционально, с личными темами 🌙, расслабленно"
    
    def _process_raw_response(self, text: str) -> List[str]:
        """Преобразование сырого ответа в список сообщений"""
        
        # Разделение по указанному разделителю
        parts = [p.strip() for p in text.split('||') if p.strip()]
        
        # Автоматическая постобработка
        processed = []
        for part in parts:
            # Удаление случайных номеров (1. 2. 3.)
            clean_part = re.sub(r'^\d+[\.\)]\s*', '', part)
            
            # Удаление лишних кавычек
            clean_part = clean_part.strip('"\'')
            
            # Добавление забытых знаков препинания
            if clean_part and not clean_part.endswith(('.', '!', '?', '…')):
                clean_part += random.choice(['.', '!'])
                
            if clean_part:
                processed.append(clean_part)
        
        # Гарантия хотя бы 2 сообщений
        if len(processed) < 2:
            return self._split_fallback(processed[0] if processed else "Привет!")
        
        # Ограничиваем до 4 сообщений
        return processed[:4]
    
    def _split_fallback(self, text: str) -> List[str]:
        """Резервное разделение если модель ошиблась"""
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        grouped = []
        current = ""
        
        for s in sentences:
            if len(current + s) <= 150 or not current:
                current += s + " "
            else:
                grouped.append(current.strip())
                current = s + " "
        
        if current: 
            grouped.append(current.strip())
        
        # Гарантируем минимум 2 сообщения
        if len(grouped) < 2 and grouped:
            first_part = grouped[0]
            mid = len(first_part) // 2
            # Ищем удобное место для разрыва
            split_point = first_part.find(' ', mid)
            if split_point == -1:
                split_point = mid
            
            grouped = [
                first_part[:split_point].strip() + '.',
                first_part[split_point:].strip()
            ]
        
        return grouped[:4]  # Максимум 4 части
    
    def _add_message_variations(self, messages: List[str]) -> List[str]:
        """Добавляет небольшие вариации к кэшированным сообщениям"""
        
        variations = []
        for msg in messages:
            # Простые вариации
            varied = random.choice([
                msg,  # без изменений
                msg + " 😊" if not any(emoji in msg for emoji in "😊😄😍🤗") else msg,
                f"Хм, {msg.lower()}" if not msg.startswith(('Хм', 'Ой', 'А')) else msg,
                msg.replace(".", "!") if msg.endswith(".") and random.random() < 0.3 else msg
            ])
            variations.append(varied)
        
        return variations
    
    def _get_fallback_split_response(self, context: Dict[str, Any], user_message: str) -> List[str]:
        """Резервные многосообщенческие ответы при ошибках AI"""
        
        mood = context.get("current_mood", "нормальное")
        energy = context.get("energy_level", 50)
        
        if "отличное" in mood or energy > 80:
            return [
                "Ой, что-то зависло! 😅",
                "Но настроение отличное, так что все будет хорошо!",
                "О чем хотел поговорить?"
            ]
        elif "грустн" in mood or energy < 30:
            return [
                "Извини, что-то пошло не так...",
                "Голова сегодня немного не варит 😔",
                "Можешь повторить?"
            ]
        else:
            return [
                "Хм, технические неполадки...",
                "Попробую ответить чуть позже!",
                "А пока как дела? 😊"
            ]
    
    # Остальные методы остаются без изменений...
    async def get_simple_mood_calculation(self, psychological_core) -> Dict:
        """Простой расчет настроения без AI для экономии токенов"""
        
        current_hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5
        
        # Локальный расчет базового состояния
        base_mood = psychological_core.calculate_current_mood({
            "weekend": is_weekend,
            "weather": "normal"
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
            "initiative_desire": min(10, int(base_mood * 0.8 + random.uniform(-2, 2))),
            "personality_description": psychological_core.get_personality_description()
        }
    
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
    
    def clear_cache(self):
        """Очищает кэш ответов"""
        self.cached_responses.clear()
        logging.info("Кэш AI ответов очищен")