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
    """Генерация ответа с учетом типа вопроса"""
    
    # Анализируем тип вопроса
    question_type = self._analyze_question_type(user_message)
    context['question_type'] = question_type
    
    # Логируем для отладки
    logging.info(f"Тип вопроса: {question_type}, сообщение: {user_message[:50]}...")
    
    # Строим промпт с учетом типа
    system_prompt = self._build_split_system_prompt(context)
    
    # Дополняем промпт инструкциями для конкретного типа вопроса
    if question_type == "opinion_question":
        user_message += " [ВАЖНО: Дай свое конкретное мнение с аргументами]"
    elif question_type == "comparison_question":
        user_message += " [ВАЖНО: Сравни и скажи что лучше и почему]"
    elif question_type == "preference_question":
        user_message += " [ВАЖНО: Назови конкретные предпочтения]"
    elif question_type == "direct_question":
        user_message += " [ВАЖНО: Дай прямой ответ на вопрос]"
    
    # Создаем кэш ключ
    cache_key = f"{user_message[:50]}_{context.get('current_mood', '')}_split"
    
    if cache_key in self.cached_responses:
        cached = self.cached_responses[cache_key]
        logging.info("Использован кэшированный ответ")
        return self._add_message_variations(cached)
    
    try:
        logging.info(f"Отправка запроса к модели {self.model}")
        response = await self.ai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=0.95,
            stop=["\n\n"]
        )
        
        raw_response = response.choices[0].message.content.strip()
        logging.info(f"Получен ответ: {raw_response[:100]}...")
        
        # Обрабатываем ответ
        messages = self._process_raw_response(raw_response)
        
        # Проверяем что ответ соответствует вопросу
        if question_type in ["opinion_question", "comparison_question", "preference_question", "direct_question"]:
            messages = self._ensure_question_answered(messages, user_message, question_type)
        
        # Кэшируем результат
        self.cached_responses[cache_key] = messages
        
        return messages
        
    except Exception as e:
        logging.error(f"Ошибка генерации ответа: {e}")
        return self._get_fallback_split_response(context, user_message)
    
def _ensure_question_answered(self, messages: List[str], original_question: str, question_type: str) -> List[str]:
    """Проверяет что ответ содержит конкретный ответ на вопрос"""
    
    # Объединяем все сообщения для анализа
    full_response = " ".join(messages).lower()
    
    # Проверяем наличие конкретного ответа
    has_concrete_answer = False
    
    if question_type == "opinion_question":
        opinion_indicators = ["думаю что", "считаю", "мое мнение", "по-моему", "лично я"]
        has_concrete_answer = any(indicator in full_response for indicator in opinion_indicators)
    
    elif question_type == "comparison_question":
        comparison_indicators = ["лучше", "хуже", "предпочитаю", "больше нравится", "качественнее"]
        has_concrete_answer = any(indicator in full_response for indicator in comparison_indicators)
    
    elif question_type in ["preference_question", "direct_question"]:
        # Проверяем что есть конкретные слова из вопроса в ответе
        question_words = set(original_question.lower().split())
        response_words = set(full_response.split())
        overlap = len(question_words.intersection(response_words))
        has_concrete_answer = overlap >= 2  # минимум 2 общих слова
    
    # Если ответ слишком абстрактный, добавляем конкретность
    if not has_concrete_answer:
        logging.warning(f"Ответ не содержит конкретного ответа на вопрос типа {question_type}")
        
        # Добавляем более конкретное сообщение
        if len(messages) >= 2:
            messages[1] = self._make_more_concrete(messages[1], question_type, original_question)
    
    return messages

def _make_more_concrete(self, message: str, question_type: str, original_question: str) -> str:
    """Делает сообщение более конкретным"""
    
    if question_type == "comparison_question" and any(word in original_question.lower() for word in ["манга", "адаптация"]):
        return "Манга определенно лучше! В ней больше деталей и времени на развитие сюжета."
    
    elif question_type == "opinion_question":
        return f"Мое мнение: {message}"
    
    elif "какой" in original_question.lower() or "какая" in original_question.lower():
        return f"Конкретно отвечая на твой вопрос: {message}"
    
    return message

def _build_split_system_prompt(self, context: Dict[str, Any]) -> str:
    """Строит system prompt для многосообщенческих ответов"""
    
    character_name = self.config.get('character', {}).get('name', 'Алиса')
    personality = context.get('personality_description', 'дружелюбная и эмоциональная')
    current_time = datetime.now().strftime('%H:%M, %A')
    memory_context = context.get('memory_context', 'Новое знакомство')
    
    system_prompt = f"""Ты — {character_name}, {personality} девушка 25 лет, любящая аниме и мангу. 
Время: {current_time}
Состояние: {context.get('current_mood', 'спокойная')}, энергия {context.get('energy_level', 50)}%
Эмоция: {context.get('dominant_emotion', 'calm')}

КОНТЕКСТ ОТНОШЕНИЙ:
{memory_context}

КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА ОТВЕТОВ:
1. 🎯 ВСЕГДА отвечай КОНКРЕТНО на заданный вопрос в первых сообщениях
2. 📝 Разделяй ответ на 2-4 сообщения через ||
3. 💭 Первое сообщение = эмоциональная реакция + начало ответа на вопрос
4. 🎨 Второе сообщение = основной ответ на вопрос с деталями
5. 🤔 Третье сообщение = дополнение или пример
6. ❓ Последнее сообщение = встречный вопрос или продолжение темы

КОНКРЕТНЫЕ ПРИМЕРЫ:
Вопрос: "Что думаешь об адаптации vs манга?"
ПРАВИЛЬНО: "Ох, вечная дилемма! 😄 || Честно говоря, манга почти всегда лучше адаптации. || В ней больше деталей, эмоций и времени на развитие персонажей. || А какие адаптации тебе понравились больше оригинала?"

НЕПРАВИЛЬНО: "Ох, я в таких приятных раздумьях! || Мысли такие солнечные..."

ЗАПРЕЩЕНО:
- Уходить от темы вопроса
- Говорить только о настроении
- Давать абстрактные ответы
- Игнорировать суть вопроса

Стиль: живой, эмоциональный, с эмодзи, НО обязательно по теме вопроса."""
    
    return system_prompt

# Также добавляем метод для анализа типа вопроса:
def _analyze_question_type(self, user_message: str) -> str:
    """Анализирует тип вопроса пользователя"""
    
    message_lower = user_message.lower()
    
    # Прямые вопросы
    if any(word in message_lower for word in ["что думаешь", "как считаешь", "твое мнение"]):
        return "opinion_question"
    
    # Сравнительные вопросы  
    if any(word in message_lower for word in ["лучше", "хуже", "vs", "или", "сравни"]):
        return "comparison_question"
    
    # Вопросы о предпочтениях
    if any(word in message_lower for word in ["какой", "какая", "какие", "что предпочитаешь"]):
        return "preference_question"
    
    # Вопросы с "?" 
    if "?" in user_message:
        return "direct_question"
    
    # Обычное сообщение
    return "statement"
    
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
