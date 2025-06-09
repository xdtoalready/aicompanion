# Основной модуль AI-компаньона с многосообщенческими ответами

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger 

# Импорт character_loader
from .character_loader import get_character_loader
from .virtual_life import VirtualLifeManager, VirtualActivity

# Импорт систем планирования
from .daily_planning_system import DailyPlanningSystem

# Относительные импорты для модулей внутри core
from .psychology import PsychologicalCore
from .memory import AdvancedMemorySystem
from .ai_client import OptimizedAI
from .typing_simulator import TypingSimulator, TypingIndicator
from .multi_api_manager import create_api_manager, APIUsageType

# Импорт консолидации памяти
from .memory_consolidation import (
    EmotionalMemoryConsolidator,
    enhance_existing_memories_with_emotions,
)

# Импорт системы работы с базой данных
from ..database.memory_manager import EnhancedMemorySystem


class RealisticAICompanion:
    """Реалистичный AI-компаньон с многосообщенческими ответами"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Получаем character_loader через функцию
        self.character_loader = get_character_loader()

        # Инициализация компонентов
        self.psychological_core = PsychologicalCore()

        # База данных для памяти
        db_path = config.get("database", {}).get("path", "data/companion.db")
        self.enhanced_memory = EnhancedMemorySystem(db_path)

        # Оставляем старую систему для совместимости
        self.memory_system = AdvancedMemorySystem()

        # Загружаем персонажа по умолчанию если ещё не загружен
        if not self.character_loader.get_current_character():
            profile_path = config.get("character_profile_path")
            profile_data = config.get("character_profile")

            if profile_path or profile_data:
                loaded = self.character_loader.load_character(
                    profile_data.get("id") if isinstance(profile_data, dict) else None,
                    profile_path=profile_path,
                    profile_data=profile_data,
                )
                if loaded:
                    self.logger.info(
                        f"Загружен персонаж из конфигурации: {loaded.get('name')}"
                    )
            else:
                available_chars = self.character_loader.get_available_characters()
                if available_chars:
                    self.character_loader.load_character(available_chars[0]["id"])
                    self.logger.info(
                        f"Автоматически загружен персонаж: {available_chars[0]['name']}"
                    )

        # AI клиент
        from .multi_api_manager import create_api_manager, APIUsageType
        self.api_manager = create_api_manager(config)

        self.daily_planner = DailyPlanningSystem(
            db_path=db_path,
            api_manager=self.api_manager,
            character_loader=self.character_loader,
            config=config
        )

        self.ai_client = self.api_manager.get_client(APIUsageType.DIALOGUE)

        # Передаём character_loader в AI клиент
        self.optimized_ai = OptimizedAI(self.api_manager, config, self.character_loader)

        # Система печатания
        typing_config = config.get("typing", {})
        self.typing_simulator = TypingSimulator(
            {
                "typing_mode": typing_config.get("mode", "fast"),
                "show_typing_indicator": typing_config.get(
                    "show_typing_indicator", True
                ),
                "natural_pauses": typing_config.get("natural_pauses", True),
            }
        )
        self.typing_indicator = TypingIndicator()

        # Система виртуальной жизни
        self.virtual_life = VirtualLifeManager(
            db_path=config.get("database", {}).get("path", "data/companion.db"),
            character_loader=self.character_loader,
        )

        # Планировщик
        self.scheduler = AsyncIOScheduler()

        # Состояние
        self.last_message_time = None
        self.daily_message_count = 0
        self.conversation_history = []

        self.commands_enabled = True

        self.emotional_memory_consolidator = EmotionalMemoryConsolidator(
            db_path=db_path, api_manager=self.api_manager, config=config
        )

        self.setup_realistic_scheduler()

    def get_current_character_info(self) -> Dict[str, Any]:
        """Получает информацию о текущем персонаже"""
        character = self.character_loader.get_current_character()
        if not character:
            return {"name": "AI", "loaded": False, "error": "Персонаж не загружен"}

        return {
            "name": character.get("name", "Неизвестно"),
            "age": character.get("age", "Неизвестно"),
            "description": character.get("personality", {}).get("description", ""),
            "relationship_type": character.get("current_relationship", {}).get(
                "type", "неопределенный"
            ),
            "intimacy_level": character.get("current_relationship", {}).get(
                "intimacy_level", 0
            ),
            "loaded": True,
            "file_id": character.get("id", "unknown"),
        }

    def setup_realistic_scheduler(self):
        """Настройка реалистичного планировщика"""

        # Проверка желания написать каждые 5 минут
        self.scheduler.add_job(
            self.consciousness_cycle, IntervalTrigger(minutes=5), id="consciousness"
        )

        # Утреннее планирование в 6:00
        self.scheduler.add_job(
            self.morning_planning_cycle,
            CronTrigger(hour=6, minute=0),  # Используем CronTrigger
            id="morning_planning"
        )

        # Остальные задачи...
        self.scheduler.add_job(
            self.run_emotional_memory_consolidation,
            IntervalTrigger(hours=6),
            id="emotional_memory_consolidation",
        )

        self.scheduler.add_job(
            self.deep_emotional_consolidation,
            IntervalTrigger(days=1),
            id="deep_emotional_consolidation",
        )

        self.scheduler.add_job(
            self.analyze_recent_memories_emotions,
            IntervalTrigger(hours=2),
            id="emotion_analysis",
        )

        self.scheduler.add_job(
            self.update_virtual_life,
            IntervalTrigger(minutes=1),
            id="virtual_life_update",
        )

        self.scheduler.start()

    async def morning_planning_cycle(self):
        """Утренний цикл планирования в 6:00"""
        try:
            self.logger.info("🌅 Утренний цикл планирования запущен")
            
            # Генерируем план дня
            success = await self.daily_planner.generate_daily_plan()
            
            if success:
                self.logger.info("✅ План дня сгенерирован успешно")
                
                # Обновляем психологическое состояние - планирование поднимает настроение
                self.psychological_core.update_emotional_state("accomplishment", 1.0)
                
                # Можем отправить уведомление пользователю о планах (опционально)
                if hasattr(self, 'allowed_users') and self.config.get('behavior', {}).get('notify_about_plans', False):
                    await self._notify_users_about_daily_plan()
            else:
                self.logger.warning("⚠️ Не удалось сгенерировать план дня")
                
        except Exception as e:
            self.logger.error(f"Ошибка утреннего планирования: {e}")

    async def _notify_users_about_daily_plan(self):
        """Уведомляет пользователей о планах на день"""
        try:
            # Получаем сегодняшние планы
            today_plans = await self._get_today_ai_plans()
            
            if not today_plans:
                return
            
            # Формируем сообщение о планах
            plan_messages = await self._generate_plan_announcement(today_plans)
            
            # Отправляем пользователям (будет переопределено в telegram_bot.py)
            await self.deliver_messages_with_timing(
                plan_messages, 
                await self.optimized_ai.get_simple_mood_calculation(self.psychological_core),
                message_type="plan_announcement"
            )
                    
        except Exception as e:
            self.logger.error(f"Ошибка уведомления о планах: {e}")

    async def _get_today_ai_plans(self) -> List[Dict]:
        """Получает планы ИИ на сегодня"""
        try:
            import sqlite3
            from datetime import date
            
            today = date.today().isoformat()
            
            with sqlite3.connect(self.enhanced_memory.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT activity_type, description, start_time, importance, flexibility
                    FROM virtual_activities
                    WHERE planning_date = ? AND generated_by_ai = 1
                    ORDER BY start_time ASC
                """, (today,))
                
                plans = []
                for row in cursor.fetchall():
                    plans.append({
                        'type': row[0],
                        'description': row[1], 
                        'start_time': row[2],
                        'importance': row[3],
                        'flexibility': row[4]
                    })
                
                return plans
                
        except Exception as e:
            self.logger.error(f"Ошибка получения планов: {e}")
            return []
        
    async def _generate_plan_announcement(self, plans: List[Dict]) -> List[str]:
        """Генерирует сообщения о планах"""
        
        if not plans:
            return ["Сегодня у меня свободный день! 😊"]
        
        character = self.character_loader.get_current_character()
        character_name = character.get('name', 'AI') if character else 'AI'
        
        messages = [
            f"Доброе утро! ☀️ Я уже спланировала день!"
        ]
        
        # Добавляем основные планы
        important_plans = [p for p in plans if p['importance'] >= 7]
        casual_plans = [p for p in plans if p['importance'] < 7]
        
        if important_plans:
            important_desc = []
            for plan in important_plans[:2]:  # Максимум 2 важных
                time_str = plan['start_time'].split(' ')[1][:5]  # HH:MM
                important_desc.append(f"{time_str} - {plan['description']}")
            
            messages.append(f"Главные дела:\n" + "\n".join(important_desc))
        
        if casual_plans:
            messages.append(f"А ещё планирую {casual_plans[0]['description'].lower()} и ещё кое-что! ✨")
        
        # Персонаж-специфичный комментарий
        if character and 'марин' in character_name.lower():
            messages.append("Может присоединишься к каким-то планам? Было бы весело! 💕")
        else:
            messages.append("Расскажи как дела у тебя! Может что-то планируешь? 😊")
        
        return messages
    
    async def force_generate_daily_plan(self) -> bool:
        """Принудительно генерирует план дня (для тестирования)"""
        try:
            return await self.daily_planner.generate_daily_plan()
        except Exception as e:
            self.logger.error(f"Ошибка принудительного планирования: {e}")
            return False
    
    def get_planning_stats(self) -> Dict[str, Any]:
        """Получает статистику планирования"""
        try:
            import sqlite3
            from datetime import date, timedelta
            
            db_path = self.enhanced_memory.db_manager.db_path
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Общая статистика планирования
                cursor.execute("SELECT COUNT(*) FROM planning_sessions")
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM virtual_activities WHERE generated_by_ai = 1")
                total_ai_activities = cursor.fetchone()[0]
                
                # Статистика за последнюю неделю
                week_ago = (date.today() - timedelta(days=7)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM planning_sessions 
                    WHERE planning_date >= ?
                """, (week_ago,))
                weekly_sessions = cursor.fetchone()[0]
                
                # Успешность планирования
                cursor.execute("""
                    SELECT COUNT(*) FROM planning_sessions 
                    WHERE success = 1 AND planning_date >= ?
                """, (week_ago,))
                successful_sessions = cursor.fetchone()[0]
                
                # Планы на сегодня
                today = date.today().isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM virtual_activities
                    WHERE planning_date = ? AND generated_by_ai = 1
                """, (today,))
                today_plans = cursor.fetchone()[0]
                
                return {
                    "total_sessions": total_sessions,
                    "total_ai_activities": total_ai_activities,
                    "weekly_sessions": weekly_sessions,
                    "successful_sessions": successful_sessions,
                    "today_plans": today_plans,
                    "success_rate": (successful_sessions / weekly_sessions * 100) if weekly_sessions > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики планирования: {e}")
            return {
                "total_sessions": 0,
                "total_ai_activities": 0,
                "weekly_sessions": 0,
                "successful_sessions": 0,
                "today_plans": 0,
                "success_rate": 0,
                "error": str(e)
            }

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
                self.enhanced_memory.db_manager.db_path, self.ai_client, self.config
            )

        except Exception as e:
            self.logger.error(f"Ошибка глубокой эмоциональной консолидации: {e}")

    async def analyze_recent_memories_emotions(self):
        """Анализирует эмоции недавних воспоминаний"""
        try:
            # Улучшаем воспоминания без эмоциональных меток
            await enhance_existing_memories_with_emotions(
                self.enhanced_memory.db_manager.db_path, self.ai_client, self.config
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
                cursor.execute(
                    """
                    SELECT emotion_type, COUNT(*), AVG(emotional_intensity), AVG(importance)
                    FROM memories 
                    WHERE created_at >= ? AND emotion_type IS NOT NULL
                    GROUP BY emotion_type
                    ORDER BY COUNT(*) DESC
                """,
                    (month_ago,),
                )

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
                    model=self.config.get("ai", {}).get("model"),
                    messages=[
                        {"role": "system", "content": analysis_prompt},
                        {"role": "user", "content": pattern_text},
                    ],
                    max_tokens=400,
                    temperature=0.3,
                )

                analysis = response.choices[0].message.content.strip()

                # Сохраняем анализ как специальное воспоминание
                cursor.execute(
                    """
                    INSERT INTO memories 
                    (character_id, memory_type, content, importance, 
                     emotional_intensity, emotion_type, is_consolidated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        1,
                        "emotional_analysis",
                        f"Эмоциональный анализ пользователя: {analysis}",
                        9,  # Высокая важность
                        7.0,  # Средне-высокая интенсивность
                        "analytical",
                        True,
                    ),
                )

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
                model=self.config.get("ai", {}).get("model"),
                messages=[
                    {"role": "system", "content": analysis_prompt},
                    {
                        "role": "user",
                        "content": f"Воспоминания:\n{consolidated_memories}",
                    },
                ],
                max_tokens=300,
                temperature=0.3,
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

                cursor.execute(
                    """
                    SELECT content FROM memories 
                    WHERE is_consolidated = 1 
                    AND consolidation_level IN ('medium_term', 'long_term')
                    ORDER BY importance DESC, last_consolidated DESC
                    LIMIT 20
                """
                )

                memories = [row[0] for row in cursor.fetchall()]
                return "\n".join(memories)

        except Exception as e:
            self.logger.error(f"Ошибка получения консолидированных воспоминаний: {e}")
            return ""

    def _save_memory_analysis(self, analysis: str):
        """Сохраняет результат анализа памяти"""
        try:
            self.enhanced_memory.add_conversation(
                "[АНАЛИЗ_ПАМЯТИ]", [analysis], "analytical", "insightful"
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
            max_daily = self.config.get("behavior", {}).get("max_daily_initiatives", 8)
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
                await self.send_initiative_messages(
                    current_state
                )  # ИЗМЕНЕНО: теперь множественные
                self.daily_message_count += 1

            # Иногда генерируем жизненные события
            if random.random() < 0.15:  # 15% шанс
                await self.generate_life_event()

        except Exception as e:
            self.logger.error(f"Ошибка в цикле сознания: {e}")

    async def _should_initiate_realistically(self, current_state: Dict) -> bool:
        """Улучшенное решение об инициативе с подробным логированием"""

        initiative_desire = current_state.get("initiative_desire", 0)
        current_hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5  # 5=суббота, 6=воскресенье
        activity_context = current_state.get("activity_context")

        self.logger.debug(f"🤔 Проверка инициативы: desire={initiative_desire}, hour={current_hour}, weekend={is_weekend}")

        # 1. Ночное время - спим
        if current_hour >= 23 or current_hour < 7:
            self.logger.debug("😴 Ночное время - не пишем")
            return False

        # 2. Базовый порог желания (понижен!)
        if initiative_desire < 2:  # Было 3, стало 2
            self.logger.debug(f"😐 Слабое желание писать: {initiative_desire} < 2")
            return False

        # 3. Проверяем время последнего сообщения (ослаблено!)
        min_hours = self.config.get("behavior", {}).get("min_hours_between_initiatives", 2)

        # В выходные и вечером - можем писать чаще
        if is_weekend or current_hour >= 18:
            min_hours = min_hours * 0.7  # Уменьшаем интервал на 30%

        if self.last_message_time:
            hours_since = (datetime.now() - self.last_message_time).total_seconds() / 3600
            if hours_since < min_hours:
                self.logger.debug(f"⏰ Слишком рано: прошло {hours_since:.1f}ч < {min_hours:.1f}ч")
                return False

        # 4. Бонусы к желанию
        bonus_reasons = []

        # Часы пик активности
        peak_hours = [9, 12, 16, 19, 22]
        if current_hour in peak_hours:
            initiative_desire += 1
            bonus_reasons.append(f"час пик ({current_hour})")

        # Выходные - более активное общение
        if is_weekend:
            initiative_desire += 1.5
            bonus_reasons.append("выходные")

        # Вечернее время - больше желания общаться  
        if activity_context == "evening_time":
            initiative_desire += 1
            bonus_reasons.append("вечер")

        # Учитываем персонажа (исправлен баг!)
        character = self.character_loader.get_current_character()  # Исправлено: добавлен self.
        if character:
            name = character.get("name", "").lower()
            if "марин" in name or "китагава" in name:
                initiative_desire += 1
                bonus_reasons.append("активный персонаж")
            
            # Экстравертные персонажи пишут чаще
            extraversion = character.get("personality", {}).get("key_traits", [])
            if any("экстравертн" in trait.lower() for trait in extraversion):
                initiative_desire += 0.5
                bonus_reasons.append("экстраверт")

        if bonus_reasons:
            self.logger.debug(f"✨ Бонусы: {', '.join(bonus_reasons)} -> desire={initiative_desire}")

        # 5. Рабочее время (ослаблено!)
        work_penalty = 0
        if activity_context == "work_time" and not is_weekend:
            # Теперь только 50% блокировка вместо 80%
            if random.random() < 0.5:  # Было 0.8, стало 0.5
                self.logger.debug("💼 Рабочее время - блокируем (50% шанс)")
                return False
            work_penalty = 0.5
            self.logger.debug("💼 Рабочее время, но прошли проверку")

        # 6. Финальная проверка (исправлена формула!)
        adjusted_desire = initiative_desire - work_penalty

        # Новая формула: чем больше желание, тем больше шанс
        chance = min(0.8, adjusted_desire / 10)  # Максимум 80% шанс
        random_roll = random.random()

        should_send = random_roll < chance

        self.logger.debug(
            f"🎲 Финальная проверка: desire={adjusted_desire:.1f} -> chance={chance:.2f} "
            f"vs roll={random_roll:.2f} -> {'✅ ОТПРАВЛЯЕМ' if should_send else '❌ не отправляем'}"
        )

        # 7. Дополнительная статистика для отладки
        if should_send:
            self.logger.info(f"🚀 Решение отправить инициативу! Желание: {adjusted_desire:.1f}, бонусы: {bonus_reasons}")

        return should_send

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

        if hasattr(self, "allowed_users") and self.allowed_users:
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

        if hasattr(self, "allowed_users") and self.allowed_users:
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

        name = character.get("name", "").lower()

        # Базовое расписание для всех персонажей
        base_schedule = [
            ("work", "работаю/учусь", 9, 5, 1.0, 40),  # 9 утра, 5 часов
            ("rest", "отдыхаю дома", 14, 1, 0.5, 10),  # 14:00, 1 час
            ("hobby", "занимаюсь хобби", 16, 2, 2.0, 30),  # 16:00, 2 часа
            ("social", "общаюсь с друзьями", 19, 1.5, 1.5, 20),  # 19:00, 1.5 часа
        ]

        # Специальное расписание для Марин
        if "марин" in name or "китагава" in name:
            cosplay_schedule = [
                ("cosplay", "работаю над новым костюмом", 15, 3, 2.5, 35),
                ("cosplay", "фотосессия в готовом костюме", 11, 2, 3.0, 25),
                ("social", "иду на аниме-конвент", 10, 6, 3.0, 50),
                ("hobby", "смотрю новое аниме", 20, 2, 2.0, 15),
            ]
            base_schedule.extend(cosplay_schedule)

        # Планируем на следующие 3 дня
        for day_offset in range(1, 4):
            target_date = datetime.now() + timedelta(days=day_offset)

            # Выбираем случайные активности для этого дня
            daily_activities = random.sample(base_schedule, k=random.randint(2, 4))

            for (
                activity_type,
                description,
                start_hour,
                duration,
                mood_effect,
                energy_cost,
            ) in daily_activities:
                start_time = target_date.replace(
                    hour=start_hour, minute=0, second=0, microsecond=0
                )

                # Добавляем случайность ±30 минут
                start_time += timedelta(minutes=random.randint(-30, 30))

                self.virtual_life.schedule_activity(
                    activity_type=activity_type,
                    description=description,
                    start_time=start_time,
                    duration_hours=duration,
                    mood_effect=mood_effect,
                    energy_cost=energy_cost,
                )

        self.logger.info("📅 Автоматическое расписание создано на 3 дня")

    async def send_initiative_messages(self, current_state: Dict):
        """Отправка инициативных сообщений с БД контекстом"""

        # НОВОЕ: Получаем контекст из базы данных
        db_context = self.enhanced_memory.get_context_for_response(
            "инициативное общение"
        )
        current_state["memory_context"] = db_context

        try:
            # Генерируем множественные сообщения
            messages = await self.optimized_ai.generate_split_response(
                "Хочу написать пользователю что-то интересное", current_state
            )

            # Доставляем сообщения
            await self.deliver_messages_with_timing(
                messages, current_state, message_type="initiative"
            )

            # Сохраняем в БД как инициативный диалог
            mood_current = current_state.get("dominant_emotion", "calm")
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
                "recent_conversations": summary["recent_conversations"],
                "total_memories": summary["total_memories"],
                "last_conversation": summary["last_conversation"],
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики БД: {e}")
            return {"database_enabled": False, "error": str(e)}

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
            current_state["memory_context"] = db_context

            # Добавляем контекст персонажа
            character_context = self.character_loader.get_character_context_for_ai()
            current_state["character_context"] = character_context

            self.logger.info(f"Контекст персонажа: {character_context[:100]}...")

            # Генерируем ответ с полным контекстом
            ai_messages = await self.optimized_ai.generate_split_response(
                message, current_state
            )

            # Получаем настроение ПОСЛЕ обработки
            mood_after = self.psychological_core.emotional_momentum["current_emotion"]

            # Сохраняем диалог в базу данных
            conversation_id = self.enhanced_memory.add_conversation(
                message, ai_messages, mood_before, mood_after
            )

            # Обновляем прогресс отношений с персонажем
            character = self.character_loader.get_current_character()
            if character:
                # Увеличиваем близость при позитивном общении
                current_intimacy = character.get("current_relationship", {}).get(
                    "intimacy_level", 1
                )
                if (
                    mood_after in ["happy", "excited", "content"]
                    and random.random() < 0.1
                ):  # 10% шанс
                    new_intimacy = min(10, current_intimacy + 0.1)
                    self.character_loader.update_relationship_progress(
                        {
                            "intimacy_level": new_intimacy,
                            "last_positive_interaction": datetime.now().isoformat(),
                        }
                    )
                    self.logger.info(f"Близость увеличена до {new_intimacy:.1f}")

            self.logger.info(f"Диалог сохранен в БД с ID: {conversation_id}")

            # Сохраняем также в локальную историю для совместимости
            await self.save_conversation(message, ai_messages)

            self.last_message_time = datetime.now()
            return ai_messages

        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            # Fallback с учётом персонажа
            character = self.character_loader.get_current_character()
            if character and "марин" in character.get("name", "").lower():
                return [
                    "Ой! 😅 Что-то пошло не так...",
                    "Попробуй написать ещё раз! ✨",
                ]
            else:
                return ["Извини, что-то пошло не так... 😅 Попробуй еще раз!"]

    # МЕТОД ДЛЯ ИНИЦИАТИВНЫХ СООБЩЕНИЙ С УЧЁТОМ ПЕРСОНАЖА:
    async def send_initiative_messages(self, current_state: Dict):
        """Отправка инициативных сообщений с учётом персонажа"""

        # Получаем контекст из базы данных
        db_context = self.enhanced_memory.get_context_for_response(
            "инициативное общение"
        )
        current_state["memory_context"] = db_context

        # НОВОЕ: Добавляем контекст персонажа
        character_context = character_loader.get_character_context_for_ai()
        current_state["character_context"] = character_context

        # Получаем текущего персонажа для специальных тем
        character = character_loader.get_current_character()
        initiative_prompt = "Хочу написать пользователю что-то интересное"

        if character:
            # Специальные темы для инициатив в зависимости от персонажа
            initiative_topics = character.get("behavior", {}).get(
                "initiative_topics", []
            )
            if initiative_topics:
                topic = random.choice(initiative_topics)
                initiative_prompt = f"Хочу {topic}"

            # Для Марин - особые инициативы
            if "марин" in character.get("name", "").lower():
                special_topics = [
                    "рассказать о новом косплее который планирую",
                    "поделиться впечатлениями от аниме которое смотрела",
                    "предложить вместе поработать над костюмом",
                    "рассказать о смешном случае на конвенции",
                    "спросить мнение о новом наряде",
                ]
                initiative_prompt = f"Хочу {random.choice(special_topics)}"

        try:
            # Генерируем множественные сообщения
            messages = await self.optimized_ai.generate_split_response(
                initiative_prompt, current_state
            )

            # Доставляем сообщения
            await self.deliver_messages_with_timing(
                messages, current_state, message_type="initiative"
            )

            # Сохраняем в БД как инициативный диалог
            mood_current = current_state.get("dominant_emotion", "calm")
            self.enhanced_memory.add_conversation(
                "[ИНИЦИАТИВА]", messages, mood_current, mood_current
            )

            # Обновляем состояние
            self.psychological_core.update_emotional_state("positive_interaction", 0.5)
            self.last_message_time = datetime.now()

            self.logger.info(f"Инициативные сообщения отправлены: {len(messages)} шт.")

        except Exception as e:
            self.logger.error(f"Ошибка генерации инициативы: {e}")

    async def deliver_messages_with_timing(
        self,
        messages: List[str],
        current_state: Dict[str, Any],
        message_type: str = "response",
    ):
        """Доставка сообщений с реалистичным печатанием и адаптивной скоростью"""

        emotional_state = current_state.get("dominant_emotion", "calm")
        energy_level = current_state.get("energy_level", 50)

        # НОВОЕ: Адаптивная скорость печатания в зависимости от состояния
        mood = current_state.get("current_mood", "нормальное")
        if "возбужден" in emotional_state or "excited" in emotional_state:
            self.typing_simulator.set_speed_mode("fast")
        elif energy_level < 30 or "tired" in emotional_state:
            self.typing_simulator.set_speed_mode("normal")
        elif "anxious" in emotional_state or "sad" in emotional_state:
            self.typing_simulator.set_speed_mode("normal")
        else:
            # Возвращаем к режиму по умолчанию из конфига
            default_mode = self.config.get("typing", {}).get("mode", "fast")
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
        if self.config.get("logging", {}).get("log_typing_timings", False):
            timing_summary = self.typing_simulator.get_realistic_delays_summary(
                messages, emotional_state, energy_level
            )
            self.logger.info(
                f"Планируемое время отправки: {timing_summary['total_time']}с, режим: {self.typing_simulator.current_mode}"
            )

        # Отправляем с реалистичными паузами
        await self.typing_simulator.send_messages_with_realistic_timing(
            messages=messages,
            emotional_state=emotional_state,
            energy_level=energy_level,
            send_callback=send_callback,
            typing_callback=typing_callback,
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
            self.psychological_core.physical_state["stress_level"] = min(
                8, self.psychological_core.physical_state["stress_level"] + 0.5
            )
        else:
            self.psychological_core.physical_state["stress_level"] = max(
                1, self.psychological_core.physical_state["stress_level"] - 0.3
            )

    async def generate_life_event(self):
        """Генерация жизненного события"""

        current_hour = datetime.now().hour

        if 9 <= current_hour <= 18:  # рабочие события
            events = [
                ("получила интересную задачу", "positive", 1.0),
                ("коллега принес кофе", "positive", 0.5),
                ("сложная встреча затянулась", "negative", -1.0),
                ("похвалили за работу", "positive", 2.0),
            ]
        else:  # личные события
            events = [
                ("увидела красивый закат", "positive", 1.0),
                ("подруга написала", "positive", 1.5),
                ("нашла интересную статью", "positive", 0.5),
                ("соседи шумят", "negative", -0.8),
            ]

        event_desc, event_type, intensity = random.choice(events)

        # Обновляем эмоциональное состояние
        self.psychological_core.update_emotional_state(
            "positive_interaction" if event_type == "positive" else "stress",
            abs(intensity),
        )

        # Сохраняем в память
        self.memory_system.add_memory(
            f"Событие: {event_desc}",
            "life_event",
            min(7, int(abs(intensity) * 3)),
            intensity,
        )

        self.logger.info(f"Жизненное событие: {event_desc}")

    async def save_conversation(self, user_message: str, ai_messages: List[str]):
        """Сохранение диалога с множественными ответами"""
        self.conversation_history.append(
            {
                "timestamp": datetime.now(),
                "user": user_message,
                "ai": ai_messages,  # Теперь список сообщений
                "message_count": len(ai_messages),
            }
        )

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

        if any(
            word in user_message.lower() for word in ["люблю", "нравится", "обожаю"]
        ):
            facts_found.append((f"предпочтения: {user_message[:100]}", 5))

        if any(word in user_message.lower() for word in ["грустно", "плохо", "устал"]):
            facts_found.append(("эмоциональное состояние пользователя", 4))

        # Сохраняем найденные факты
        for fact, importance in facts_found:
            self.memory_system.add_memory(fact, "user_fact", importance, 0.0)

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
            "total_ai_messages": sum(
                conv.get("message_count", 1) for conv in self.conversation_history
            ),
            "daily_initiatives_sent": self.daily_message_count,
            "last_conversation": (
                self.conversation_history[-1]["timestamp"].strftime("%H:%M:%S")
                if self.conversation_history
                else None
            ),
        }

        if base_stats["total_conversations"] > 0:
            base_stats["avg_messages_per_response"] = round(
                base_stats["total_ai_messages"] / base_stats["total_conversations"], 1
            )
        else:
            base_stats["avg_messages_per_response"] = 0

        # НОВОЕ: Добавляем информацию о персонаже
        character_info = self.get_current_character_info()
        base_stats.update(
            {
                "current_character": character_info["name"],
                "character_loaded": character_info["loaded"],
                "relationship_type": character_info.get(
                    "relationship_type", "неизвестный"
                ),
                "intimacy_level": character_info.get("intimacy_level", 0),
            }
        )

        return base_stats

    async def start(self):
        """Запуск компаньона"""
        self.logger.info(
            "Реалистичный AI-компаньон с многосообщенческими ответами запущен"
        )

        # Создаем расписание виртуальной жизни один раз при запуске
        await self.create_automatic_schedule()

        while True:
            await asyncio.sleep(1)

    def stop(self):
        """Остановка компаньона"""
        self.scheduler.shutdown()
        self.logger.info("AI-компаньон остановлен")


    async def api_stats_command(self, update: Any, context: Any):
        """Статистика использования API ключей"""
        if not self.commands_enabled:
            return
        
        stats = self.api_manager.get_usage_stats()
        
        text = f"📊 **СТАТИСТИКА API КЛЮЧЕЙ**\n\n"
        text += f"🔢 **Общая статистика:**\n"
        text += f"• Всего запросов: {stats['total_requests']}\n"
        text += f"• Всего токенов: {stats['total_tokens']:,}\n"
        text += f"• Ошибок: {stats['total_errors']}\n\n"
        
        for usage_type, type_stats in stats['by_type'].items():
            emoji = {"dialogue": "💬", "planning": "📅", "analytics": "📊"}.get(usage_type, "🔧")
            
            text += f"{emoji} **{usage_type.upper()}:**\n"
            text += f"• Ключей в пуле: {type_stats['keys_available']}\n"
            text += f"• Запросов: {type_stats['requests']}\n"
            text += f"• Токенов: {type_stats['tokens']:,}\n"
            text += f"• Ошибок: {type_stats['errors']}\n\n"
        
        # Добавляем предупреждения о лимитах
        limits = self.config.get("ai", {}).get("limits", {})
        if limits:
            text += "⚠️ **Лимиты (если настроены):**\n"
            for usage_type, type_stats in stats['by_type'].items():
                if usage_type in limits:
                    limit_info = limits[usage_type]
                    tokens_limit = limit_info.get("max_tokens_per_day", 0)
                    if tokens_limit > 0:
                        usage_pct = (type_stats['tokens'] / tokens_limit) * 100
                        text += f"• {usage_type}: {usage_pct:.1f}% дневного лимита\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')

