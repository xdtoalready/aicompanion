import asyncio
import json
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class VirtualActivity:
    """Виртуальная активность"""
    id: int
    activity_type: str  # "work", "hobby", "rest", "social", "cosplay"
    description: str    # "работаю над костюмом Шизуку"
    start_time: datetime
    end_time: datetime
    status: str         # "planned", "active", "completed", "cancelled"
    mood_effect: float  # как влияет на настроение (-3 до +3)
    energy_cost: int    # сколько энергии тратит (0-100)

class VirtualLifeManager:
    """Менеджер виртуальной жизни персонажа"""
    
    def __init__(self, db_path: str, character_loader=None):
        self.db_path = db_path
        self.character_loader = character_loader
        self.logger = logging.getLogger(__name__)
        
        # Текущее состояние
        self.current_activity: Optional[VirtualActivity] = None
        self.location = "дома"  # где находится персонаж
        self.availability = "free"  # free, busy, away
        
        self._ensure_tables_exist()
        self._load_current_state()
    
    def _ensure_tables_exist(self):
        """Создает таблицы для виртуальной жизни"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица активностей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS virtual_activities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        character_id INTEGER DEFAULT 1,
                        activity_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        start_time DATETIME NOT NULL,
                        end_time DATETIME NOT NULL,
                        status TEXT DEFAULT 'planned',
                        mood_effect REAL DEFAULT 0,
                        energy_cost INTEGER DEFAULT 20,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица состояний персонажа
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS character_states (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        character_id INTEGER DEFAULT 1,
                        location TEXT DEFAULT 'дома',
                        availability TEXT DEFAULT 'free',
                        current_activity_id INTEGER,
                        mood_modifier REAL DEFAULT 0,
                        energy_level INTEGER DEFAULT 80,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (current_activity_id) REFERENCES virtual_activities(id)
                    )
                """)
                
                conn.commit()
                self.logger.info("📅 Таблицы виртуальной жизни созданы")
                
        except Exception as e:
            self.logger.error(f"Ошибка создания таблиц виртуальной жизни: {e}")
    
    def _load_current_state(self):
        """Загружает текущее состояние персонажа"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Получаем последнее состояние
                cursor.execute("""
                    SELECT location, availability, current_activity_id
                    FROM character_states 
                    WHERE character_id = 1
                    ORDER BY last_updated DESC 
                    LIMIT 1
                """)
                
                result = cursor.fetchone()
                if result:
                    self.location = result[0]
                    self.availability = result[1]
                    
                    # Загружаем текущую активность если есть
                    if result[2]:
                        self.current_activity = self._get_activity_by_id(result[2])
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки состояния: {e}")

    def _get_today_ai_plans(self) -> List[Dict]:
        """Получает ИИ-планы на сегодня"""
        try:
            from datetime import date
            today = date.today()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, activity_type, description, start_time, end_time,
                        importance, flexibility, emotional_reason
                    FROM virtual_activities
                    WHERE DATE(start_time) = ? AND generated_by_ai = 1
                    ORDER BY start_time ASC
                """, (today.isoformat(),))
                
                plans = []
                for row in cursor.fetchall():
                    plans.append({
                        'id': row[0],
                        'activity_type': row[1],
                        'description': row[2],
                        'start_time': row[3],
                        'end_time': row[4],
                        'importance': row[5] or 5,
                        'flexibility': row[6] or 5,
                        'emotional_reason': row[7] or ''
                    })
                
                return plans
                
        except Exception as e:
            self.logger.error(f"Ошибка получения ИИ-планов: {e}")
            return []
        
    def check_and_update_activities(self):
        """Обновляет виртуальную жизнь персонажа (ИСПРАВЛЕНО)"""
        try:
            changes = {
                "activity_started": None,
                "activity_ended": None, 
                "status_changed": False
            }
            
            now = datetime.now()
            
            # НОВОЕ: Получаем ИИ-планы на сегодня
            ai_plans = self._get_today_ai_plans()
            
            # Проверяем текущую активность из ИИ-планов
            for plan in ai_plans:
                try:
                    plan_start = datetime.fromisoformat(plan['start_time'])
                    plan_end = datetime.fromisoformat(plan['end_time'])
                    
                    # Активность должна начаться
                    if plan_start <= now < plan_end and not self.current_activity:
                        activity = VirtualActivity(
                            id=plan['id'],
                            activity_type=plan['activity_type'],
                            description=plan['description'],
                            start_time=plan_start,
                            end_time=plan_end,
                            status="active",
                            mood_effect=0.0,
                            energy_cost=20
                        )
                        
                        self.current_activity = activity
                        self.availability = "busy"
                        changes["activity_started"] = activity
                        changes["status_changed"] = True
                        
                        self.logger.info(f"🎭 Начата ИИ-активность: {activity.description}")
                        break
                    
                    # Активность должна закончиться
                    elif self.current_activity and now >= plan_end:
                        if self.current_activity.id == plan['id']:
                            changes["activity_ended"] = self.current_activity
                            self.current_activity = None
                            self.availability = "free"
                            changes["status_changed"] = True
                            
                            self.logger.info(f"✅ Завершена ИИ-активность")
                            break
                            
                except Exception as e:
                    self.logger.error(f"Ошибка обработки плана {plan}: {e}")
                    continue
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления виртуальной жизни: {e}")
            return {"activity_started": None, "activity_ended": None, "status_changed": False}
        
    def get_current_context_for_ai(self) -> str:
        """Возвращает контекст текущей активности для AI (ИСПРАВЛЕНО)"""
        context_parts = []
        
        context_parts.append(f"ТЕКУЩЕЕ МЕСТОПОЛОЖЕНИЕ: {self.location}")
        context_parts.append(f"ДОСТУПНОСТЬ: {self.availability}")
        
        # Получаем ИИ-планы
        ai_plans = self._get_today_ai_plans()
        current_time = datetime.now()
        
        # Ищем текущую активность и ближайшие планы
        current_plan = None
        upcoming_plans = []
        
        for plan in ai_plans:
            try:
                plan_start = datetime.fromisoformat(plan['start_time'])
                plan_end = datetime.fromisoformat(plan['end_time'])
                
                if plan_start <= current_time < plan_end:
                    current_plan = plan
                elif plan_start > current_time:
                    upcoming_plans.append(plan)
            except Exception as e:
                self.logger.error(f"Ошибка обработки времени плана: {e}")
                continue
        
        if current_plan:
            try:
                time_left = (datetime.fromisoformat(current_plan['end_time']) - current_time).total_seconds() / 3600
                
                context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {current_plan['description']}")
                context_parts.append(f"Тип: {current_plan['activity_type']}")
                context_parts.append(f"Осталось времени: {time_left:.1f} часов")
                context_parts.append(f"Важность: {current_plan['importance']}/10")
                
                if current_plan['emotional_reason']:
                    context_parts.append(f"Причина: {current_plan['emotional_reason']}")
                
                # Контекст поведения в зависимости от активности
                activity_behaviors = {
                    "cosplay": "ПОВЕДЕНИЕ: Увлечена работой над костюмом, но можем поговорить",
                    "work": "ПОВЕДЕНИЕ: На работе/учебе, отвечаю когда могу", 
                    "social": "ПОВЕДЕНИЕ: С друзьями, но рада пообщаться",
                    "rest": "ПОВЕДЕНИЕ: Отдыхаю, расслабленная",
                    "hobby": "ПОВЕДЕНИЕ: Занимаюсь любимым делом, в хорошем настроении"
                }
                
                behavior = activity_behaviors.get(current_plan['activity_type'], "ПОВЕДЕНИЕ: Занята, но могу пообщаться")
                context_parts.append(behavior)
                
            except Exception as e:
                self.logger.error(f"Ошибка формирования контекста текущей активности: {e}")
        else:
            context_parts.append("АКТИВНОСТЬ: Сейчас свободна")
        
        # Добавляем ближайшие планы
        if upcoming_plans:
            context_parts.append(f"\nБЛИЖАЙШИЕ ПЛАНЫ:")
            for plan in upcoming_plans[:3]:  # Первые 3
                try:
                    plan_start = datetime.fromisoformat(plan['start_time'])
                    time_str = plan_start.strftime('%H:%M')
                    importance_marker = "🔥" if plan['importance'] >= 8 else "📋"
                    context_parts.append(f"• {time_str} {importance_marker} {plan['description']}")
                except Exception as e:
                    self.logger.error(f"Ошибка форматирования плана: {e}")
                    continue
        
        return "\n".join(context_parts)
    
    def _get_activity_by_id(self, activity_id: int) -> Optional[VirtualActivity]:
        """Получает активность по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, activity_type, description, start_time, end_time, 
                           status, mood_effect, energy_cost
                    FROM virtual_activities 
                    WHERE id = ?
                """, (activity_id,))
                
                result = cursor.fetchone()
                if result:
                    return VirtualActivity(
                        id=result[0],
                        activity_type=result[1],
                        description=result[2],
                        start_time=datetime.fromisoformat(result[3]),
                        end_time=datetime.fromisoformat(result[4]),
                        status=result[5],
                        mood_effect=result[6],
                        energy_cost=result[7]
                    )
                    
        except Exception as e:
            self.logger.error(f"Ошибка получения активности: {e}")
        
        return None
    
    def schedule_activity(self, activity_type: str, description: str, 
                         start_time: datetime, duration_hours: float,
                         mood_effect: float = 0, energy_cost: int = 20) -> bool:
        """Планирует новую активность"""
        try:
            end_time = start_time + timedelta(hours=duration_hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO virtual_activities 
                    (character_id, activity_type, description, start_time, end_time,
                     mood_effect, energy_cost, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'planned')
                """, (
                    1, activity_type, description, 
                    start_time.isoformat(), end_time.isoformat(),
                    mood_effect, energy_cost
                ))
                
                conn.commit()
                
                self.logger.info(f"📅 Запланирована активность: {description} на {start_time.strftime('%d.%m %H:%M')}")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка планирования активности: {e}")
            return False
    
    def check_and_update_activities(self) -> Dict[str, Any]:
        """Проверяет и обновляет текущие активности"""
        now = datetime.now()
        changes = {
            "activity_started": None,
            "activity_ended": None,
            "status_changed": False
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем активности которые должны начаться
                cursor.execute("""
                    SELECT id, activity_type, description, start_time, end_time,
                           mood_effect, energy_cost
                    FROM virtual_activities
                    WHERE status = 'planned' 
                    AND start_time <= ?
                    ORDER BY start_time ASC
                    LIMIT 1
                """, (now.isoformat(),))
                
                starting_activity = cursor.fetchone()
                if starting_activity:
                    activity = VirtualActivity(
                        id=starting_activity[0],
                        activity_type=starting_activity[1],
                        description=starting_activity[2],
                        start_time=datetime.fromisoformat(starting_activity[3]),
                        end_time=datetime.fromisoformat(starting_activity[4]),
                        status="active",
                        mood_effect=starting_activity[5],
                        energy_cost=starting_activity[6]
                    )
                    
                    # Завершаем предыдущую активность если есть
                    if self.current_activity:
                        self._end_activity(self.current_activity.id)
                        changes["activity_ended"] = self.current_activity
                    
                    # Начинаем новую
                    self._start_activity(activity.id)
                    self.current_activity = activity
                    changes["activity_started"] = activity
                    changes["status_changed"] = True
                
                # Проверяем активность которая должна закончиться
                elif self.current_activity and now >= self.current_activity.end_time:
                    self._end_activity(self.current_activity.id)
                    changes["activity_ended"] = self.current_activity
                    self.current_activity = None
                    self.availability = "free"
                    changes["status_changed"] = True
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления активностей: {e}")
        
        return changes
    
    def _start_activity(self, activity_id: int):
        """Начинает активность"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Обновляем статус активности
                cursor.execute("""
                    UPDATE virtual_activities 
                    SET status = 'active'
                    WHERE id = ?
                """, (activity_id,))
                
                # Обновляем состояние персонажа
                cursor.execute("""
                    INSERT INTO character_states
                    (character_id, current_activity_id, availability, last_updated)
                    VALUES (?, ?, 'busy', ?)
                """, (1, activity_id, datetime.now().isoformat()))
                
                self.availability = "busy"
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Ошибка начала активности: {e}")
    
    def _end_activity(self, activity_id: int):
        """Заканчивает активность"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE virtual_activities 
                    SET status = 'completed'
                    WHERE id = ?
                """, (activity_id,))
                
                conn.commit()

        except Exception as e:
            self.logger.error(f"Ошибка завершения активности: {e}")

    async def _notify_activity_end(self, activity: VirtualActivity):
        """Отправляет уведомление о завершении активности"""
        messages = [
            f"Я закончила {activity.description}.",
            "Теперь я свободна пообщаться!",
        ]

        # Для простоты пока выводим уведомление в лог
        for msg in messages:
            self.logger.info(msg)
    
    def get_current_context_for_ai(self) -> str:
        """Возвращает контекст текущей активности для AI"""
        context_parts = []
        
        context_parts.append(f"ТЕКУЩЕЕ МЕСТОПОЛОЖЕНИЕ: {self.location}")
        context_parts.append(f"ДОСТУПНОСТЬ: {self.availability}")
        
        if self.current_activity:
            activity = self.current_activity
            time_left = (activity.end_time - datetime.now()).total_seconds() / 3600
            
            context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {activity.description}")
            context_parts.append(f"Тип: {activity.activity_type}")
            context_parts.append(f"Осталось времени: {time_left:.1f} часов")
            
            # Контекст поведения в зависимости от активности
            if activity.activity_type == "cosplay":
                context_parts.append("ПОВЕДЕНИЕ: Увлечена работой над костюмом, может делиться процессом")
            elif activity.activity_type == "work":
                context_parts.append("ПОВЕДЕНИЕ: На работе/учебе, отвечает реже но с радостью")
            elif activity.activity_type == "rest":
                context_parts.append("ПОВЕДЕНИЕ: Отдыхает, расслабленная, время для долгих разговоров")
            elif activity.activity_type == "social":
                context_parts.append("ПОВЕДЕНИЕ: С друзьями/на мероприятии, может рассказывать что происходит")
        else:
            context_parts.append("АКТИВНОСТЬ: Свободна, дома, доступна для общения")
        
        return "\n".join(context_parts)
    
    def get_upcoming_activities(self, hours: int = 24) -> List[VirtualActivity]:
        """Получает предстоящие активности"""
        try:
            end_time = datetime.now() + timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, activity_type, description, start_time, end_time,
                           status, mood_effect, energy_cost
                    FROM virtual_activities
                    WHERE status = 'planned'
                    AND start_time <= ?
                    ORDER BY start_time ASC
                """, (end_time.isoformat(),))
                
                activities = []
                for row in cursor.fetchall():
                    activities.append(VirtualActivity(
                        id=row[0],
                        activity_type=row[1],
                        description=row[2],
                        start_time=datetime.fromisoformat(row[3]),
                        end_time=datetime.fromisoformat(row[4]),
                        status=row[5],
                        mood_effect=row[6],
                        energy_cost=row[7]
                    ))
                
                return activities
                
        except Exception as e:
            self.logger.error(f"Ошибка получения планов: {e}")
            return []
