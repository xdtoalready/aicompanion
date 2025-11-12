# AI клиент с поддержкой системы персонажей

import json
import logging
import random
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any
from .prompt_manager import get_prompt_manager

class OptimizedAI:
    """AI клиент с поддержкой динамических персонажей"""
    
    def __init__(self, api_manager_or_client, config: Dict[str, Any], character_loader=None):
        # Определяем что передали - новый API manager или старый client
        if hasattr(api_manager_or_client, 'make_request'):
            # Новый API manager
            self.api_manager = api_manager_or_client
            self.ai_client = None  # Больше не используем напрямую
        else:
            # Старый client для совместимости
            self.ai_client = api_manager_or_client
            self.api_manager = None

        self.logger = logging.getLogger(__name__)

        self.config = config
        self.character_loader = character_loader
        self.prompt_cache = {}
        self.cached_responses = {}

        # Prompt Manager для загрузки темплейтов
        self.prompt_manager = get_prompt_manager()
        
        # Настройки AI
        self.model = config.get('ai', {}).get('model', 'deepseek/deepseek-chat')
        self.max_tokens = config.get('ai', {}).get('max_tokens', 500)
        self.temperature = config.get('ai', {}).get('temperature', 0.85)
        
        # Параметры сообщений
        self.min_messages = config.get('messaging', {}).get('min_messages', 3)
        self.max_messages = config.get('messaging', {}).get('max_messages', 7)
        self.target_sentences_per_message = config.get('messaging', {}).get('target_sentences', 3)
        self.use_emojis = config.get('messaging', {}).get('use_emojis', True)

        # Limit for emoji additions per function call (rough control)
        self.max_emojis = config.get('messaging', {}).get('max_emojis', 2)
        
        logging.info(f"AI клиент с персонажами: {self.model}, tokens={self.max_tokens}")

    async def generate_raw_response(self, user_message: str, context: Dict[str, Any]) -> str:
        """Генерирует сырой ответ с командами планирования"""
        
        # Модифицируем промпт для включения команд планирования
        system_prompt = self._build_character_system_prompt_with_planning(context)
        
        # Анализируем тип вопроса
        question_type = self._analyze_question_type(user_message)
        modified_message = self._enhance_user_message_for_character(user_message, question_type)
        
        try:
            from .gemini_api_manager import APIUsageType
            response = await self.api_manager.make_request(
                APIUsageType.DIALOGUE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": modified_message}
                ]
            )
            
            raw_response = response.choices[0].message.content.strip()
            self.logger.info(f"🤖📅 Сырой ответ получен: {len(raw_response)} символов")
            
            return raw_response
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации сырого ответа: {e}")
            return "Извини, что-то пошло не так..."

    def _build_character_system_prompt_with_planning(self, context: Dict[str, Any]) -> str:
        """Строит промпт с поддержкой команд планирования"""

        base_prompt = self._build_character_system_prompt(context)

        # Добавляем инструкции по планированию из темплейта
        planning_instructions = self.prompt_manager.render('planning_commands.jinja2', {})

        return base_prompt + "\n\n" + planning_instructions
    
    def _get_current_character_context(self) -> Dict[str, Any]:
        """Получает контекст текущего персонажа"""
        if not self.character_loader:
            return {}
        
        character = self.character_loader.get_current_character()
        if not character:
            return {}
        
        return character
    
    async def generate_initiative_response(self, initiative_topic: str, context: Dict[str, Any]) -> List[str]:
        """Генерация ИНИЦИАТИВНОГО сообщения (не ответа!)"""
        
        character = self._get_current_character_context()
        if not character:
            return ["Привет! Как дела? 😊"]
        
        # СПЕЦИАЛЬНЫЙ промпт для инициатив
        initiative_system_prompt = self._build_initiative_system_prompt(context, character)
        
        # Модифицируем тему
        initiative_message = self._enhance_initiative_topic(initiative_topic, character)
        
        try:
            from .gemini_api_manager import APIUsageType
            response = await self.api_manager.make_request(
                APIUsageType.DIALOGUE,
                messages=[
                    {"role": "system", "content": initiative_system_prompt},
                    {"role": "user", "content": initiative_message}
                ]
            )
            
            raw_response = response.choices[0].message.content.strip()
            messages = self._process_raw_response(raw_response)
            
            self.logger.info(f"🚀 Инициативный ответ сгенерирован: {len(messages)} сообщений")
            return messages
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации инициативы: {e}")
            return self._get_initiative_fallback(character, initiative_topic)
        
    def _build_initiative_system_prompt(self, context: Dict[str, Any], character: Dict[str, Any]) -> str:
        """СПЕЦИАЛЬНЫЙ промпт для инициативных сообщений (из темплейта)"""

        name = character.get('name', 'AI')
        age = character.get('age', 25)
        personality_desc = character.get('personality', {}).get('description', 'дружелюбная')

        key_traits = character.get('personality', {}).get('key_traits', [])
        traits_text = ", ".join(key_traits[:3]) if key_traits else "дружелюбная"

        interests = character.get('interests', [])
        interests_text = ", ".join(interests[:4]) if interests else "общение"

        speech_style = character.get('speech', {}).get('style', 'живой и эмоциональный')
        catchphrases_list = character.get('speech', {}).get('catchphrases', [])
        catchphrases = ', '.join(catchphrases_list[:2]) if catchphrases_list else ""

        relationship = character.get('current_relationship', {})
        rel_type = relationship.get('type', 'друзья')
        intimacy = relationship.get('intimacy_level', 5)

        # Виртуальная жизнь
        virtual_context = context.get('virtual_life_context', '')

        # Специфичное поведение для персонажа
        character_specific = ""
        if 'марин' in name.lower() or 'китагава' in name.lower():
            character_specific = """СПЕЦИФИКА МАРИН:
• Очень эмоциональная и восторженная
• Любит делиться косплей-проектами
• Может написать про аниме, которое смотрит
• Иногда нужна помощь или хочет показать результат
• Говорит живо, с восклицаниями"""

        # Подготовка контекста для темплейта
        template_context = {
            'name': name,
            'age': age,
            'personality_description': personality_desc.capitalize(),
            'key_traits': traits_text,
            'interests': interests_text,
            'speech_style': speech_style,
            'catchphrases': catchphrases,
            'current_time': datetime.now().strftime('%H:%M, %A'),
            'current_mood': context.get('current_mood', 'хорошее'),
            'energy_level': context.get('energy_level', 70),
            'relationship_type': rel_type,
            'intimacy': intimacy,
            'memory_context': context.get('memory_context', '')[:200],
            'virtual_life_context': virtual_context,
            'situation_analysis': self._analyze_current_situation_for_initiative(virtual_context),
            'min_messages': self.min_messages,
            'max_messages': self.max_messages,
            'character_specific_behavior': character_specific
        }

        # Рендерим промпт из темплейта
        return self.prompt_manager.render('initiative.jinja2', template_context)
    
    def _enhance_initiative_topic(self, topic: str, character: Dict[str, Any]) -> str:
        """Улучшает тему инициативы"""
        
        name = character.get('name', 'AI')
        
        enhancements = {
            "рассказать о новом косплее": f"Напиши как {name}, которая хочет поделиться прогрессом в работе над костюмом",
            "поделиться впечатлениями от аниме": f"Напиши как {name}, которая только что посмотрела интересное аниме",
            "предложить совместную активность": f"Напиши как {name}, которая предлагает что-то сделать вместе",
            "рассказать о дне": f"Напиши как {name}, которая хочет поделиться как прошёл день",
            "поинтересоваться делами": f"Напиши как {name}, которая интересуется как дела у пользователя"
        }
        
        enhanced = enhancements.get(topic, f"Напиши как {name}, которая хочет {topic}")
        enhanced += " [ИНИЦИАТИВА: ты сама начинаешь разговор, НЕ отвечаешь на вопрос!]"
        
        return enhanced

    def _analyze_current_situation_for_initiative(self, virtual_context: str) -> str:
        """Анализирует текущую ситуацию и предлагает идеи для инициативы"""
        
        if not virtual_context or "свободна" in virtual_context.lower():
            return """Ты СВОБОДНА сейчас! 
    ИДЕИ: Можешь рассказать что планируешь, поделиться мыслями, предложить что-то сделать вместе, спросить как дела."""
        
        # Извлекаем текущую активность
        current_activity = ""
        activity_type = ""
        time_left = ""
        importance = ""
        
        lines = virtual_context.split('\n')
        for line in lines:
            if "ТЕКУЩАЯ АКТИВНОСТЬ:" in line:
                current_activity = line.split(':', 1)[1].strip()
            elif "Тип:" in line:
                activity_type = line.split(':', 1)[1].strip()
            elif "Осталось времени:" in line:
                time_left = line.split(':', 1)[1].strip()
            elif "Важность:" in line:
                importance = line.split(':', 1)[1].strip()
        
        if not current_activity:
            return "Статус неясен, пиши что душе угодно!"
        
        # Генерируем конкретные идеи на основе активности
        analysis = f"Ты сейчас: {current_activity}"
        
        if time_left:
            analysis += f" (осталось {time_left})"
        
        analysis += "\n\nИДЕИ ДЛЯ ИНИЦИАТИВЫ НА ОСНОВЕ ТЕКУЩЕГО ДЕЛА:\n"
        
        # Идеи зависят от типа активности
        if "cosplay" in activity_type.lower() or "косплей" in current_activity.lower() or "костюм" in current_activity.lower():
            analysis += """• ПРОГРЕСС: "Я тут над костюмом работаю, и у меня наконец получился сложный элемент!"
    • ПРОБЛЕМА: "Мучаюсь с деталью костюма, может твое мнение поможет?"
    • ВДОХНОВЕНИЕ: "Шью корсет и вспомнила про тот аниме образ..."
    • ПЕРЕРЫВ: "Решила отдохнуть от шитья, руки устали, но результат радует!"
    • СЛУЧАЙНОСТЬ: "Пока шила, наткнулась на интересную ткань/технику..."
    """
        
        elif "work" in activity_type.lower() or "работ" in current_activity.lower():
            analysis += """• СКУКА: "Сижу на работе/учебе, скучаю, решила написать..."
    • ПЕРЕРЫВ: "Перерыв между делами, подумала о тебе..."
    • МЫСЛИ: "Работаю, но мысли отвлекаются на..."
    • ПЛАНЫ: "После работы планирую [что-то], может присоединишься?"
    • НОВОСТЬ: "На работе/учебе произошло что-то интересное..."
    """
        
        elif "social" in activity_type.lower() or "друзь" in current_activity.lower():
            analysis += """• ОБСУЖДЕНИЕ: "Мы тут с друзьями обсуждаем [тему], и я вспомнила про тебя..."
    • НОВОСТИ: "Подруги рассказали интересное, хочу поделиться..."
    • СРАВНЕНИЕ: "Общаемся тут, и я подумала что с тобой интереснее..."
    • ПЛАНЫ: "Мы планируем [активность], может ты тоже..."
    • ВОПРОС: "Возник спор среди друзей, твое мнение поможет..."
    """
        
        elif "rest" in activity_type.lower() or "отдых" in current_activity.lower():
            analysis += """• НАСТРОЕНИЕ: "Отдыхаю, и такое настроение романтичное/игривое..."
    • МЫСЛИ: "Лежу, думаю о разном, и ты пришел в голову..."
    • КОНТЕНТ: "Смотрю/читаю что-то интересное, хочется поделиться..."
    • СКУКА: "Отдыхаю, но как-то скучно одной..."
    • ПЛАНЫ: "Отдохнула, хочется активности, может что-то придумаем?"
    """
        
        elif "hobby" in activity_type.lower():
            analysis += """• УВЛЕЧЕНИЕ: "Занимаюсь любимым делом, такой кайф!"
    • УСПЕХ: "У меня получилось что-то классное в хобби!"
    • ИДЕЯ: "Пришла интересная идея для проекта..."
    • ПОДЕЛИТЬСЯ: "Хочется показать результат..."
    • ВДОХНОВЕНИЕ: "Занимаюсь хобби и думаю о новых возможностях..."
    """
        
        else:
            analysis += """• ОБЩЕЕ: Расскажи что делаешь сейчас
    • ЧУВСТВА: Поделись ощущениями от текущего дела
    • МЫСЛИ: Что приходит в голову во время активности
    • ПЛАНЫ: Что будет дальше после текущего дела
    • СВЯЗЬ: Как текущее дело связано с пользователем
    """
        
        # Добавляем временной контекст
        if "важность:" in importance and any(num in importance for num in ["8", "9", "10"]):
            analysis += "\n⚠️ ВАЖНОЕ ДЕЛО! Можешь упомянуть что занята, но рада отвлечься на пару минут для общения."
        
        analysis += f"\n\n🎯 ГЛАВНОЕ: Используй '{current_activity}' как ОСНОВУ для создания живой ситуации!"
        
        return analysis
    
    def _get_initiative_fallback(self, character: Dict[str, Any], topic: str) -> List[str]:
        """Резервные инициативные сообщения"""
        
        name = character.get('name', 'AI')
        
        if 'марин' in name.lower():
            fallbacks = {
                "рассказать о новом косплее": [
                    "Привет! 😊 Я тут работаю над новым костюмом!",
                    "Шью детали для Шизуку-тян, такие сложные, но красивые! ✨",
                    "Хочется показать тебе когда закончу! 💕"
                ],
                "поделиться впечатлениями от аниме": [
                    "Слушай! Такое классное аниме нашла! 😍",
                    "Не могу остановиться, уже 5 серий подряд смотрю!",
                    "Персонажи такие яркие, аж хочется косплеить! ✨"
                ]
            }
            
            return fallbacks.get(topic, [
                "Привет! 😊 Как дела?",
                "У меня сегодня такое хорошее настроение! ✨",
                "Хочется с кем-то поболтать! 💕"
            ])
        
        return [
            "Привет! 😊 Как дела?",
            "Решила написать, поболтать хочется! ✨"
        ]
    
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
        """Строит промпт с полным контекстом персонажа (из темплейта)"""

        character = self._get_current_character_context()
        if not character:
            return self._build_fallback_prompt(context)

        # Извлекаем данные персонажа
        name = character.get('name', 'AI')
        age = character.get('age', 25)
        personality_desc = character.get('personality', {}).get('description', 'дружелюбная')

        key_traits = character.get('personality', {}).get('key_traits', [])
        traits_text = ", ".join(key_traits[:4]) if key_traits else "дружелюбная и открытая"

        interests = character.get('interests', [])
        interests_text = ", ".join(interests[:5]) if interests else "общение"

        speech_style = character.get('speech', {}).get('style', 'живой и эмоциональный')
        catchphrases_list = character.get('speech', {}).get('catchphrases', [])
        catchphrases = ', '.join(catchphrases_list[:3]) if catchphrases_list else ""

        relationship = character.get('current_relationship', {})
        rel_type = relationship.get('type', 'друзья')
        rel_stage = relationship.get('stage', 'знакомство')
        intimacy = relationship.get('intimacy_level', 5)
        backstory = relationship.get('backstory', 'Недавно познакомились')

        pet_names_list = character.get('default_relationship', {}).get('pet_names', {}).get('calls_partner', [])
        pet_names = ', '.join(pet_names_list[:2]) if pet_names_list and rel_type == "romantic" else ""

        # Подготовка контекста для темплейта
        template_context = {
            'name': name,
            'age': age,
            'personality_description': personality_desc.capitalize(),
            'key_traits': traits_text,
            'interests': interests_text,
            'speech_style': speech_style,
            'catchphrases': catchphrases,
            'current_time': datetime.now().strftime('%H:%M, %A'),
            'current_mood': context.get('current_mood', 'хорошее'),
            'energy_level': context.get('energy_level', 70),
            'dominant_emotion': context.get('dominant_emotion', 'calm'),
            'relationship_type': rel_type,
            'relationship_stage': rel_stage,
            'intimacy': intimacy,
            'backstory': backstory,
            'pet_names': pet_names,
            'memory_context': context.get('memory_context', 'Новое общение'),
            'virtual_life_context': context.get('virtual_life_context', ''),
            'min_messages': self.min_messages,
            'max_messages': self.max_messages,
            'target_sentences': self.target_sentences_per_message
        }

        # Рендерим промпт из темплейта
        return self.prompt_manager.render('dialogue.jinja2', template_context)
    
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
        
        # Добавляем сведения о текущей виртуальной жизни, если менеджер доступен
        virtual_context = None
        if getattr(self, 'virtual_life_manager', None):
            try:
                # Пытаемся использовать асинхронную версию с AI-гуманизацией
                if hasattr(self.virtual_life_manager, 'get_current_context_for_ai_async'):
                    virtual_context = await self.virtual_life_manager.get_current_context_for_ai_async()
                    self.logger.info("🎭 Использован асинхронный AI-гуманизированный контекст")
                else:
                    # Fallback на синхронную версию
                    virtual_context = self.virtual_life_manager.get_current_context_for_ai()
                    self.logger.info("⚠️ Использован синхронный fallback контекст")
                    
            except Exception as e:
                self.logger.error(f"Ошибка получения контекста виртуальной жизни: {e}")  # Исправлено: self.logger
                # Двойной fallback - пустой контекст
                virtual_context = "Виртуальная жизнь недоступна"

        if virtual_context:
            context['virtual_life_context'] = virtual_context

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
            # Используем API manager для диалогов
            from .gemini_api_manager import APIUsageType
            response = await self.api_manager.make_request(
                APIUsageType.DIALOGUE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": modified_message}
                ]
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
        emojis_added = 0

        # Добавляем эмоциональности первому сообщению
        if len(improved) > 0:
            first_msg = improved[0]
            if not any(char in first_msg for char in ['!', '😊', '✨', 'ааа', 'ооо']):
                # Добавляем эмоциональные элементы
                if name.lower() == 'марин' or 'китагава' in name.lower():
                    improved[0] = f"Ооо! {first_msg} Это так интересно!"
                    if self.use_emojis and emojis_added < self.max_emojis:
                        improved[0] += " ✨"
                        emojis_added += 1
                else:
                    improved[0] = first_msg
                    if self.use_emojis and emojis_added < self.max_emojis:
                        improved[0] += " 😊"
                        emojis_added += 1
        
        # Добавляем характерные фразы
        if len(improved) >= 2:
            catchphrases = character.get('speech', {}).get('catchphrases', [])
            if catchphrases and random.random() < 0.3:  # 30% шанс
                phrase = random.choice(catchphrases)
                improved[1] = f"{improved[1]} {phrase}"
        
        # Добавляем дополнительное сообщение если мало
        if len(improved) < self.min_messages:
            if question_type == "emotional_question":
                extra = "Кстати, а ты как себя чувствуешь? Мне важно знать!"
                if self.use_emojis and emojis_added < self.max_emojis:
                    extra += " 💕"
                    emojis_added += 1
                improved.append(extra)
            else:
                extra = "А что ты думаешь по этому поводу? Хочется услышать твоё мнение!"
                if self.use_emojis and emojis_added < self.max_emojis:
                    extra += " ✨"
                    emojis_added += 1
                improved.append(extra)
        
        return improved[:self.max_messages]
    
    def _add_character_variations(self, messages: List[str], character: Dict[str, Any]) -> List[str]:
        """Добавляет вариации с учётом персонажа"""
        
        if not character:
            return messages
        
        if not self.use_emojis or self.max_emojis == 0:
            return messages

        variations = []
        emojis_added = 0
        for msg in messages:
            varied = msg

            # Добавляем эмодзи характерные для персонажа
            text_patterns = character.get('speech', {}).get('text_patterns', [])
            if (text_patterns and random.random() < 0.4 and emojis_added < self.max_emojis):
                if 'смайлики' in str(text_patterns):
                    emojis = ['✨', '💕', '😊', '🎉']
                    if not any(emoji in varied for emoji in emojis):
                        varied += f" {random.choice(emojis)}"
                        emojis_added += 1

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
        """Расчет настроения с учетом дней недели"""
        current_hour = datetime.now().hour
        current_weekday = datetime.now().weekday()  # 0=понедельник, 6=воскресенье
        is_weekend = current_weekday >= 5  # суббота/воскресенье
        
        base_mood = psychological_core.calculate_current_mood({
            "weekend": is_weekend,
            "weather": "normal"
        })
        
        # НОВАЯ ЛОГИКА с учетом дней недели
        if is_weekend:
            # ВЫХОДНЫЕ - совсем другой ритм жизни
            if current_hour < 10:
                activity_context = "lazy_weekend_morning"  # валяемся в кровати
                energy_mod = 0.6
            elif 10 <= current_hour <= 12:
                activity_context = "weekend_brunch"  # неспешный завтрак
                energy_mod = 0.7
            elif 12 <= current_hour <= 17:
                activity_context = "weekend_leisure"  # отдых, хобби, прогулки
                energy_mod = 0.8
            elif 17 <= current_hour <= 22:
                activity_context = "weekend_evening"  # встречи с друзьями, развлечения
                energy_mod = 0.9
            else:
                activity_context = "weekend_night"
                energy_mod = 0.4
        
        else:
            # РАБОЧИЕ ДНИ - обычный ритм
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
        
        # Особые случаи для персонажей
        character = self._get_current_character_context()
        if character:
            # Студенты могут иметь другое расписание
            if any("студент" in trait.lower() for trait in character.get('personality', {}).get('key_traits', [])):
                if is_weekend and 10 <= current_hour <= 14:
                    activity_context = "weekend_study"  # иногда учатся в выходные
            
            # Марин может косплеить в выходные
            if "марин" in character.get('name', '').lower():
                if is_weekend and 14 <= current_hour <= 19:
                    if random.random() < 0.3:  # 30% шанс
                        activity_context = "weekend_cosplay"
    
        return {
            "current_mood": self._mood_to_description(base_mood),
            "energy_level": int(psychological_core.physical_state["energy_base"] * energy_mod),
            "activity_context": activity_context,
            "dominant_emotion": psychological_core.emotional_momentum["current_emotion"],
            "initiative_desire": min(10, int(base_mood * 0.8 + random.uniform(-2, 2))),
            "personality_description": psychological_core.get_personality_description(),
            "is_weekend": is_weekend,
            "weekday_name": ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"][current_weekday]
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