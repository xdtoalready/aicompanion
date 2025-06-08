# Основной модуль AI-компаньона с многосообщенческими ответами

from .character_loader import character_loader
import asyncio
import json
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .virtual_life import VirtualLifeManager, VirtualActivity

# Добавляем корневой путь в sys.path ОДИН РАЗ
sys.path.append(str(Path(__file__).parent.parent.parent))

# Относительные импорты для модулей внутри core
from .psychology import PsychologicalCore
from .memory import AdvancedMemorySystem
from .ai_client import OptimizedAI
from .typing_simulator import TypingSimulator, TypingIndicator

# Импорт консолидации памяти
from .memory_consolidation import EmotionalMemoryConsolidator, enhance_existing_memories_with_emotions

# Абсолютный импорт для database (так как sys.path добавлен)
from app.database.memory_manager import EnhancedMemorySystem

class RealisticAICompanion:
    """Реалистичный AI-компаньон с многосообщенческими ответами"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        self.psychological_core = PsychologicalCore()
        
        # База данных для памяти
        db_path = config.get('database', {}).get('path', 'data/companion.db')
        self.enhanced_memory = EnhancedMemorySystem(db_path)
        
        # Оставляем старую систему для совместимости
        self.memory_system = AdvancedMemorySystem()
        
        # НОВОЕ: Инициализируем загрузчик персонажей
        global character_loader
        
        # Загружаем персонажа по умолчанию если ещё не загружен
        if not character_loader.get_current_character():
            available_chars = character_loader.get_available_characters()
            if available_chars:
                # Загружаем первого доступного персонажа
                character_loader.load_character(available_chars[0]['id'])
                self.logger.info(f"Автоматически загружен персонаж: {available_chars[0]['name']}")
        
        # AI клиент
        self.ai_client = AsyncOpenAI(
            api_key=config['ai']['openrouter_api_key'],
            base_url="https://openrouter.ai/api/v1"
        )
        
        # ИЗМЕНЕНО: Передаём character_loader в AI клиент
        self.optimized_ai = OptimizedAI(self.ai_client, config, character_loader)
        
        # Система печатания
        typing_config = config.get('typing', {})
        self.typing_simulator = TypingSimulator({
            'typing_mode': typing_config.get('mode', 'fast'),
            'show_typing_indicator': typing_config.get('show_typing_indicator', True),
            'natural_pauses': typing_config.get('natural_pauses', True)
        })
        self.typing_indicator = TypingIndicator()

        # Система виртуальной жизни
        self.virtual_life = VirtualLifeManager(
            db_path=config.get('database', {}).get('path', 'data/companion.db'),
            character_loader=character_loader,
        )
        
        # Планировщик
        self.scheduler = AsyncIOScheduler()
        
        # Состояние
        self.last_message_time = None
        self.daily_message_count = 0
        self.conversation_history = []
        
        self.commands_enabled = True
        
        self.emotional_memory_consolidator = EmotionalMemoryConsolidator(
            db_path=db_path,
            ai_client=self.ai_client,
            config=config
        )

        self.setup_realistic_scheduler()

    def get_current_character_info(self) -> Dict[str, Any]:
        """Получает информацию о текущем персонаже"""
        character = character_loader.get_current_character()
        if not character:
            return {
                "name": "AI",
                "loaded": False,
                "error": "Персонаж не загружен"
            }
        
        return {
            "name": character.get('name', 'Неизвестно'),
            "age": character.get('age', 'Неизвестно'),
            "description": character.get('personality', {}).get('description', ''),
            "relationship_type": character.get('current_relationship', {}).get('type', 'неопределенный'),
            "intimacy_level": character.get('current_relationship', {}).get('intimacy_level', 0),
            "loaded": True,
            "file_id": character.get('id', 'unknown')
        }
    
    def setup_realistic_scheduler(self):
        """Настройка реалистичного планировщика"""
        
        # Проверка желания написать каждые 5 минут
        self.scheduler.add_job(
            self.consciousness_cycle,
            IntervalTrigger(minutes=5),
            id='consciousness'
        )
        
        # Остальные задачи остаются без изменений...
        self.scheduler.add_job(
            self.run_emotional_memory_consolidation,
            IntervalTrigger(hours=6),
            id='emotional_memory_consolidation'
        )
        
        # Глубокая эмоциональная консолидация раз в день
        self.scheduler.add_job(
            self.deep_emotional_consolidation,
            IntervalTrigger(days=1),
            id='deep_emotional_consolidation'
        )
        
        # Анализ эмоций новых воспоминаний каждые 2 часа
        self.scheduler.add_job(
            self.analyze_recent_memories_emotions,
            IntervalTrigger(hours=2),
            id='emotion_analysis'
        )

        # Обновление виртуальной жизни персонажа каждые минуту
        self.scheduler.add_job(
            self.update_virtual_life,
            IntervalTrigger(minutes=1),
            id='virtual_life_update'
        )

        self.scheduler.start()

    async def run_memory_consolidation(self):
        """Запуск автоматической консолидации памяти"""
        try:
            self.logger.info("🧠 Запуск консолидации памяти...")
            await self.emotional_memory_consolidator.run_emotional_consolidation_cycle()
        except Exception as e:
            self.logger.error(f"Ошибка консолидации памяти: {e}")

    async def deep_memory_consolidation(self):
        """Глубокая консолидация и анализ воспоминаний"""
        try:
            # Обычная консолидация
            await self.emotional_memory_consolidator.run_emotional_consolidation_cycle()
            
            # Дополнительный анализ паттернов
            await self._analyze_memory_patterns()
            
        except Exception as e:
            self.logger.error(f"Ошибка глубокой консолидации: {e}")

    async def run_emotional_memory_consolidation(self):
        """Запуск эмоциональной консолидации"""
        try:
            self.logger.info("🧠💕 Запуск эмоциональной консолидации...")
            await self.emotional_memory_consolidator.run_emotional_consolidation_cycle()
        except Exception as e:
            self.logger.error(f"Ошибка эмоциональной консолидации: {e}")

    async def deep_emotional_consolidation(self):
        """Глубокая эмоциональная консолидация"""
        try:
            # Основная консолидация
            await self.emotional_memory_consolidator.run_emotional_consolidation_cycle()
            
            # Анализ эмоциональных паттернов пользователя
            await self._analyze_emotional_patterns()
            
            # Обновление эмоциональных меток старых воспоминаний
            await enhance_existing_memories_with_emotions(
                self.enhanced_memory.db_manager.db_path,
                self.ai_client,
                self.config
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка глубокой эмоциональной консолидации: {e}")

    async def analyze_recent_memories_emotions(self):
        """Анализирует эмоции недавних воспоминаний"""
        try:
            # Улучшаем воспоминания без эмоциональных меток
            await enhance_existing_memories_with_emotions(
                self.enhanced_memory.db_manager.db_path,
                self.ai_client,
                self.config
            )
        except Exception as e:
            self.logger.error(f"Ошибка анализа эмоций: {e}")

    async def _analyze_emotional_patterns(self):
        """Анализирует эмоциональные паттерны пользователя"""
        
        try:
            import sqlite3
            with sqlite3.connect(self.enhanced_memory.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем эмоциональную статистику за последний месяц
                month_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute("""
                    SELECT emotion_type, COUNT(*), AVG(emotional_intensity), AVG(importance)
                    FROM memories 
                    WHERE created_at >= ? AND emotion_type IS NOT NULL
                    GROUP BY emotion_type
                    ORDER BY COUNT(*) DESC
                """, (month_ago,))
                
                emotional_patterns = cursor.fetchall()
                
                if not emotional_patterns:
                    return
                
                # Создаём анализ для AI
                pattern_text = "Эмоциональные паттерны пользователя за месяц:\n"
                for emotion, count, avg_intensity, avg_importance in emotional_patterns:
                    pattern_text += f"- {emotion}: {count} раз (интенсивность {avg_intensity:.1f}, важность {avg_importance:.1f})\n"
                
                # Анализируем что это значит для отношений
                analysis_prompt = """Проанализируй эмоциональные паттерны пользователя в общении с AI-компаньоном.
                
Определи:
1. Какие эмоции доминируют?
2. Что это говорит о личности пользователя?
3. Как можно улучшить взаимодействие?
4. На что обращать внимание в будущем?

Ответь кратко, 2-3 предложения на каждый пункт."""

                response = await self.ai_client.chat.completions.create(
                    model=self.config.get('ai', {}).get('model'),
                    messages=[
                        {"role": "system", "content": analysis_prompt},
                        {"role": "user", "content": pattern_text}
                    ],
                    max_tokens=400,
                    temperature=0.3
                )
                
                analysis = response.choices[0].message.content.strip()
                
                # Сохраняем анализ как специальное воспоминание
                cursor.execute("""
                    INSERT INTO memories 
                    (character_id, memory_type, content, importance, 
                     emotional_intensity, emotion_type, is_consolidated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    1,
                    "emotional_analysis",
                    f"Эмоциональный анализ пользователя: {analysis}",
                    9,  # Высокая важность
                    7.0,  # Средне-высокая интенсивность
                    "analytical",
                    True
                ))
                
                conn.commit()
                
                self.logger.info("🔍💕 Эмоциональный анализ пользователя сохранён")
                
        except Exception as e:
            self.logger.error(f"Ошибка анализа эмоциональных паттернов: {e}")

    async def _analyze_memory_patterns(self):
        """Анализирует паттерны в воспоминаниях для улучшения отношений"""
        
        # Получаем консолидированные воспоминания
        consolidated_memories = self._get_consolidated_memories()
        
        if not consolidated_memories:
            return
        
        # Анализируем что важно для пользователя
        analysis_prompt = """Проанализируй воспоминания AI-компаньона о пользователе.
        Определи:
        1. Основные интересы и предпочтения
        2. Паттерны поведения и общения  
        3. Что важно для пользователя в отношениях
        4. Как можно улучшить взаимодействие
        
        Ответь кратко, 2-3 предложения на каждый пункт."""
        
        try:
            response = await self.ai_client.chat.completions.create(
                model=self.config.get('ai', {}).get('model'),
                messages=[
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": f"Воспоминания:\n{consolidated_memories}"}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content.strip()
            
            # Сохраняем анализ как специальное воспоминание
            self._save_memory_analysis(analysis)
            
            self.logger.info("🔍 Анализ паттернов памяти завершён")
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа паттернов: {e}")

    def _get_consolidated_memories(self) -> str:
        """Получает консолидированные воспоминания для анализа"""
        try:
            import sqlite3
            with sqlite3.connect(self.enhanced_memory.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT content FROM memories 
                    WHERE is_consolidated = 1 
                    AND consolidation_level IN ('medium_term', 'long_term')
                    ORDER BY importance DESC, last_consolidated DESC
                    LIMIT 20
                """)
                
                memories = [row[0] for row in cursor.fetchall()]
                return "\n".join(memories)
                
        except Exception as e:
            self.logger.error(f"Ошибка получения консолидированных воспоминаний: {e}")
            return ""
        
    def _save_memory_analysis(self, analysis: str):
        """Сохраняет результат анализа памяти"""
        try:
            self.enhanced_memory.add_conversation(
                "[АНАЛИЗ_ПАМЯТИ]", 
                [analysis], 
                "analytical", 
                "insightful"
            )
        except Exception as e:
            self.logger.error(f"Ошибка сохранения анализа: {e}")
    
    async def consciousness_cycle(self):
        """Реалистичный цикл сознания с многосообщенческими инициативами"""
        
        try:
            current_time = datetime.now()
            
            # Не активен ночью (23:00 - 7:00)
            if current_time.hour >= 23 or current_time.hour < 7:
                return
            
            # Ограничение сообщений в день
            max_daily = self.config.get('behavior', {}).get('max_daily_initiatives', 8)
            if self.daily_message_count >= max_daily:
                return
            
            # Обновляем эмоциональное состояние
            self.psychological_core.decay_emotions(30)  # 30 минут прошло
            
            # Простой расчет состояния (экономим токены)
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            
            # Решение об инициативе
            should_initiate = await self._should_initiate_realistically(current_state)
            
            if should_initiate:
                await self.send_initiative_messages(current_state)  # ИЗМЕНЕНО: теперь множественные
                self.daily_message_count += 1
            
            # Иногда генерируем жизненные события
            if random.random() < 0.15:  # 15% шанс
                await self.generate_life_event()
                
        except Exception as e:
            self.logger.error(f"Ошибка в цикле сознания: {e}")
    
    async def _should_initiate_realistically(self, current_state: Dict) -> bool:
        """Улучшенное решение об инициативе с учетом времени"""
        
        initiative_desire = current_state.get("initiative_desire", 0)
        
        # Базовые условия (более мягкие для частых проверок)
        if initiative_desire < 3:  # Было 4, теперь 3
            return False
        
        # Проверяем время последнего сообщения
        min_hours = self.config.get('behavior', {}).get('min_hours_between_initiatives', 2)
        if self.last_message_time:
            hours_since = (datetime.now() - self.last_message_time).total_seconds() / 3600
            if hours_since < min_hours:
                return False
        
        # Учитываем контекст времени
        current_hour = datetime.now().hour
        activity_context = current_state.get("activity_context")
        
        # НОВОЕ: Более активное поведение в определенные часы
        peak_hours = [9, 12, 16, 19, 22]  # Часы пик активности
        if current_hour in peak_hours:
            initiative_desire += 1
        
        # Рабочее время - реже пишет, но не полностью блокирует
        if activity_context == "work_time":
            if random.random() < 0.8:  # Было 0.7, стало 0.8 (меньше блокировки)
                return False
        
        # Вечер - больше желания общаться
        if activity_context == "evening_time":
            initiative_desire += 2
        
        # НОВОЕ: Учитываем персонажа (Марин более активная)
        character = character_loader.get_current_character()
        if character and 'марин' in character.get('name', '').lower():
            initiative_desire += 1  # Марин чаще пишет
        
        # Финальная проверка с рандомом (более мягкая для частых проверок)
        threshold = 5 - (initiative_desire * 0.4)  # Немного понизили порог
        return random.random() > (threshold / 10)

    async def update_virtual_life(self):
        """Обновляет виртуальную жизнь персонажа"""
        try:
            changes = self.virtual_life.check_and_update_activities()

            if changes["status_changed"]:
                if changes["activity_started"]:
                    activity = changes["activity_started"]
                    await self._notify_activity_start(activity)

                if changes["activity_ended"]:
                    activity = changes["activity_ended"]
                    await self.virtual_life._notify_activity_end(activity)

        except Exception as e:
            self.logger.error(f"Ошибка обновления виртуальной жизни: {e}")

    async def _notify_activity_start(self, activity: VirtualActivity):
        """Уведомляет о начале активности"""
        messages = [
            f"Кстати, я сейчас {activity.description}! ✨",
            f"Буду {activity.activity_type} до {activity.end_time.strftime('%H:%M')}",
            "Но ты всегда можешь мне писать! 💕",
        ]

        if hasattr(self, 'allowed_users') and self.allowed_users:
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )

            for user_id in self.allowed_users:
                try:
                    await self.send_telegram_messages_with_timing(
                        chat_id=user_id,
                        messages=messages,
                        current_state=current_state,
                    )
                except Exception as e:
                    self.logger.error(f"Ошибка отправки уведомления активности: {e}")

    async def _notify_activity_end(self, activity: VirtualActivity):
        """Уведомляет о завершении активности"""
        messages = [
            f"Я закончила {activity.description}.",
            "Теперь я свободна пообщаться!",
        ]

        if hasattr(self, 'allowed_users') and self.allowed_users:
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )

            for user_id in self.allowed_users:
                try:
                    await self.send_telegram_messages_with_timing(
                        chat_id=user_id,
                        messages=messages,
                        current_state=current_state,
                    )
                except Exception as e:
                    self.logger.error(f"Ошибка отправки уведомления активности: {e}")
    
    async def create_automatic_schedule(self):
        """Создает автоматическое расписание для персонажа"""
        
        character = character_loader.get_current_character()
        if not character:
            return
        
        name = character.get('name', '').lower()
        
        # Базовое расписание для всех персонажей
        base_schedule = [
            ("work", "работаю/учусь", 9, 5, 1.0, 40),  # 9 утра, 5 часов
            ("rest", "отдыхаю дома", 14, 1, 0.5, 10),   # 14:00, 1 час
            ("hobby", "занимаюсь хобби", 16, 2, 2.0, 30), # 16:00, 2 часа
            ("social", "общаюсь с друзьями", 19, 1.5, 1.5, 20) # 19:00, 1.5 часа
        ]
        
        # Специальное расписание для Марин
        if 'марин' in name or 'китагава' in name:
            cosplay_schedule = [
                ("cosplay", "работаю над новым костюмом", 15, 3, 2.5, 35),
                ("cosplay", "фотосессия в готовом костюме", 11, 2, 3.0, 25),
                ("social", "иду на аниме-конвент", 10, 6, 3.0, 50),
                ("hobby", "смотрю новое аниме", 20, 2, 2.0, 15)
            ]
            base_schedule.extend(cosplay_schedule)
        
        # Планируем на следующие 3 дня
        for day_offset in range(1, 4):
            target_date = datetime.now() + timedelta(days=day_offset)
            
            # Выбираем случайные активности для этого дня
            daily_activities = random.sample(base_schedule, k=random.randint(2, 4))
            
            for activity_type, description, start_hour, duration, mood_effect, energy_cost in daily_activities:
                start_time = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                
                # Добавляем случайность ±30 минут
                start_time += timedelta(minutes=random.randint(-30, 30))
                
                self.virtual_life.schedule_activity(
                    activity_type=activity_type,
                    description=description,
                    start_time=start_time,
                    duration_hours=duration,
                    mood_effect=mood_effect,
                    energy_cost=energy_cost
                )
        
        self.logger.info("📅 Автоматическое расписание создано на 3 дня")
    
    async def send_initiative_messages(self, current_state: Dict):
        """Отправка инициативных сообщений с БД контекстом"""
        
        # НОВОЕ: Получаем контекст из базы данных
        db_context = self.enhanced_memory.get_context_for_response("инициативное общение")
        current_state['memory_context'] = db_context
        
        try:
            # Генерируем множественные сообщения
            messages = await self.optimized_ai.generate_split_response(
                "Хочу написать пользователю что-то интересное", 
                current_state
            )
            
            # Доставляем сообщения
            await self.deliver_messages_with_timing(
                messages, 
                current_state, 
                message_type="initiative"
            )
            
            # Сохраняем в БД как инициативный диалог
            mood_current = current_state.get('dominant_emotion', 'calm')
            self.enhanced_memory.add_conversation(
                "[ИНИЦИАТИВА]", messages, mood_current, mood_current
            )
            
            # Обновляем состояние
            self.psychological_core.update_emotional_state("positive_interaction", 0.5)
            self.last_message_time = datetime.now()
            
            self.logger.info(f"Инициативные сообщения отправлены: {len(messages)} шт.")
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации инициативы: {e}")
    
    # Добавляем новый метод для получения статистики БД:
    def get_database_stats(self) -> Dict[str, Any]:
        """Статистика базы данных"""
        try:
            summary = self.enhanced_memory.get_conversation_summary()
            return {
                "database_enabled": True,
                "recent_conversations": summary['recent_conversations'],
                "total_memories": summary['total_memories'],
                "last_conversation": summary['last_conversation']
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики БД: {e}")
            return {
                "database_enabled": False,
                "error": str(e)
            }

    async def process_user_message(self, message: str) -> List[str]:
        """Обработка сообщения пользователя с учётом персонажа"""
        
        try:
            # Получаем настроение ДО обработки
            mood_before = self.psychological_core.emotional_momentum["current_emotion"]
            
            # Обновляем эмоциональное состояние от получения сообщения
            self.psychological_core.update_emotional_state("positive_interaction", 1.0)
            
            # Получаем текущее состояние
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            
            # Получаем контекст из базы данных
            db_context = self.enhanced_memory.get_context_for_response(message)
            current_state['memory_context'] = db_context
            
            # НОВОЕ: Добавляем контекст персонажа
            character_context = character_loader.get_character_context_for_ai()
            current_state['character_context'] = character_context
            
            self.logger.info(f"Контекст персонажа: {character_context[:100]}...")
            
            # Генерируем ответ с полным контекстом
            ai_messages = await self.optimized_ai.generate_split_response(message, current_state)
            
            # Получаем настроение ПОСЛЕ обработки
            mood_after = self.psychological_core.emotional_momentum["current_emotion"]
            
            # Сохраняем диалог в базу данных
            conversation_id = self.enhanced_memory.add_conversation(
                message, ai_messages, mood_before, mood_after
            )
            
            # НОВОЕ: Обновляем прогресс отношений с персонажем
            character = character_loader.get_current_character()
            if character:
                # Увеличиваем близость при позитивном общении
                current_intimacy = character.get('current_relationship', {}).get('intimacy_level', 1)
                if mood_after in ['happy', 'excited', 'content'] and random.random() < 0.1:  # 10% шанс
                    new_intimacy = min(10, current_intimacy + 0.1)
                    character_loader.update_relationship_progress({
                        'intimacy_level': new_intimacy,
                        'last_positive_interaction': datetime.now().isoformat()
                    })
                    self.logger.info(f"Близость увеличена до {new_intimacy:.1f}")
            
            self.logger.info(f"Диалог сохранен в БД с ID: {conversation_id}")
            
            # Сохраняем также в локальную историю для совместимости
            await self.save_conversation(message, ai_messages)
            
            self.last_message_time = datetime.now()
            return ai_messages
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            # Fallback с учётом персонажа
            character = character_loader.get_current_character()
            if character and 'марин' in character.get('name', '').lower():
                return ["Ой! 😅 Что-то пошло не так...", "Попробуй написать ещё раз! ✨"]
            else:
                return ["Извини, что-то пошло не так... 😅 Попробуй еще раз!"]
            
    # МЕТОД ДЛЯ ИНИЦИАТИВНЫХ СООБЩЕНИЙ С УЧЁТОМ ПЕРСОНАЖА:
    async def send_initiative_messages(self, current_state: Dict):
        """Отправка инициативных сообщений с учётом персонажа"""
        
        # Получаем контекст из базы данных
        db_context = self.enhanced_memory.get_context_for_response("инициативное общение")
        current_state['memory_context'] = db_context
        
        # НОВОЕ: Добавляем контекст персонажа
        character_context = character_loader.get_character_context_for_ai()
        current_state['character_context'] = character_context
        
        # Получаем текущего персонажа для специальных тем
        character = character_loader.get_current_character()
        initiative_prompt = "Хочу написать пользователю что-то интересное"
        
        if character:
            # Специальные темы для инициатив в зависимости от персонажа
            initiative_topics = character.get('behavior', {}).get('initiative_topics', [])
            if initiative_topics:
                topic = random.choice(initiative_topics)
                initiative_prompt = f"Хочу {topic}"
                
            # Для Марин - особые инициативы
            if 'марин' in character.get('name', '').lower():
                special_topics = [
                    "рассказать о новом косплее который планирую",
                    "поделиться впечатлениями от аниме которое смотрела",
                    "предложить вместе поработать над костюмом",
                    "рассказать о смешном случае на конвенции",
                    "спросить мнение о новом наряде"
                ]
                initiative_prompt = f"Хочу {random.choice(special_topics)}"
        
        try:
            # Генерируем множественные сообщения
            messages = await self.optimized_ai.generate_split_response(
                initiative_prompt, 
                current_state
            )
            
            # Доставляем сообщения
            await self.deliver_messages_with_timing(
                messages, 
                current_state, 
                message_type="initiative"
            )
            
            # Сохраняем в БД как инициативный диалог
            mood_current = current_state.get('dominant_emotion', 'calm')
            self.enhanced_memory.add_conversation(
                "[ИНИЦИАТИВА]", messages, mood_current, mood_current
            )
            
            # Обновляем состояние
            self.psychological_core.update_emotional_state("positive_interaction", 0.5)
            self.last_message_time = datetime.now()
            
            self.logger.info(f"Инициативные сообщения отправлены: {len(messages)} шт.")
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации инициативы: {e}")
    
    async def deliver_messages_with_timing(self, messages: List[str], 
                                         current_state: Dict[str, Any],
                                         message_type: str = "response"):
        """Доставка сообщений с реалистичным печатанием и адаптивной скоростью"""
        
        emotional_state = current_state.get('dominant_emotion', 'calm')
        energy_level = current_state.get('energy_level', 50)
        
        # НОВОЕ: Адаптивная скорость печатания в зависимости от состояния
        mood = current_state.get('current_mood', 'нормальное')
        if 'возбужден' in emotional_state or 'excited' in emotional_state:
            self.typing_simulator.set_speed_mode('fast')
        elif energy_level < 30 or 'tired' in emotional_state:
            self.typing_simulator.set_speed_mode('normal')
        elif 'anxious' in emotional_state or 'sad' in emotional_state:
            self.typing_simulator.set_speed_mode('normal')
        else:
            # Возвращаем к режиму по умолчанию из конфига
            default_mode = self.config.get('typing', {}).get('mode', 'fast')
            self.typing_simulator.set_speed_mode(default_mode)
        
        # Создаем callback'и для системы печатания
        async def send_callback(msg):
            await self.deliver_message(msg, message_type)
        
        async def typing_callback(is_typing):
            # Будет переопределено в интеграциях
            if is_typing:
                self.logger.debug("Показываем 'печатает...'")
            else:
                self.logger.debug("Скрываем 'печатает...'")
        
        # Показываем сводку времени (если включено в логах)
        if self.config.get('logging', {}).get('log_typing_timings', False):
            timing_summary = self.typing_simulator.get_realistic_delays_summary(
                messages, emotional_state, energy_level
            )
            self.logger.info(f"Планируемое время отправки: {timing_summary['total_time']}с, режим: {self.typing_simulator.current_mode}")
        
        # Отправляем с реалистичными паузами
        await self.typing_simulator.send_messages_with_realistic_timing(
            messages=messages,
            emotional_state=emotional_state,
            energy_level=energy_level,
            send_callback=send_callback,
            typing_callback=typing_callback
        )
    
    async def update_physical_state(self):
        """Обновление физиологического состояния"""
        
        current_hour = datetime.now().hour
        
        # Энергия в зависимости от времени
        if 6 <= current_hour <= 8:
            self.psychological_core.physical_state["energy_base"] = 85
        elif 9 <= current_hour <= 12:
            self.psychological_core.physical_state["energy_base"] = 90
        elif 13 <= current_hour <= 17:
            self.psychological_core.physical_state["energy_base"] = 75
        elif 18 <= current_hour <= 21:
            self.psychological_core.physical_state["energy_base"] = 60
        else:
            self.psychological_core.physical_state["energy_base"] = 30
        
        # Стресс накапливается в рабочее время
        if 9 <= current_hour <= 18:
            self.psychological_core.physical_state["stress_level"] = min(8, 
                self.psychological_core.physical_state["stress_level"] + 0.5)
        else:
            self.psychological_core.physical_state["stress_level"] = max(1,
                self.psychological_core.physical_state["stress_level"] - 0.3)
    
    async def generate_life_event(self):
        """Генерация жизненного события"""
        
        current_hour = datetime.now().hour
        
        if 9 <= current_hour <= 18:  # рабочие события
            events = [
                ("получила интересную задачу", "positive", 1.0),
                ("коллега принес кофе", "positive", 0.5),
                ("сложная встреча затянулась", "negative", -1.0),
                ("похвалили за работу", "positive", 2.0)
            ]
        else:  # личные события
            events = [
                ("увидела красивый закат", "positive", 1.0),
                ("подруга написала", "positive", 1.5),
                ("нашла интересную статью", "positive", 0.5),
                ("соседи шумят", "negative", -0.8)
            ]
        
        event_desc, event_type, intensity = random.choice(events)
        
        # Обновляем эмоциональное состояние
        self.psychological_core.update_emotional_state(
            "positive_interaction" if event_type == "positive" else "stress",
            abs(intensity)
        )
        
        # Сохраняем в память
        self.memory_system.add_memory(
            f"Событие: {event_desc}",
            "life_event",
            min(7, int(abs(intensity) * 3)),
            intensity
        )
        
        self.logger.info(f"Жизненное событие: {event_desc}")
    
    async def save_conversation(self, user_message: str, ai_messages: List[str]):
        """Сохранение диалога с множественными ответами"""
        self.conversation_history.append({
            "timestamp": datetime.now(),
            "user": user_message,
            "ai": ai_messages,  # Теперь список сообщений
            "message_count": len(ai_messages)
        })
        
        # Ограничиваем историю
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-50:]
    
    async def extract_memories(self, user_message: str, ai_messages: List[str]):
        """Извлечение воспоминаний о пользователе"""
        
        # Простое извлечение фактов
        facts_found = []
        
        # Ключевые слова для фактов
        if any(word in user_message.lower() for word in ["работаю", "работа", "job"]):
            facts_found.append(("работа пользователя", 6))
        
        if any(word in user_message.lower() for word in ["люблю", "нравится", "обожаю"]):
            facts_found.append((f"предпочтения: {user_message[:100]}", 5))
        
        if any(word in user_message.lower() for word in ["грустно", "плохо", "устал"]):
            facts_found.append(("эмоциональное состояние пользователя", 4))
        
        # Сохраняем найденные факты
        for fact, importance in facts_found:
            self.memory_system.add_memory(
                fact, "user_fact", importance, 0.0
            )
    
    async def daily_memory_consolidation(self):
        """Ежедневная консолидация памяти"""
        self.memory_system._consolidate_memories()
        self.daily_message_count = 0  # сброс счетчика сообщений
        self.logger.info("Консолидация памяти выполнена")
    
    async def deliver_message(self, message: str, message_type: str):
        """Доставка сообщения пользователю - будет переопределена в интеграциях"""
        # Базовая реализация - просто печать
        print(f"\n[{message_type.upper()}]: {message}")
    
    # НОВЫЕ МЕТОДЫ для отладки и мониторинга
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Статистика разговоров с информацией о персонаже"""
        base_stats = {
            "total_conversations": len(self.conversation_history),
            "total_ai_messages": sum(conv.get('message_count', 1) for conv in self.conversation_history),
            "daily_initiatives_sent": self.daily_message_count,
            "last_conversation": self.conversation_history[-1]['timestamp'].strftime('%H:%M:%S') if self.conversation_history else None
        }
        
        if base_stats["total_conversations"] > 0:
            base_stats["avg_messages_per_response"] = round(
                base_stats["total_ai_messages"] / base_stats["total_conversations"], 1
            )
        else:
            base_stats["avg_messages_per_response"] = 0
        
        # НОВОЕ: Добавляем информацию о персонаже
        character_info = self.get_current_character_info()
        base_stats.update({
            "current_character": character_info["name"],
            "character_loaded": character_info["loaded"],
            "relationship_type": character_info.get("relationship_type", "неизвестный"),
            "intimacy_level": character_info.get("intimacy_level", 0)
        })
        
        return base_stats
    
    async def start(self):
        """Запуск компаньона"""
        self.logger.info("Реалистичный AI-компаньон с многосообщенческими ответами запущен")
        
        while True:
            await asyncio.sleep(1)
    
    def stop(self):
        """Остановка компаньона"""
        self.scheduler.shutdown()
        self.logger.info("AI-компаньон остановлен")
