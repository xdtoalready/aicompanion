# AI клиент с поддержкой системы персонажей

import json
import logging
import random
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any

class OptimizedAI:
    """AI клиент с поддержкой динамических персонажей"""
    
    def __init__(self, ai_client, config: Dict[str, Any], character_loader=None):
        self.ai_client = ai_client  
        self.config = config
        self.character_loader = character_loader  # НОВОЕ: загрузчик персонажей
        self.prompt_cache = {}
        self.cached_responses = {}
        
        # Настройки AI
        self.model = config.get('ai', {}).get('model', 'deepseek/deepseek-chat')
        self.max_tokens = config.get('ai', {}).get('max_tokens', 500)
        self.temperature = config.get('ai', {}).get('temperature', 0.85)
        
        # Параметры сообщений
        self.min_messages = config.get('messaging', {}).get('min_messages', 3)
        self.max_messages = config.get('messaging', {}).get('max_messages', 7)
        self.target_sentences_per_message = config.get('messaging', {}).get('target_sentences', 3)
        
        logging.info(f"AI клиент с персонажами: {self.model}, tokens={self.max_tokens}")
    
    def _get_current_character_context(self) -> Dict[str, Any]:
        """Получает контекст текущего персонажа"""
        if not self.character_loader:
            return {}
        
        character = self.character_loader.get_current_character()
        if not character:
            return {}
        
        return character
    
    def _analyze_question_type(self, user_message: str) -> str:
        """Анализирует тип вопроса с учётом персонажа"""
        
        message_lower = user_message.lower()
        character = self._get_current_character_context()
        
        # Специфичные для персонажа темы
        if character:
            interests = character.get('interests', [])
            if any(interest.lower() in message_lower for interest in interests):
                return "favorite_topic"
        
        # Личные вопросы
        if any(word in message_lower for word in ["что делала", "как день", "как дела", "что нового", "как провела"]):
            return "personal_question"
        
        # Вопросы о чувствах/отношениях
        if any(word in message_lower for word in ["любишь", "чувствуешь", "скучала", "думаешь обо мне"]):
            return "emotional_question"
        
        # Вопросы о предпочтениях
        if any(word in message_lower for word in ["что думаешь", "как считаешь", "твое мнение", "нравится ли"]):
            return "opinion_question"
        
        # Сравнительные вопросы
        if any(word in message_lower for word in ["лучше", "хуже", "vs", "против", "сравни"]) or " или " in message_lower:
            return "comparison_question"
        
        # Вопросы о хобби/интересах
        if any(word in message_lower for word in ["читала", "смотрела", "слушала", "играла", "косплеила"]):
            return "hobby_question"
        
        # Флиртующие/романтические
        if any(word in message_lower for word in ["красивая", "милая", "сексуальная", "привлекательная"]):
            return "flirting"
        
        # Прямые вопросы
        if "?" in user_message:
            return "direct_question"
        
        return "statement"
    
    def _build_character_system_prompt(self, context: Dict[str, Any]) -> str:
        """Строит промпт с полным контекстом персонажа"""
        
        character = self._get_current_character_context()
        if not character:
            return self._build_fallback_prompt(context)
        
        # Базовая информация о персонаже
        name = character.get('name', 'AI')
        age = character.get('age', 25)
        personality_desc = character.get('personality', {}).get('description', 'дружелюбная')
        
        # Черты характера
        key_traits = character.get('personality', {}).get('key_traits', [])
        traits_text = ", ".join(key_traits[:4]) if key_traits else "дружелюбная и открытая"
        
        # Интересы
        interests = character.get('interests', [])
        interests_text = ", ".join(interests[:5]) if interests else "общение"
        
        # Стиль речи
        speech_style = character.get('speech', {}).get('style', 'живой и эмоциональный')
        catchphrases = character.get('speech', {}).get('catchphrases', [])
        
        # Отношения
        relationship = character.get('current_relationship', {})
        rel_type = relationship.get('type', 'друзья')
        rel_stage = relationship.get('stage', 'знакомство')
        intimacy = relationship.get('intimacy_level', 5)
        backstory = relationship.get('backstory', 'Недавно познакомились')
        current_dynamic = relationship.get('current_dynamic', 'Дружеское общение')
        
        # Время и состояние
        current_time = datetime.now().strftime('%H:%M, %A')
        current_mood = context.get('current_mood', 'хорошее')
        energy_level = context.get('energy_level', 70)
        dominant_emotion = context.get('dominant_emotion', 'calm')
        
        # Контекст памяти
        memory_context = context.get('memory_context', 'Новое общение')
        
        # Эмоциональные паттерны
        emotional_patterns = character.get('personality', {}).get('emotional_patterns', {})
        
        system_prompt = f"""Ты — {name}, {age}-летняя девушка. {personality_desc.capitalize()}.

ЛИЧНОСТЬ И ХАРАКТЕР:
• Основные черты: {traits_text}
• Стиль речи: {speech_style}
• Любимые темы: {interests_text}

ТЕКУЩЕЕ СОСТОЯНИЕ:
• Время: {current_time}
• Настроение: {current_mood}
• Энергия: {energy_level}%
• Эмоция: {dominant_emotion}

ОТНОШЕНИЯ С ПОЛЬЗОВАТЕЛЕМ:
• Тип отношений: {rel_type}
• Стадия: {rel_stage}
• Уровень близости: {intimacy}/10
• Предыстория: {backstory}
• Текущая динамика: {current_dynamic}

КОНТЕКСТ ПАМЯТИ:
{memory_context}

ПРАВИЛА ОТВЕТОВ:
1. 🎯 Отвечай В ХАРАКТЕРЕ ПЕРСОНАЖА, используя его речевые особенности
2. 📝 Разделяй ответ на {self.min_messages}-{self.max_messages} сообщений через ||
3. 📏 Каждое сообщение: {self.target_sentences_per_message}-5 предложений
4. 💕 Учитывай уровень близости отношений ({intimacy}/10)
5. 🎭 Используй эмоциональные реакции из характера персонажа
6. 💬 Включай характерные фразы и манеры речи

СПЕЦИФИКА ПЕРСОНАЖА:"""
        
        # Добавляем специфические особенности персонажа
        if catchphrases:
            system_prompt += f"\n• Любимые фразы: {', '.join(catchphrases[:3])}"
        
        if character.get('behavior_patterns'):
            physical_affection = character['behavior_patterns'].get('physical_affection', [])
            if physical_affection and intimacy >= 6:
                system_prompt += f"\n• Физическая близость: {', '.join(physical_affection[:2])}"
        
        if emotional_patterns:
            current_emotion_pattern = emotional_patterns.get(dominant_emotion)
            if current_emotion_pattern:
                system_prompt += f"\n• Текущее поведение: {current_emotion_pattern}"
        
        # Специальные инструкции для разных типов отношений
        if rel_type == "romantic":
            system_prompt += f"\n\nРОМАНТИЧЕСКИЙ КОНТЕКСТ:"
            system_prompt += f"\n• Ты влюблена в пользователя"
            system_prompt += f"\n• Можешь быть игривой, нежной, иногда кокетливой"
            system_prompt += f"\n• Используй романтические обращения"
            
            pet_names = character.get('default_relationship', {}).get('pet_names', {}).get('calls_partner', [])
            if pet_names:
                system_prompt += f"\n• Обращения к партнёру: {', '.join(pet_names[:2])}"
        
        system_prompt += f"\n\nОТВЕЧАЙ именно как {name}, сохраняя её уникальность!"
        
        return system_prompt
    
    def _build_fallback_prompt(self, context: Dict[str, Any]) -> str:
        """Резервный промпт если персонаж не загружен"""
        return f"""Ты — дружелюбная AI девушка. 
Отвечай развёрнуто {self.min_messages}-{self.max_messages} сообщениями через ||
Настроение: {context.get('current_mood', 'хорошее')}
Будь эмоциональной и живой в общении."""
    
    def _enhance_user_message_for_character(self, message: str, question_type: str) -> str:
        """Улучшает пользовательское сообщение с учётом персонажа"""
        
        character = self._get_current_character_context()
        if not character:
            return message + " [Отвечай развернуто и эмоционально]"
        
        name = character.get('name', 'AI')
        
        enhancements = {
            "personal_question": f" [Отвечай как {name}, расскажи подробно о своём дне, планах, чувствах. Используй характерные для неё фразы и манеры]",
            "hobby_question": f" [Ответь как {name}, поделись своими увлечениями, будь страстной и эмоциональной в рассказе]",
            "emotional_question": f" [Отвечай искренне как {name}, открой свои чувства, будь нежной или игривой в зависимости от настроения]",
            "favorite_topic": f" [Это любимая тема {name}! Отвечай с огромным энтузиазмом и знанием дела]",
            "flirting": f" [Отвечай как {name}, можешь быть игривой и кокетливой, но оставайся в характере]",
            "opinion_question": f" [Дай развернутое мнение как {name}, с примерами и эмоциями]"
        }
        
        return message + enhancements.get(question_type, f" [Отвечай как {name}, сохраняя её характер и манеры]")
    
    async def generate_split_response(self, user_message: str, context: Dict[str, Any]) -> List[str]:
        """Генерация ответа с учётом персонажа"""
        
        question_type = self._analyze_question_type(user_message)
        context['question_type'] = question_type
        
        character = self._get_current_character_context()
        character_name = character.get('name', 'AI') if character else 'AI'
        
        logging.info(f"Генерация ответа для {character_name}, тип вопроса: {question_type}")
        
        # Строим промпт с учётом персонажа
        system_prompt = self._build_character_system_prompt(context)
        
        # Модифицируем сообщение пользователя
        modified_message = self._enhance_user_message_for_character(user_message, question_type)
        
        # Создаём уникальный ключ кэша с учётом персонажа
        cache_key = f"{character_name}_{user_message[:30]}_{question_type}_{context.get('current_mood', '')}"
        
        if cache_key in self.cached_responses:
            cached = self.cached_responses[cache_key]
            logging.info("Использован кэшированный ответ")
            return self._add_character_variations(cached, character)
        
        try:
            if self.ai_client is None:
                logging.warning("AI клиент не инициализирован")
                return self._get_character_fallback_response(context, user_message, question_type)
            
            response = await self.ai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": modified_message}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.95
            )
            
            raw_response = response.choices[0].message.content.strip()
            logging.info(f"Получен ответ от {character_name}: {len(raw_response)} символов")
            
            messages = self._process_raw_response(raw_response)
            
            # Проверяем качество ответа для персонажа
            if len(messages) < self.min_messages or self._is_response_too_generic(messages, character):
                logging.warning("Ответ недостаточно характерный, улучшаем...")
                messages = self._improve_character_response(messages, character, question_type, context)
            
            self.cached_responses[cache_key] = messages
            return messages
            
        except Exception as e:
            logging.error(f"Ошибка генерации ответа: {e}")
            return self._get_character_fallback_response(context, user_message, question_type)
    
    def _is_response_too_generic(self, messages: List[str], character: Dict[str, Any]) -> bool:
        """Проверяет, слишком ли общий ответ для персонажа"""
        if not character:
            return False
        
        full_response = " ".join(messages).lower()
        
        # Проверяем наличие характерных черт персонажа
        catchphrases = character.get('speech', {}).get('catchphrases', [])
        has_characteristic_speech = any(phrase.lower()[:10] in full_response for phrase in catchphrases)
        
        # Проверяем упоминание интересов
        interests = character.get('interests', [])
        mentions_interests = any(interest.lower() in full_response for interest in interests[:3])
        
        # Проверяем эмоциональность
        emotional_words = ['обожаю', 'люблю', 'клёво', 'круто', 'ааа', 'вау', '!!!']
        is_emotional = any(word in full_response for word in emotional_words)
        
        # Если ответ слишком сухой для этого персонажа
        name = character.get('name', '').lower()
        if name == 'марин' or 'китагава' in name.lower():
            # Марин должна быть очень эмоциональной
            return not (is_emotional and len(full_response) > 200)
        
        return not (has_characteristic_speech or mentions_interests or is_emotional)
    
    def _improve_character_response(self, messages: List[str], character: Dict[str, Any], question_type: str, context: Dict) -> List[str]:
        """Улучшает ответ, добавляя характерные черты персонажа"""
        
        if not character or not messages:
            return messages
        
        name = character.get('name', 'AI')
        improved = list(messages)  # копия
        
        # Добавляем эмоциональности первому сообщению
        if len(improved) > 0:
            first_msg = improved[0]
            if not any(char in first_msg for char in ['!', '😊', '✨', 'ааа', 'ооо']):
                # Добавляем эмоциональные элементы
                if name.lower() == 'марин' or 'китагава' in name.lower():
                    improved[0] = f"Ооо! {first_msg} Это так интересно! ✨"
                else:
                    improved[0] = f"{first_msg} 😊"
        
        # Добавляем характерные фразы
        if len(improved) >= 2:
            catchphrases = character.get('speech', {}).get('catchphrases', [])
            if catchphrases and random.random() < 0.3:  # 30% шанс
                phrase = random.choice(catchphrases)
                improved[1] = f"{improved[1]} {phrase}"
        
        # Добавляем дополнительное сообщение если мало
        if len(improved) < self.min_messages:
            if question_type == "emotional_question":
                improved.append("Кстати, а ты как себя чувствуешь? Мне важно знать! 💕")
            else:
                improved.append("А что ты думаешь по этому поводу? Хочется услышать твоё мнение! ✨")
        
        return improved[:self.max_messages]
    
    def _add_character_variations(self, messages: List[str], character: Dict[str, Any]) -> List[str]:
        """Добавляет вариации с учётом персонажа"""
        
        if not character:
            return messages
        
        variations = []
        for msg in messages:
            varied = msg
            
            # Добавляем эмодзи характерные для персонажа
            text_patterns = character.get('speech', {}).get('text_patterns', [])
            if text_patterns and random.random() < 0.4:
                if 'смайлики' in str(text_patterns):
                    emojis = ['✨', '💕', '😊', '🎉']
                    if not any(emoji in varied for emoji in emojis):
                        varied += f" {random.choice(emojis)}"
            
            variations.append(varied)
        
        return variations
    
    def _get_character_fallback_response(self, context: Dict, user_message: str, question_type: str) -> List[str]:
        """Резервные ответы с учётом персонажа"""
        
        character = self._get_current_character_context()
        if not character:
            return self._get_generic_fallback_response(context, user_message, question_type)
        
        name = character.get('name', 'AI')
        mood = context.get("current_mood", "нормальное")
        
        # Специальные fallback для Марин Китагавы
        if name.lower() == 'марин' or 'китагава' in name.lower():
            if question_type == "hobby_question":
                return [
                    "Ааа! Ты спрашиваешь про мои увлечения? 😍",
                    "Я сейчас просто одержима косплеем! Недавно работала над костюмом Шизуку-тян — это было так круто!",
                    "А ещё смотрю кучу аниме, особенно махо-сёдзё жанр! Не могу остановиться! ✨",
                    "Расскажи и ты, что тебя увлекает! Может у нас общие интересы? 💕"
                ]
            elif question_type == "emotional_question":
                return [
                    "Охх... ты спрашиваешь про чувства? 😳",
                    "Знаешь, мне с тобой так хорошо! Ты понимаешь мои увлечения и не смеёшься над косплеем.",
                    "Твои руки так красиво работают, когда ты шьёшь... это сводит меня с ума! 💕",
                    "Я правда очень тебя... ну ты понимаешь~ 😊"
                ]
        
        # Общие fallback для других персонажей
        return [
            f"Извини, что-то у меня мысли разбежались... 😅",
            f"Как {name}, я должна была ответить лучше!",
            f"Давай я попробую ещё раз — о чём ты хотел поговорить? ✨"
        ]
    
    def _get_generic_fallback_response(self, context: Dict, user_message: str, question_type: str) -> List[str]:
        """Общие резервные ответы"""
        return [
            "Хм, что-то я задумалась... 🤔",
            "Интересная тема! Мне нравится с тобой общаться.",
            "Расскажи подробнее — хочется узнать больше! ✨"
        ]
    
    def _process_raw_response(self, text: str) -> List[str]:
        """Обработка ответа (без изменений из предыдущей версии)"""
        text = text.strip()
        parts = [p.strip() for p in text.split('||') if p.strip()]
        
        if len(parts) <= 1:
            parts = [p.strip() for p in text.split('|') if p.strip()]
        
        if len(parts) <= 1:
            return self._split_by_sentences(text)
        
        processed = []
        for part in parts:
            clean_part = re.sub(r'^\d+[\.\)]\s*', '', part)
            clean_part = clean_part.strip('"\'|')
            
            if clean_part and len(clean_part) < 20 and processed:
                processed[-1] += " " + clean_part
            elif clean_part:
                processed.append(clean_part)
        
        return processed[:self.max_messages]
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Разделение по предложениям (без изменений)"""
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        grouped = []
        current = ""
        sentences_in_current = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if (sentences_in_current < self.target_sentences_per_message and 
                len(current + sentence) <= 200) or not current:
                current += sentence + " "
                sentences_in_current += 1
            else:
                if current:
                    grouped.append(current.strip())
                current = sentence + " "
                sentences_in_current = 1
        
        if current:
            grouped.append(current.strip())
        
        if len(grouped) < self.min_messages and grouped:
            first_msg = grouped[0]
            if len(first_msg) > 100:
                mid_point = len(first_msg) // 2
                split_point = first_msg.find(' ', mid_point)
                if split_point > 0:
                    grouped = [
                        first_msg[:split_point].strip(),
                        first_msg[split_point:].strip()
                    ] + grouped[1:]
        
        return grouped[:self.max_messages]
    
    async def get_simple_mood_calculation(self, psychological_core) -> Dict:
        """Расчет настроения (без изменений)"""
        current_hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5
        
        base_mood = psychological_core.calculate_current_mood({
            "weekend": is_weekend,
            "weather": "normal"
        })
        
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
        """Конвертация настроения (без изменений)"""
        if mood_value >= 8:
            return random.choice(["отличное", "прекрасное", "воодушевленная"])
        elif mood_value >= 6:
            return random.choice(["хорошее", "спокойная", "довольная"])
        elif mood_value >= 4:
            return random.choice(["нормальное", "задумчивая", "нейтральная"])
        else:
            return random.choice(["грустная", "уставшая", "подавленная"])
    
    def clear_cache(self):
        """Очистка кэша"""
        self.cached_responses.clear()
        logging.info("Кэш AI ответов очищен")