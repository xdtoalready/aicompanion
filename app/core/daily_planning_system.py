"""
Система ИИ-планирования для автоматического создания планов дня (ИСПРАВЛЕНО)
"""

import json
import logging
import sqlite3
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .prompt_manager import get_prompt_manager

@dataclass
class PlannedActivity:
    """Запланированная активность"""
    activity_type: str
    description: str
    start_hour: int
    start_minute: int = 0
    duration_hours: float = 1.0
    importance: int = 5
    flexibility: int = 5
    emotional_reason: str = ""
    can_reschedule: bool = True
    weather_dependent: bool = False

class DailyPlanningSystem:
    """Система ежедневного ИИ-планирования (ИСПРАВЛЕНО)"""
    
    def __init__(self, db_path: str, api_manager, character_loader, config: Dict[str, Any]):
        self.db_path = db_path
        self.api_manager = api_manager
        self.character_loader = character_loader
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Prompt Manager
        self.prompt_manager = get_prompt_manager()

        # Кэш последнего планирования
        self.last_planning_date = None

        # Создаём недостающие таблицы если их нет
        self._ensure_planning_tables()
    
    def _ensure_planning_tables(self):
        """Создаёт таблицы планирования если их нет"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем есть ли таблица planning_sessions
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='planning_sessions'
                """)
                
                if not cursor.fetchone():
                    # Создаём таблицу planning_sessions
                    cursor.execute("""
                        CREATE TABLE planning_sessions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            character_id INTEGER DEFAULT 1,
                            planning_date DATE NOT NULL,
                            planning_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                            day_of_week TEXT,
                            character_mood TEXT,
                            weather_context TEXT,
                            total_activities_planned INTEGER DEFAULT 0,
                            planning_prompt TEXT,
                            ai_response TEXT,
                            success BOOLEAN DEFAULT TRUE
                        )
                    """)
                    self.logger.info("📋 Создана таблица planning_sessions")
                
                # Добавляем недостающие колонки в virtual_activities
                columns_to_add = [
                    ("planning_date", "DATE"),
                    ("generated_by_ai", "BOOLEAN DEFAULT FALSE"),
                    ("flexibility", "INTEGER DEFAULT 5"),
                    ("importance", "INTEGER DEFAULT 5"),
                    ("planned_by", "TEXT DEFAULT 'auto'"),
                    ("emotional_reason", "TEXT"),
                    ("can_reschedule", "BOOLEAN DEFAULT TRUE")
                ]
                
                for column_name, column_def in columns_to_add:
                    try:
                        cursor.execute(f"ALTER TABLE virtual_activities ADD COLUMN {column_name} {column_def}")
                        self.logger.debug(f"Добавлена колонка: {column_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e).lower():
                            continue  # Колонка уже существует
                        else:
                            self.logger.error(f"Ошибка добавления колонки {column_name}: {e}")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Ошибка создания таблиц планирования: {e}")
    
    async def should_plan_today(self) -> bool:
        """Проверяет нужно ли планировать сегодня (УЛУЧШЕННАЯ)"""
        
        today = date.today()
        
        # Уже планировали сегодня?
        if self.last_planning_date == today:
            self.logger.info(f"Планирование уже выполнялось сегодня: {today}")
            return False
        
        # 🔧 ИСПРАВЛЕНО: Проверяем есть ли планы на сегодня
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем планы на сегодня
                cursor.execute("""
                    SELECT COUNT(*) FROM virtual_activities 
                    WHERE DATE(start_time) = ? 
                    AND generated_by_ai = 1
                    AND status IN ('planned', 'active')
                """, (today.isoformat(),))
                
                existing_plans = cursor.fetchone()[0]
                
                self.logger.info(f"Найдено существующих планов на {today}: {existing_plans}")
                
                # Если есть больше 2 планов, считаем что уже запланировали
                if existing_plans >= 2:
                    self.logger.info(f"На {today} уже есть {existing_plans} ИИ-планов - планирование не нужно")
                    self.last_planning_date = today
                    return False
                
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки планов: {e}")
            return True
    
    async def generate_daily_plan(self) -> bool:
        """🔧 ИСПРАВЛЕННАЯ генерация плана дня"""
        
        today = date.today()
        
        if not await self.should_plan_today():
            return False
        
        self.logger.info(f"🧠📅 Генерирую план на {today}")
        
        try:
            # 🔧 НОВОЕ: Очищаем старые планы на сегодня перед созданием новых
            await self._clear_existing_plans(today)
            
            # Получаем контекст для планирования
            planning_context = await self._build_planning_context()
            
            # Создаём промпт
            planning_prompt = self._build_planning_prompt(planning_context)
            
            # Делаем запрос к ИИ через PLANNING API
            from .gemini_api_manager import APIUsageType
            
            response = await self.api_manager.make_request(
                APIUsageType.PLANNING,
                model=self.config.get('ai', {}).get('model', 'deepseek/deepseek-chat'),
                messages=[
                    {"role": "system", "content": planning_prompt},
                    {"role": "user", "content": f"Запланируй день для {today.strftime('%A, %d.%m.%Y')}"}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            if not response or not response.choices:
                self.logger.error("Пустой ответ от ИИ планировщика")
                return False
            
            ai_response = response.choices[0].message.content.strip()
            
            # Парсим и сохраняем планы
            success = await self._parse_and_save_plans_fixed(ai_response, planning_context)
            
            if success:
                self.last_planning_date = today
                self.logger.info("✅ План дня успешно сгенерирован")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации плана дня: {e}")
            return False
        
    async def _clear_existing_plans(self, target_date: date):
        """🔧 НОВОЕ: Очищает существующие планы на указанную дату"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Удаляем только запланированные ИИ-планы (не активные!)
                cursor.execute("""
                    DELETE FROM virtual_activities 
                    WHERE DATE(start_time) = ? 
                    AND generated_by_ai = 1
                    AND status = 'planned'
                """, (target_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"🗑️ Удалено {deleted_count} старых планов на {target_date}")
                
        except Exception as e:
            self.logger.error(f"Ошибка очистки планов: {e}")
    
    async def _parse_and_save_plans_fixed(self, ai_response: str, context: Dict[str, Any]) -> bool:
        """ИСПРАВЛЕННЫЙ парсинг ответа ИИ и сохранение планов"""
        
        try:
            self.logger.debug(f"Парсинг ответа ИИ: {ai_response[:200]}...")
            
            # 1. Пытаемся найти JSON в ответе (между ``` или прямо)
            json_text = self._extract_json_from_response(ai_response)
            
            if not json_text:
                self.logger.error("JSON не найден в ответе ИИ")
                return False
            
            # 2. ИСПРАВЛЕНО: Очищаем JSON от возможных проблем
            cleaned_json = self._clean_json_response(json_text)
            
            # 3. Парсим JSON
            try:
                plan_data = json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                self.logger.error(f"Ошибка парсинга JSON: {e}")
                self.logger.error(f"Проблемный JSON: {cleaned_json}")
                
                # Пытаемся парсить активности напрямую если основной JSON сломан
                activities = self._parse_activities_from_broken_json(ai_response)
                if activities:
                    plan_data = {"activities": activities, "day_mood": "обычный день"}
                else:
                    return False
            
            activities = plan_data.get('activities', [])
            day_mood = plan_data.get('day_mood', 'обычный день')
            
            if not activities:
                self.logger.error("Нет активностей в плане")
                return False
            
            # 4. Сохраняем в БД
            today = date.today()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Сначала сохраняем сессию планирования
                cursor.execute("""
                    INSERT INTO planning_sessions
                    (planning_date, day_of_week, character_mood, 
                     total_activities_planned, planning_prompt, ai_response, success)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    today.isoformat(),
                    context['weekday'],
                    f"{context['current_mood']} -> {day_mood}",
                    len(activities),
                    self._build_planning_prompt(context)[:1000],
                    ai_response[:2000],
                    True
                ))
                
                # Сохраняем каждую активность
                saved_count = 0
                for i, activity in enumerate(activities):
                    try:
                        saved = self._save_single_activity(cursor, activity, today)
                        if saved:
                            saved_count += 1
                    except Exception as e:
                        self.logger.error(f"Ошибка сохранения активности {i}: {e}")
                        continue
                
                conn.commit()
                
                self.logger.info(f"📅 Сохранено {saved_count}/{len(activities)} активностей на {today}")
                return saved_count > 0
                
        except Exception as e:
            self.logger.error(f"Критическая ошибка сохранения плана: {e}")
            return False
    
    def _extract_json_from_response(self, response: str) -> str:
        """Извлекает JSON из ответа ИИ"""
        
        # Ищем JSON между ```json и ```
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Ищем JSON между ``` и ```
        json_match = re.search(r'```\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Ищем просто JSON блок
        json_match = re.search(r'(\{[^}]*"activities"[^}]*\})', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Ищем от первой { до последней }
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1 and end > start:
            return response[start:end+1]
        
        return ""
    
    def _clean_json_response(self, json_text: str) -> str:
        """ИСПРАВЛЕНО: Очищает JSON от типичных проблем"""
        
        # Убираем комментарии
        json_text = re.sub(r'//.*', '', json_text)
        
        # Исправляем trailing commas
        json_text = re.sub(r',\s*}', '}', json_text)
        json_text = re.sub(r',\s*]', ']', json_text)
        
        # Заменяем одинарные кавычки на двойные (если есть)
        json_text = re.sub(r"'([^']*)':", r'"\1":', json_text)
        
        # Убираем лишние запятые
        json_text = re.sub(r',+', ',', json_text)
        
        return json_text.strip()
    
    def _parse_activities_from_broken_json(self, response: str) -> List[Dict]:
        """Fallback: пытается извлечь активности из сломанного JSON"""
        
        activities = []
        
        # Ищем паттерны активностей
        activity_pattern = r'"activity_type":\s*"([^"]+)"[^}]*"description":\s*"([^"]+)"[^}]*"start_hour":\s*(\d+)'
        
        matches = re.findall(activity_pattern, response)
        
        for match in matches:
            activity_type, description, start_hour = match
            
            activities.append({
                "activity_type": activity_type,
                "description": description,
                "start_hour": int(start_hour),
                "start_minute": 0,
                "duration_hours": 2.0,
                "importance": 5,
                "flexibility": 5,
                "emotional_reason": "запланированная активность",
                "can_reschedule": True
            })
        
        self.logger.info(f"Извлечено {len(activities)} активностей из сломанного JSON")
        return activities
    
    def _save_single_activity(self, cursor, activity: Dict, today: date) -> bool:
        """Сохраняет одну активность в БД"""
        
        try:
            start_hour = activity.get('start_hour', 9)
            start_minute = activity.get('start_minute', 0)
            
            # ИСПРАВЛЕНО: Безопасное создание времени
            start_time = datetime.combine(
                today,
                datetime.min.time().replace(
                    hour=max(0, min(23, start_hour)),
                    minute=max(0, min(59, start_minute))
                )
            )
            
            duration = float(activity.get('duration_hours', 1.0))
            end_time = start_time + timedelta(hours=duration)
            
            cursor.execute("""
                INSERT INTO virtual_activities
                (character_id, activity_type, description, start_time, end_time,
                 status, planned_by, flexibility, importance, emotional_reason,
                 can_reschedule, planning_date, generated_by_ai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # character_id
                activity.get('activity_type', 'unknown'),
                activity.get('description', 'Запланированная активность'),
                start_time.isoformat(),
                end_time.isoformat(),
                'planned',
                'ai_planner',
                activity.get('flexibility', 5),
                activity.get('importance', 5),
                activity.get('emotional_reason', ''),
                activity.get('can_reschedule', True),
                today.isoformat(),
                True
            ))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения активности: {e}")
            return False

    # Остальные методы остаются без изменений...
    async def _build_planning_context(self) -> Dict[str, Any]:
        """Собирает контекст для планирования"""
        
        today = date.today()
        weekday = today.weekday()
        is_weekend = weekday >= 5
        
        weekday_names = [
            "понедельник", "вторник", "среда", "четверг", 
            "пятница", "суббота", "воскресенье"
        ]
        weekday_name = weekday_names[weekday]
        
        character = self.character_loader.get_current_character()
        character_context = self.character_loader.get_character_context_for_ai() if character else ""
        
        previous_plans = await self._get_recent_plans(days=7)
        pending_desires = await self._get_pending_desires()
        
        import random
        moods = ["энергичная", "спокойная", "мечтательная", "сосредоточенная", "игривая"]
        current_mood = random.choice(moods)
        
        return {
            "date": today.isoformat(),
            "weekday": weekday_name,
            "is_weekend": is_weekend,
            "character_context": character_context,
            "current_mood": current_mood,
            "previous_plans": previous_plans,
            "pending_desires": pending_desires,
            "character_name": character.get('name', 'AI') if character else 'AI'
        }
    
    def _build_planning_prompt(self, context: Dict[str, Any]) -> str:
        """🔧 УЛУЧШЕННЫЙ промпт для планирования (из темплейта)"""

        current_hour = datetime.now().hour

        # Добавляем current_hour в контекст для темплейта
        template_context = {
            **context,
            'current_hour': current_hour
        }

        # Рендерим промпт из темплейта
        return self.prompt_manager.render('planning.jinja2', template_context)
    
    async def _get_recent_plans(self, days: int = 7) -> str:
        """Получает недавние планы для контекста"""
        try:
            week_ago = (date.today() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT planning_date, day_of_week, total_activities_planned
                    FROM planning_sessions
                    WHERE planning_date >= ?
                    ORDER BY planning_date DESC
                    LIMIT 5
                """, (week_ago,))
                
                plans = cursor.fetchall()
                
                if not plans:
                    return "Предыдущих планов нет"
                
                summary = []
                for plan_date, weekday, activities_count in plans:
                    summary.append(f"{weekday}: {activities_count} активностей")
                
                return "Недавно: " + ", ".join(summary)
                
        except Exception as e:
            self.logger.error(f"Ошибка получения предыдущих планов: {e}")
            return "Ошибка загрузки истории"
    
    async def _get_pending_desires(self) -> str:
        """Получает незавершённые желания"""
        return "Нет незавершённых желаний"