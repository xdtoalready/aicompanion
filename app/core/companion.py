# Основной модуль AI-компаньона с многосообщенческими ответами

import asyncio
import json
import logging
import random
import re
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
from ..database.memory_manager_optimized import OptimizedMemoryManager

class AISelfPlanningParser:
    """Парсер команд самопланирования AI"""
    
    def __init__(self, virtual_life_manager, logger):
        self.virtual_life = virtual_life_manager
        self.logger = logger
        
        # Паттерны для разных типов планирования
        self.planning_patterns = {
            # {{plan: 17:00 - написать любимому}}
            'simple': r'\{\{plan:\s*(\d{1,2}):(\d{2})\s*-\s*([^}]+)\}\}',
            
            # {{plan_add: 17:00, "написать любимому", high, personal}}
            'detailed': r'\{\{plan_add:\s*(\d{1,2}):(\d{2}),\s*"([^"]+)",\s*(\w+),\s*(\w+)\}\}',
            
            # {{remind: 17:00 - написать сообщение}}
            'reminder': r'\{\{remind:\s*(\d{1,2}):(\d{2})\s*-\s*([^}]+)\}\}',
            
            # {{plan_now: занимаюсь косплеем до 16:00}}
            'current': r'\{\{plan_now:\s*([^}]+)\}\}'
        }
    
    def parse_and_execute_plans(self, ai_response_text: str) -> str:
        """Парсит команды планирования и выполняет их, возвращает очищенный текст"""
        
        original_text = ai_response_text
        executed_plans = []
        
        self.logger.info(f"🔍 Анализирую ответ на команды планирования: {ai_response_text[:100]}...")
        
        # Обрабатываем каждый тип команд
        for plan_type, pattern in self.planning_patterns.items():
            matches = re.findall(pattern, ai_response_text)
            
            if matches:
                self.logger.info(f"🎯 Найдены команды типа '{plan_type}': {matches}")
            
            for match in matches:
                try:
                    success = self._execute_plan_command(plan_type, match)
                    if success:
                        executed_plans.append(f"{plan_type}: {match}")
                        self.logger.info(f"✅ Выполнена команда планирования: {plan_type} - {match}")
                    else:
                        self.logger.warning(f"⚠️ Не удалось выполнить команду: {plan_type} - {match}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Ошибка выполнения команды планирования: {e}")
            
            # Убираем команды из текста
            ai_response_text = re.sub(pattern, '', ai_response_text)
        
        # Очищаем лишние пробелы и разделители
        ai_response_text = re.sub(r'\|\|\s*\|\|', '||', ai_response_text)  # Двойные разделители
        ai_response_text = re.sub(r'^\|\|', '', ai_response_text)  # В начале
        ai_response_text = re.sub(r'\|\|$', '', ai_response_text)  # В конце
        
        if executed_plans:
            self.logger.info(f"🤖📅 AI добавил {len(executed_plans)} планов: {executed_plans}")
        else:
            self.logger.info("📅 Команд планирования в ответе не найдено")
        
        cleaned = ai_response_text.strip()
        self.logger.info(f"✂️ Очищенный ответ: {cleaned[:100]}...")
        
        return cleaned
    
    def _execute_plan_command(self, plan_type: str, match_data) -> bool:
        """Выполняет конкретную команду планирования"""
        
        try:
            if plan_type == 'simple':
                hour, minute, description = match_data
                return self._add_simple_plan(int(hour), int(minute), description.strip())
                
            elif plan_type == 'detailed':
                hour, minute, description, priority, activity_type = match_data
                return self._add_detailed_plan(
                    int(hour), int(minute), 
                    description.strip(), 
                    priority.strip(), 
                    activity_type.strip()
                )
                
            elif plan_type == 'reminder':
                hour, minute, description = match_data
                return self._add_reminder(int(hour), int(minute), description.strip())
                
            elif plan_type == 'current':
                description = match_data[0] if isinstance(match_data, tuple) else match_data
                return self._update_current_activity(description.strip())
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды {plan_type}: {e}")
            return False
    
    def _add_simple_plan(self, hour: int, minute: int, description: str) -> bool:
        """Добавляет простой план на сегодня"""
        
        try:
            # Создаём время на сегодня
            today = datetime.now().date()
            plan_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            # Если время уже прошло, планируем на завтра
            if plan_time <= datetime.now():
                plan_time += timedelta(days=1)
                self.logger.info(f"📅 Время {hour:02d}:{minute:02d} уже прошло, планирую на завтра")
            
            # Определяем тип активности по описанию
            activity_type = self._guess_activity_type(description)
            
            # Определяем важность
            importance = self._guess_importance(description)
            
            # Добавляем план
            success = self.virtual_life.schedule_activity(
                activity_type=activity_type,
                description=f"🤖 {description}",  # Помечаем как AI-план
                start_time=plan_time,
                duration_hours=0.5,  # По умолчанию 30 минут
                mood_effect=1.0,  # Выполнение обещаний улучшает настроение
                energy_cost=10
            )
            
            if success:
                self.logger.info(f"📝 ✅ Добавлен AI-план: {plan_time.strftime('%d.%m %H:%M')} - {description}")
            else:
                self.logger.error(f"📝 ❌ Не удалось добавить AI-план: {plan_time.strftime('%d.%m %H:%M')} - {description}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления простого плана: {e}")
            return False
    
    def _add_detailed_plan(self, hour: int, minute: int, description: str, priority: str, activity_type: str) -> bool:
        """Добавляет детальный план"""
        
        try:
            today = datetime.now().date()
            plan_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            if plan_time <= datetime.now():
                plan_time += timedelta(days=1)
            
            # Конвертируем приоритет в важность
            priority_map = {
                'low': 3, 'medium': 5, 'high': 8, 'critical': 10,
                'низкий': 3, 'средний': 5, 'высокий': 8, 'критический': 10
            }
            importance = priority_map.get(priority.lower(), 5)
            
            # Конвертируем тип активности
            activity_type_map = {
                'personal': 'personal', 'work': 'work', 'social': 'social',
                'hobby': 'hobby', 'rest': 'rest', 'cosplay': 'cosplay',
                'личное': 'personal', 'работа': 'work', 'общение': 'social',
                'хобби': 'hobby', 'отдых': 'rest', 'косплей': 'cosplay'
            }
            mapped_type = activity_type_map.get(activity_type.lower(), 'personal')
            
            success = self.virtual_life.schedule_activity(
                activity_type=mapped_type,
                description=f"🤖 {description}",
                start_time=plan_time,
                duration_hours=0.5,
                mood_effect=1.5 if importance >= 8 else 1.0,
                energy_cost=15 if importance >= 8 else 10
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления детального плана: {e}")
            return False
    
    def _add_reminder(self, hour: int, minute: int, description: str) -> bool:
        """Добавляет напоминание (короткий план на 5 минут)"""
        
        try:
            today = datetime.now().date()
            plan_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
            
            if plan_time <= datetime.now():
                plan_time += timedelta(days=1)
            
            success = self.virtual_life.schedule_activity(
                activity_type='reminder',
                description=f"🔔 {description}",
                start_time=plan_time,
                duration_hours=0.083,  # 5 минут
                mood_effect=0.5,
                energy_cost=5
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления напоминания: {e}")
            return False
    
    def _update_current_activity(self, description: str) -> bool:
        """Обновляет текущую активность"""
        # Пока просто логируем, можно расширить
        self.logger.info(f"🔄 AI обновил текущую активность: {description}")
        return True
    
    def _guess_activity_type(self, description: str) -> str:
        """Угадывает тип активности по описанию"""
        
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['косплей', 'костюм', 'шить', 'аниме']):
            return 'cosplay'
        elif any(word in desc_lower for word in ['написать', 'сообщение', 'позвонить', 'встретиться']):
            return 'social'
        elif any(word in desc_lower for word in ['работа', 'дело', 'задача', 'проект']):
            return 'work'
        elif any(word in desc_lower for word in ['отдых', 'отдохнуть', 'расслабиться']):
            return 'rest'
        else:
            return 'personal'
    
    def _guess_importance(self, description: str) -> int:
        """Угадывает важность по описанию"""
        
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ['обязательно', 'обещаю', 'важно', 'срочно']):
            return 8
        elif any(word in desc_lower for word in ['хочу', 'планирую', 'собираюсь']):
            return 6
        elif any(word in desc_lower for word in ['может', 'если', 'попробую']):
            return 4
        else:
            return 5

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

        # Трекинг отправленных уведомлений
        self.notified_activities = set()

        # База данных для памяти
        db_path = config.get("database", {}).get("path", "data/companion.db")
        self.enhanced_memory = OptimizedMemoryManager(db_path)

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

        # Система виртуальной жизни СНАЧАЛА
        self.virtual_life = VirtualLifeManager(
            db_path=config.get("database", {}).get("path", "data/companion.db"),
            character_loader=self.character_loader,
            api_manager=self.api_manager,
            config=config
        )

        # Теперь передаем VirtualLifeManager ПОСЛЕ его создания
        self.optimized_ai.virtual_life_manager = self.virtual_life

        # Планировщик
        self.scheduler = AsyncIOScheduler()

        # Состояние
        self.last_message_time = None
        self.daily_message_count = 0
        self.conversation_history = []

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
            CronTrigger(hour=6, minute=0),
            id="morning_planning"
        )

        # Проверка планов при запуске
        self.scheduler.add_job(
            self.check_and_generate_plans_on_startup,
            'date',
            run_date=datetime.now() + timedelta(seconds=10),
            id="startup_planning_check"
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

        # Очистка уведомлений в полночь
        self.scheduler.add_job(
            self.clean_activity_notifications,
            CronTrigger(hour=0, minute=0),
            id="clean_notifications"
        )

        self.scheduler.start()

    async def check_and_generate_plans_on_startup(self):
        """Проверяет есть ли планы на сегодня при запуске"""
        try:
            self.logger.info("🔍 Проверка планов при запуске системы...")
            
            # Проверяем есть ли планы на сегодня
            today_plans = await self._get_today_ai_plans()
            
            if not today_plans:
                self.logger.info("📅 Планов на сегодня нет - запускаю экстренное планирование!")
                
                # Генерируем план немедленно
                success = await self.daily_planner.generate_daily_plan()
                
                if success:
                    self.logger.info("✅ Экстренное планирование выполнено успешно!")
                    
                    # Уведомляем пользователей (опционально)
                    if hasattr(self, 'allowed_users') and self.config.get('notify_about_emergency_planning', False):
                        emergency_messages = [
                            "Ой! Я проспала утреннее планирование! 😅",
                            "Но сейчас быстро составила план на день! ✨", 
                            "Теперь всё готово для продуктивного дня! 💪"
                        ]
                        
                        current_state = await self.optimized_ai.get_simple_mood_calculation(self.psychological_core)
                        
                        await self.deliver_messages_with_timing(
                            emergency_messages,
                            current_state,
                            message_type="emergency_planning"
                        )
                else:
                    self.logger.warning("⚠️ Экстренное планирование не удалось")
            else:
                self.logger.info(f"✅ Планы на сегодня уже есть: {len(today_plans)} активностей")
                
                # Показываем первые несколько планов для контроля
                for i, plan in enumerate(today_plans[:3]):
                    time_str = plan.get('start_time', '').split(' ')[1][:5] if ' ' in plan.get('start_time', '') else plan.get('start_time', '')[:5]
                    self.logger.info(f"   {i+1}. {time_str} - {plan.get('description', 'Неизвестно')} (важность: {plan.get('importance', 'N/A')})")
                
                if len(today_plans) > 3:
                    self.logger.info(f"   ... и ещё {len(today_plans) - 3} планов")
                    
        except Exception as e:
            self.logger.error(f"Ошибка проверки планов при запуске: {e}")

    def check_database_health(self) -> Dict[str, Any]:
        """Проверяет состояние базы данных"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.enhanced_memory.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем основные таблицы
                tables_to_check = [
                    'virtual_activities', 
                    'planning_sessions', 
                    'memories', 
                    'conversations'
                ]
                
                table_status = {}
                for table in tables_to_check:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_status[table] = {"exists": True, "rows": count}
                    except sqlite3.OperationalError:
                        table_status[table] = {"exists": False, "rows": 0}
                
                # Размер БД
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
                return {
                    "db_path": self.enhanced_memory.db_path,
                    "db_size_mb": round(db_size / 1024 / 1024, 2),
                    "tables": table_status,
                    "health": "OK"
                }
                
        except Exception as e:
            return {
                "db_path": getattr(self.enhanced_memory, 'db_path', 'unknown'),
                "error": str(e),
                "health": "ERROR"
            }

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
            
            # ИСПРАВЛЕНО: db_path напрямую у OptimizedMemoryManager
            with sqlite3.connect(self.enhanced_memory.db_path) as conn:
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
                
                self.logger.info(f"📅 Найдено {len(plans)} ИИ-планов на {today}")
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
            
            # db_path напрямую
            db_path = self.enhanced_memory.db_path
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Общая статистика планирования
                cursor.execute("SELECT COUNT(*) FROM planning_sessions")
                total_sessions = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT COUNT(*) FROM virtual_activities WHERE generated_by_ai = 1")
                total_ai_activities = cursor.fetchone()[0] or 0
                
                # Статистика за последнюю неделю
                week_ago = (date.today() - timedelta(days=7)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM planning_sessions 
                    WHERE planning_date >= ?
                """, (week_ago,))
                weekly_sessions = cursor.fetchone()[0] or 0
                
                # Успешность планирования
                cursor.execute("""
                    SELECT COUNT(*) FROM planning_sessions 
                    WHERE success = 1 AND planning_date >= ?
                """, (week_ago,))
                successful_sessions = cursor.fetchone()[0] or 0
                
                # Планы на сегодня
                today = date.today().isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM virtual_activities
                    WHERE planning_date = ? AND generated_by_ai = 1
                """, (today,))
                today_plans = cursor.fetchone()[0] or 0
                
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
            # Отмечаем время проверки для мониторинга
            self._last_consciousness_check = datetime.now()
            
            current_time = datetime.now()
            self.logger.info(f"🧠 [CONSCIOUSNESS] Цикл сознания запущен в {current_time.strftime('%H:%M:%S')}")

            # Не активен ночью (23:00 - 7:00)
            if current_time.hour >= 23 or current_time.hour < 7:
                self.logger.info("😴 [CONSCIOUSNESS] Ночное время - пропускаю")
                return

            # Ограничение сообщений в день
            max_daily = self.config.get("behavior", {}).get("max_daily_initiatives", 8)
            if self.daily_message_count >= max_daily:
                self.logger.info(f"📊 [CONSCIOUSNESS] Лимит сообщений достигнут: {self.daily_message_count}/{max_daily}")
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
                self.logger.info("🚀 [CONSCIOUSNESS] Отправляю инициативные сообщения...")
                await self.send_initiative_messages(current_state)
                self.daily_message_count += 1
            else:
                self.logger.info("😐 [CONSCIOUSNESS] Инициатива не одобрена")

            # Иногда генерируем жизненные события
            if random.random() < 0.15:  # 15% шанс
                self.logger.info("🎲 [CONSCIOUSNESS] Генерирую жизненное событие...")
                await self.generate_life_event()

        except Exception as e:
            self.logger.error(f"💥 [CONSCIOUSNESS] Ошибка в цикле сознания: {e}", exc_info=True)

    async def _should_initiate_realistically(self, current_state: Dict) -> bool:
        """Решение об инициативе с динамическими интервалами"""

        initiative_desire = current_state.get("initiative_desire", 0)
        current_hour = datetime.now().hour
        is_weekend = datetime.now().weekday() >= 5
        activity_context = current_state.get("activity_context")

        self.logger.info(f"🤔 ПРОВЕРКА ИНИЦИАТИВЫ:")
        self.logger.info(f"   Желание: {initiative_desire}/10")
        self.logger.info(f"   Час: {current_hour}")
        self.logger.info(f"   Выходные: {is_weekend}")
        self.logger.info(f"   Активность: {activity_context}")
        self.logger.info(f"   Сообщений сегодня: {self.daily_message_count}")

        # 1. Ночное время - спим (ослабленное)
        if current_hour >= 24 or current_hour < 6:
            self.logger.info("😴 Слишком поздно/рано - не пишем")
            return False

        # 2. Минимальное желание (сильно ослабляем!)
        if initiative_desire < 0.5:  # Было 1, стало 0.5!
            self.logger.info(f"😐 Очень слабое желание: {initiative_desire} < 0.5")
            return False

        # 3. НОВАЯ СИСТЕМА: Динамические интервалы вместо жёстких 2 часов!
        dynamic_interval = await self._calculate_dynamic_interval(current_state)
        
        if self.last_message_time:
            hours_since = (datetime.now() - self.last_message_time).total_seconds() / 3600
            
            # Теперь интервал зависит от ситуации, а не жёстко 2 часа
            if hours_since < dynamic_interval:
                self.logger.info(f"⏰ Динамический интервал: {hours_since:.1f}ч < {dynamic_interval:.1f}ч")
                
                # НО! Добавляем шанс "спонтанности" даже при невыполненном интервале
                spontaneity_chance = await self._calculate_spontaneity_chance(current_state, hours_since, dynamic_interval)
                
                if random.random() < spontaneity_chance:
                    self.logger.info(f"✨ СПОНТАННОСТЬ! Пишем несмотря на интервал (шанс: {spontaneity_chance:.2f})")
                else:
                    self.logger.info(f"❌ Спонтанность не сработала (шанс: {spontaneity_chance:.2f})")
                    return False
            else:
                self.logger.info(f"✅ Динамический интервал пройден: {hours_since:.1f}ч >= {dynamic_interval:.1f}ч")

        # 4. Бонусы к желанию (увеличиваем!)
        bonus_reasons = []
        original_desire = initiative_desire

        # Часы пик активности (расширяем!)
        peak_hours = [8, 9, 12, 13, 16, 17, 19, 20, 21, 22]
        if current_hour in peak_hours:
            initiative_desire += 2
            bonus_reasons.append(f"час пик ({current_hour})")

        # Выходные - НАМНОГО активнее
        if is_weekend:
            initiative_desire += 3
            bonus_reasons.append("выходные")

        # Вечернее время
        if 18 <= current_hour <= 22:
            initiative_desire += 2
            bonus_reasons.append("вечер")

        # Учитываем персонажа
        character = self.character_loader.get_current_character()
        if character:
            name = character.get("name", "").lower()
            if "марин" in name or "китагава" in name:
                initiative_desire += 2
                bonus_reasons.append("активный персонаж (Марин)")

        # Бонус от текущего дела
        activity_bonus = await self._get_activity_initiative_bonus(current_state)
        if activity_bonus > 0:
            initiative_desire += activity_bonus
            bonus_reasons.append(f"интересное дело (+{activity_bonus})")

        if bonus_reasons:
            self.logger.info(f"✨ Бонусы: {', '.join(bonus_reasons)}")
            self.logger.info(f"   Желание: {original_desire} → {initiative_desire}")

        # 5. Работа теперь НЕ блокирует, а только уменьшает шанс
        work_penalty = await self._calculate_work_penalty(current_state)
        
        if work_penalty > 0:
            self.logger.info(f"💼 Рабочий штраф: -{work_penalty:.2f}")

        # 6. НОВАЯ облегченная формула!
        adjusted_desire = max(0.1, initiative_desire - work_penalty)  # Минимум 0.1

        # Более агрессивная формула для частых сообщений
        chance = min(0.95, adjusted_desire / 5)  # Было /6, стало /5!
        random_roll = random.random()

        should_send = random_roll < chance

        self.logger.info(f"🎲 ФИНАЛЬНАЯ ПРОВЕРКА:")
        self.logger.info(f"   Скорректированное желание: {adjusted_desire:.1f}")
        self.logger.info(f"   Шанс отправки: {chance:.2f} ({chance*100:.0f}%)")
        self.logger.info(f"   Случайное число: {random_roll:.2f}")
        self.logger.info(f"   Результат: {'✅ ОТПРАВЛЯЕМ!' if should_send else '❌ не отправляем'}")

        if should_send:
            self.logger.info(f"🚀 ИНИЦИАТИВА ОДОБРЕНА! Желание {adjusted_desire:.1f}, бонусы: {bonus_reasons}")

        return should_send
    
    async def _calculate_dynamic_interval(self, current_state: Dict) -> float:
        """Рассчитывает динамический интервал между сообщениями"""
        
        base_interval = 1.0  # Базовый интервал 1 час (было 2!)
        
        # Модификаторы интервала
        activity_context = current_state.get("activity_context", "")
        is_weekend = current_state.get("is_weekend", False)
        current_hour = datetime.now().hour
        
        # Выходные - чаще пишем
        if is_weekend:
            base_interval *= 0.7  # 42 минуты
        
        # Вечернее время - активнее
        if 18 <= current_hour <= 22:
            base_interval *= 0.8  # 48 минут
        
        # Обеденное время - может написать
        if 12 <= current_hour <= 14:
            base_interval *= 0.9  # 54 минуты
        
        # Рабочее время - реже, но не блокируем полностью
        if activity_context == "work_time" and not is_weekend:
            base_interval *= 1.5  # 1.5 часа
        
        # Добавляем случайность ±30%
        randomness = random.uniform(0.7, 1.3)
        final_interval = base_interval * randomness
        
        # Ограничиваем: минимум 20 минут, максимум 4 часа
        final_interval = max(0.33, min(4.0, final_interval))
        
        self.logger.debug(f"🕐 Динамический интервал: {final_interval:.1f}ч (база: {base_interval:.1f}ч)")
        
        return final_interval
    
    async def _calculate_spontaneity_chance(self, current_state: Dict, hours_since: float, required_interval: float) -> float:
        """Рассчитывает шанс спонтанности при невыполненном интервале"""
        
        # Базовый шанс спонтанности зависит от того, насколько близко к интервалу
        progress = hours_since / required_interval  # От 0 до 1
        
        # Базовый шанс растёт с приближением к интервалу
        base_chance = max(0, (progress - 0.3) * 0.4)  # После 30% интервала начинает расти
        
        # Модификаторы спонтанности
        initiative_desire = current_state.get("initiative_desire", 0)
        is_weekend = current_state.get("is_weekend", False)
        activity_context = current_state.get("activity_context", "")
        
        # Высокое желание = больше спонтанности
        if initiative_desire >= 7:
            base_chance += 0.15
        elif initiative_desire >= 5:
            base_chance += 0.08
        
        # Выходные = больше спонтанности
        if is_weekend:
            base_chance += 0.1
        
        # Вечернее время = больше спонтанности
        current_hour = datetime.now().hour
        if 19 <= current_hour <= 22:
            base_chance += 0.08
        
        # Обеденное время = средняя спонтанность
        if 12 <= current_hour <= 14:
            base_chance += 0.05
        
        # Рабочее время = меньше спонтанности, но не ноль
        if activity_context == "work_time" and not is_weekend:
            base_chance *= 0.3  # Сильно уменьшаем, но не убираем
        
        # Персонаж-модификатор
        character = self.character_loader.get_current_character()
        if character:
            name = character.get("name", "").lower()
            if "марин" in name or "китагава" in name:
                base_chance += 0.1  # Марин более спонтанная
        
        # Ограничиваем шанс
        final_chance = max(0, min(0.4, base_chance))  # Максимум 40% спонтанности
        
        self.logger.debug(f"✨ Шанс спонтанности: {final_chance:.2f} (прогресс: {progress:.2f})")
        
        return final_chance
    
    async def _get_activity_initiative_bonus(self, current_state: Dict) -> float:
        """Бонус к инициативе от текущей активности"""
        
        # Получаем контекст виртуальной жизни
        virtual_context = current_state.get("virtual_life_context", "")
        
        bonus = 0.0
        
        # Парсим контекст для поиска интересных активностей
        if "косплей" in virtual_context.lower():
            bonus += 1.5  # Косплей = хочется поделиться
        
        if "хобби" in virtual_context.lower() or "hobby" in virtual_context.lower():
            bonus += 1.0  # Хобби = энтузиазм
        
        if "друзья" in virtual_context.lower() or "social" in virtual_context.lower():
            bonus += 0.8  # Социальная активность = хочется общаться
        
        if "важность: 8" in virtual_context or "важность: 9" in virtual_context or "важность: 10" in virtual_context:
            bonus += 0.5  # Важное дело = может написать об этом
        
        if "свободна" in virtual_context.lower():
            bonus += 1.2  # Свободна = больше времени на общение
        
        self.logger.debug(f"🎯 Бонус от активности: +{bonus:.1f}")
        
        return bonus

    async def _calculate_work_penalty(self, current_state: Dict) -> float:
        """Рассчитывает штраф за рабочее время (вместо полной блокировки)"""
        
        activity_context = current_state.get("activity_context", "")
        is_weekend = current_state.get("is_weekend", False)
        current_hour = datetime.now().hour
        
        # Рабочее время в будни
        if activity_context == "work_time" and not is_weekend:
            # Получаем важность текущего дела
            virtual_context = current_state.get("virtual_life_context", "")
            
            # Если очень важное дело (8-10) - больше штраф
            if any(pattern in virtual_context for pattern in ["важность: 8", "важность: 9", "важность: 10", "ВАЖНО"]):
                penalty = 2.0  # Серьёзный штраф, но не блокировка
                self.logger.debug("💼 Важное рабочее дело - большой штраф")
            # Обычное рабочее время
            else:
                penalty = 1.0  # Умеренный штраф
                self.logger.debug("💼 Обычное рабочее время - умеренный штраф")
            
            # В обеденное время штраф меньше
            if 12 <= current_hour <= 14:
                penalty *= 0.5
                self.logger.debug("🍽️ Обеденное время - штраф уменьшен")
                
            return penalty
        
        return 0.0

    async def update_virtual_life(self):
        """Обновляет виртуальную жизнь персонажа (ИСПРАВЛЕНО)"""
        try:
            changes = self.virtual_life.check_and_update_activities()

            # Уведомляем только при реальных изменениях
            if changes["status_changed"]:
                if changes["activity_started"]:
                    activity = changes["activity_started"]
                    await self._notify_activity_start(activity)

                elif changes["activity_ended"]:
                    activity = changes["activity_ended"]
                    # Уведомляем только о важных завершениях
                    await self._notify_activity_end(activity)
            # Если нет изменений - ничего не делаем

        except Exception as e:
            self.logger.error(f"Ошибка обновления виртуальной жизни: {e}")

    async def _notify_activity_start(self, activity: VirtualActivity):
        """Уведомления о начале активности"""
        
        # Проверяем что не уведомляли уже об этой активности
        if activity.id in self.notified_activities:
            self.logger.info(f"⏭️ Уведомление о активности {activity.id} уже отправлено, пропускаем")
            return
        
        # Добавляем в список уведомленных
        self.notified_activities.add(activity.id)
        
        try:
            # Используем AI-гуманизатор для конвертации описания
            if hasattr(self.virtual_life, 'activity_humanizer') and self.virtual_life.activity_humanizer:
                try:
                    humanized_activity = await self.virtual_life.activity_humanizer.humanize_activity(
                        activity_type=activity.activity_type,
                        start_time=activity.start_time.strftime('%H:%M'),
                        duration=float((activity.end_time - activity.start_time).total_seconds() / 3600),
                        importance=getattr(activity, 'importance', 5),
                        emotional_reason=getattr(activity, 'emotional_reason', ''),
                        current_mood="нормальное"
                    )
                    
                    self.logger.info(f"🎭 AI гуманизировал активность: {activity.activity_type} -> {humanized_activity}")
                    
                    messages = [
                        f"Кстати, я сейчас {humanized_activity}! ✨",
                        f"Буду заниматься этим до {activity.end_time.strftime('%H:%M')}",
                        "Но ты всегда можешь мне писать! 💕"
                    ]
                    
                except Exception as e:
                    self.logger.error(f"Ошибка AI-гуманизации в уведомлении: {e}")
                    messages = self._get_fallback_activity_messages(activity)
            else:
                messages = self._get_fallback_activity_messages(activity)

            # Отправляем уведомления пользователям
            if hasattr(self, "allowed_users") and self.allowed_users:
                current_state = await self.optimized_ai.get_simple_mood_calculation(
                    self.psychological_core
                )

                await self.send_telegram_messages_with_timing(
                    chat_id=list(self.allowed_users)[0],  # Первый пользователь
                    messages=messages,
                    current_state=current_state,
                )
                
                self.logger.info(f"📨 Уведомление отправлено для активности: {activity.description}")
        
        except Exception as e:
            # Если ошибка - убираем из списка уведомленных, чтобы попробовать ещё раз
            self.notified_activities.discard(activity.id)
            self.logger.error(f"Критическая ошибка в _notify_activity_start: {e}")

    def _get_fallback_activity_messages(self, activity: VirtualActivity) -> List[str]:
        """Fallback сообщения с улучшенными человеческими описаниями"""
        
        character = self.character_loader.get_current_character()
        
        # Человеческие описания активностей
        activity_descriptions = {
            "personal": "занимаюсь личными делами",
            "work": "работаю/учусь", 
            "hobby": "занимаюсь любимым хобби",
            "rest": "отдыхаю дома",
            "social": "общаюсь с друзьями",
            "cosplay": "работаю над костюмом",
            "study": "изучаю что-то интересное",
            "gaming": "играю в игры",
            "reading": "читаю книгу/мангу",
            "shopping": "хожу по магазинам"
        }
        
        # Специальные описания для Марин
        if character and 'марин' in character.get('name', '').lower():
            marin_descriptions = {
                "hobby": "работаю над новым косплеем",
                "personal": "занимаюсь косплей-проектами",
                "rest": "смотрю аниме и расслабляюсь",
                "social": "болтаю с подругами о косплее",
                "study": "изучаю новых персонажей для косплея"
            }
            activity_descriptions.update(marin_descriptions)
        
        activity_desc = activity_descriptions.get(
            activity.activity_type, 
            activity.description or activity.activity_type
        )
        
        return [
            f"Кстати, я сейчас {activity_desc}! ✨",
            f"Буду заниматься этим до {activity.end_time.strftime('%H:%M')}",
            "Но ты всегда можешь мне писать! 💕"
        ]
    
    def clean_activity_notifications(self):
        """Очищает список уведомленных активностей (вызывать в полночь)"""
        self.notified_activities.clear()
        self.logger.info("🗑️ Список уведомленных активностей очищен")

    async def _notify_activity_end(self, activity: VirtualActivity):
        """🔧 ОПЦИОНАЛЬНЫЕ уведомления о завершении (отключены по умолчанию)"""
        
        # ОТКЛЮЧЕНО: Не спамим уведомлениями о каждом завершении
        # Можно включить только для важных активностей
        
        importance = getattr(activity, 'importance', 5)
        if importance >= 8:  # Только для очень важных активностей
            try:
                messages = [
                    f"Я закончила {activity.description}! ✅",
                    "Теперь я свободна и готова пообщаться! 😊"
                ]

                if hasattr(self, "allowed_users") and self.allowed_users:
                    current_state = await self.optimized_ai.get_simple_mood_calculation(
                        self.psychological_core
                    )

                    await self.send_telegram_messages_with_timing(
                        chat_id=list(self.allowed_users)[0],
                        messages=messages,
                        current_state=current_state,
                    )
                        
            except Exception as e:
                self.logger.error(f"Ошибка уведомления о завершении: {e}")
        else:
            # Просто логируем без уведомления
            self.logger.info(f"🏁 Активность завершена: {activity.description}")

    def _get_fallback_completion_messages(self, activity: VirtualActivity) -> List[str]:
        """Fallback сообщения о завершении активности"""
        
        character = self.character_loader.get_current_character()
        
        completion_descriptions = {
            "personal": "закончила с личными делами",
            "work": "закончила работать/учиться",
            "hobby": "завершила творческий процесс", 
            "rest": "отдохнула и восстановилась",
            "social": "пообщалась с друзьями",
            "cosplay": "поработала над костюмом",
            "study": "закончила изучать материал",
            "gaming": "наигралась в игры",
            "reading": "дочитала интересную главу",
            "shopping": "закончила с покупками",
            "exercise": "завершила тренировку",
            "cooking": "приготовила что-то вкусное",
            "cleaning": "навела порядок"
        }
        
        # Для Марин
        if character and 'марин' in character.get('name', '').lower():
            marin_completions = {
                "hobby": "поработала над косплеем",
                "personal": "завершила косплей-проекты",
                "rest": "посмотрела аниме",
                "social": "поболтала с подругами о косплее",
                "study": "изучила новых персонажей"
            }
            completion_descriptions.update(marin_completions)
        
        completion_desc = completion_descriptions.get(
            activity.activity_type, 
            activity.description or f"завершила {activity.activity_type}"
        )
        
        return [
            f"Я {completion_desc}! ✅",
            "Теперь я свободна и готова пообщаться! 😊"
        ]

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
        """Отправка инициативных сообщений с учётом виртуальной жизни"""

        # Получаем контекст из базы данных
        db_context = self.enhanced_memory.get_context_for_response(
            "инициативное общение"
        )
        current_state["memory_context"] = db_context

        # Добавляем контекст виртуальной жизни
        virtual_context = self.virtual_life.get_current_context_for_ai()
        current_state["virtual_life_context"] = virtual_context

        # Добавляем контекст персонажа
        character_context = self.character_loader.get_character_context_for_ai()
        current_state["character_context"] = character_context

        # Получаем текущего персонажа для специальных тем
        character = self.character_loader.get_current_character()
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

            # 🔧 ИСПРАВЛЕНО: Сначала получаем текущее состояние
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )

            # Получаем контекст из базы данных
            db_context = self.enhanced_memory.get_context_for_response(message)
            current_state["memory_context"] = db_context

            # Добавляем контекст виртуальной жизни
            try:
                if hasattr(self.virtual_life, 'get_current_context_for_ai_async'):
                    virtual_context = await self.virtual_life.get_current_context_for_ai_async()
                    self.logger.info("🎭 Получен AI-гуманизированный контекст виртуальной жизни")
                else:
                    virtual_context = self.virtual_life.get_current_context_for_ai()
                    self.logger.info("⚠️ Использован fallback контекст виртуальной жизни")
                
                current_state["virtual_life_context"] = virtual_context
                
            except Exception as e:
                self.logger.error(f"Ошибка получения виртуального контекста: {e}")
                current_state["virtual_life_context"] = "Виртуальная жизнь недоступна"

            # Добавляем контекст персонажа
            character_context = self.character_loader.get_character_context_for_ai()
            current_state["character_context"] = character_context

            self.logger.info(f"Контекст персонажа: {character_context[:100]}...")
            self.logger.info(f"Контекст виртуальной жизни: {virtual_context[:100]}...")

            # ✅ ТЕПЕРЬ генерируем ответ с полным контекстом
            ai_response_text = await self.optimized_ai.generate_raw_response(message, current_state)

            # 🤖📅 Парсинг и выполнение команд планирования
            if not hasattr(self, 'ai_planner_parser'):
                self.ai_planner_parser = AISelfPlanningParser(self.virtual_life, self.logger)
            
            cleaned_response = self.ai_planner_parser.parse_and_execute_plans(ai_response_text)

            # Обрабатываем очищенный ответ
            ai_messages = self.optimized_ai._process_raw_response(cleaned_response)

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

        try:
            if hasattr(self.virtual_life, 'get_current_context_for_ai_async'):
                virtual_context = await self.virtual_life.get_current_context_for_ai_async()
                self.logger.info("🎭 Инициатива с AI-гуманизированным контекстом")
            else:
                virtual_context = self.virtual_life.get_current_context_for_ai()
                self.logger.info("⚠️ Инициатива с fallback контекстом")
            
            current_state["virtual_life_context"] = virtual_context
            
        except Exception as e:
            self.logger.error(f"Ошибка получения виртуального контекста для инициативы: {e}")
            current_state["virtual_life_context"] = "Виртуальная жизнь недоступна"

        # Добавляем контекст персонажа
        character_context = self.character_loader.get_character_context_for_ai()
        current_state["character_context"] = character_context

        # Получаем текущего персонажа для специальных тем
        character = self.character_loader.get_current_character()
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

        if not messages:
            self.logger.warning("deliver_messages_with_timing: Нет сообщений для доставки")
            return

        self.logger.info(f"🚀 Доставка {len(messages)} сообщений типа '{message_type}'")
        
        emotional_state = current_state.get("dominant_emotion", "calm")
        energy_level = current_state.get("energy_level", 50)

        # Адаптивная скорость печатания в зависимости от состояния
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
            try:
                self.logger.info(f"📨 Вызов deliver_message для: {msg[:30]}...")
                await self.deliver_message(msg, message_type)
                self.logger.info("✅ deliver_message выполнен успешно")
            except Exception as e:
                self.logger.error(f"❌ Ошибка в deliver_message: {e}")
                raise

        async def typing_callback(is_typing):
            # Будет переопределено в интеграциях
            if is_typing:
                self.logger.debug("⌨️ Показываем 'печатает...'")
            else:
                self.logger.debug("🔇 Скрываем 'печатает...'")

        # Показываем сводку времени (если включено в логах)
        if self.config.get("logging", {}).get("log_timing_details", True):
            timing_summary = self.typing_simulator.get_realistic_delays_summary(
                messages, emotional_state, energy_level
            )
            self.logger.info(
                f"⏱️ Планируемое время отправки: {timing_summary['total_time']}с, режим: {self.typing_simulator.current_mode}"
            )

        try:
            # Отправляем с реалистичными паузами
            await self.typing_simulator.send_messages_with_realistic_timing(
                messages=messages,
                emotional_state=emotional_state,
                energy_level=energy_level,
                send_callback=send_callback,
                typing_callback=typing_callback,
            )
            
            self.logger.info(f"🎊 ДОСТАВКА ЗАВЕРШЕНА: {len(messages)} сообщений")
            
        except Exception as e:
            self.logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА доставки: {e}")
            self.logger.error(f"💥 Параметры: type={message_type}, emotion={emotional_state}")
            raise

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

        # Добавляем информацию о персонаже
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

