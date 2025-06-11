import asyncio
import json
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .ai_activity_humanizer import AIActivityHumanizer

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
    
    def __init__(self, db_path: str, character_loader=None, api_manager=None, config=None):
        self.db_path = db_path
        self.character_loader = character_loader
        self.logger = logging.getLogger(__name__)
        
        # AI-гуманизатор активностей
        if api_manager and character_loader and config:
            try:
                from .ai_activity_humanizer import AIActivityHumanizer
                self.activity_humanizer = AIActivityHumanizer(api_manager, character_loader, config)
                self.logger.info("🎭 AI-гуманизатор активностей инициализирован")
            except ImportError as e:
                self.logger.error(f"Ошибка импорта AI-гуманизатора: {e}")
                self.activity_humanizer = None
        else:
            self.activity_humanizer = None
            self.logger.warning("⚠️ AI-гуманизатор не инициализирован")
        
        # Трекинг текущей активности
        self.current_activity: Optional[VirtualActivity] = None
        self.last_activity_check: Optional[datetime] = None
        self.location = "дома"
        self.availability = "free"
        
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
        """Получает ИИ-планы на сегодня с проверкой статуса"""
        try:
            from datetime import date
            today = date.today()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, activity_type, description, start_time, end_time,
                        COALESCE(importance, 5) as importance, 
                        COALESCE(flexibility, 5) as flexibility,
                        COALESCE(emotional_reason, '') as emotional_reason,
                        COALESCE(status, 'planned') as status
                    FROM virtual_activities
                    WHERE DATE(start_time) = ? 
                    AND generated_by_ai = 1
                    ORDER BY start_time ASC
                """, (today.isoformat(),))
                
                plans = []
                for row in cursor.fetchall():
                    try:
                        # Проверяем формат времени
                        start_time = row[3]
                        end_time = row[4]
                        
                        # Валидация времени
                        datetime.fromisoformat(start_time)
                        datetime.fromisoformat(end_time)
                        
                        plans.append({
                            'id': row[0],
                            'activity_type': row[1],
                            'description': row[2],
                            'start_time': start_time,
                            'end_time': end_time,
                            'importance': row[5],
                            'flexibility': row[6],
                            'emotional_reason': row[7],
                            'status': row[8]  # НОВОЕ: статус активности
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки плана {row}: {e}")
                        continue
                
                return plans
                
        except Exception as e:
            self.logger.error(f"Ошибка получения ИИ-планов: {e}")
            return []
        
    def check_and_update_activities(self) -> Dict[str, Any]:
        """🔧 ИСПРАВЛЕННАЯ проверка и обновление активностей"""
        
        now = datetime.now()
        changes = {
            "activity_started": None,
            "activity_ended": None, 
            "status_changed": False
        }
        
        # Предотвращаем частые проверки
        if (self.last_activity_check and 
            (now - self.last_activity_check).total_seconds() < 30):
            return changes
        
        self.last_activity_check = now
        
        try:
            # 1. Проверяем текущую активность - должна ли она закончиться?
            if self.current_activity and now >= self.current_activity.end_time:
                self.logger.info(f"⏰ Активность должна закончиться: {self.current_activity.description}")
                changes["activity_ended"] = self.current_activity
                self._end_activity(self.current_activity.id)
                self.current_activity = None
                self.availability = "free"
                changes["status_changed"] = True
                
                # ВАЖНО: Выходим здесь, чтобы не начинать новую активность сразу
                return changes
            
            # 2. Если сейчас свободна - ищем новую активность
            if not self.current_activity:
                ai_plans = self._get_today_ai_plans()
                
                for plan in ai_plans:
                    try:
                        plan_start = datetime.fromisoformat(plan['start_time'])
                        plan_end = datetime.fromisoformat(plan['end_time'])
                        
                        # Проверяем что активность должна начаться СЕЙЧАС
                        if (plan_start <= now < plan_end and 
                            plan.get('status', 'planned') == 'planned'):
                            
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
                            
                            # Обновляем статус в БД
                            self._start_activity(activity.id)
                            
                            self.logger.info(f"🎭 Начата активность: {activity.description} ({plan_start} - {plan_end})")
                            
                            # ВАЖНО: Начинаем только ОДНУ активность за раз
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки плана {plan}: {e}")
                        continue
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления виртуальной жизни: {e}")
            return changes
        
    def get_current_context_for_ai(self) -> str:
        """Возвращает контекст текущей активности для AI (УЛУЧШЕННАЯ ВЕРСИЯ)"""
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
        
        # Обрабатываем текущую активность
        if current_plan:
            try:
                time_left = (datetime.fromisoformat(current_plan['end_time']) - current_time).total_seconds() / 3600
                
                # НОВОЕ: Пытаемся гуманизировать через AI
                if self.activity_humanizer:
                    try:
                        # Создаем задачу для асинхронного вызова
                        import asyncio
                        
                        # Проверяем есть ли текущий event loop
                        try:
                            loop = asyncio.get_running_loop()
                            # Если loop уже работает, создаем task
                            humanized_description = asyncio.create_task(
                                self.activity_humanizer.humanize_activity(
                                    activity_type=current_plan['activity_type'],
                                    start_time=current_plan['start_time'].split(' ')[1][:5] if ' ' in current_plan['start_time'] else current_plan['start_time'][:5],
                                    importance=current_plan.get('importance', 5),
                                    emotional_reason=current_plan.get('emotional_reason', '')
                                )
                            )
                            # НО! Мы в синхронном методе, поэтому используем fallback
                            activity_description = self._get_humanized_fallback(current_plan)
                            
                        except RuntimeError:
                            # Нет event loop - используем fallback
                            activity_description = self._get_humanized_fallback(current_plan)
                    
                    except Exception as e:
                        self.logger.error(f"Ошибка AI гуманизации: {e}")
                        activity_description = self._get_humanized_fallback(current_plan)
                else:
                    # Нет AI гуманизатора - используем fallback
                    activity_description = self._get_humanized_fallback(current_plan)
                
                context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {activity_description}")
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
                # Fallback на оригинальное описание
                context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {current_plan.get('description', 'занимаюсь делами')}")
        else:
            context_parts.append("АКТИВНОСТЬ: Сейчас свободна")
        
        # Обрабатываем ближайшие планы
        if upcoming_plans:
            context_parts.append(f"\nМОИ БЛИЖАЙШИЕ ПЛАНЫ:")
            for plan in upcoming_plans[:5]:
                try:
                    plan_start = datetime.fromisoformat(plan['start_time'])
                    time_str = plan_start.strftime('%H:%M')
                    importance_marker = "🔥" if plan['importance'] >= 8 else "📋"
                    
                    # Пытаемся гуманизировать описание плана
                    plan_description = self._get_humanized_fallback(plan)
                    
                    context_parts.append(f"• {time_str} {importance_marker} {plan_description}")
                    
                except Exception as e:
                    self.logger.error(f"Ошибка форматирования плана: {e}")
                    continue
            
            context_parts.append("\nИНСТРУКЦИЯ: ЗНАЙ СВОИ ПЛАНЫ! Упоминай их при вопросах о планах!")
            context_parts.append("При вопросах о планах называй конкретное время и активность!")
        else:
            context_parts.append(f"\nПЛАНОВ НА СЕГОДНЯ: нет или уже выполнены")
        
        return "\n".join(context_parts)
    
    def _get_humanized_fallback(self, plan: Dict[str, Any]) -> str:
        """Fallback гуманизация когда AI недоступен"""
        
        activity_type = plan.get('activity_type', 'unknown')
        character = self.character_loader.get_current_character() if self.character_loader else None
        
        # Базовые человечные описания
        basic_humanizations = {
            "hobby": "занимаюсь любимым делом",
            "work": "работаю/учусь",
            "rest": "отдыхаю дома",
            "social": "общаюсь с друзьями",
            "cosplay": "работаю над костюмом",
            "sleep": "готовлюсь ко сну",
            "eat": "кушаю",
            "study": "учусь",
            "gaming": "играю в игры",
            "reading": "читаю",
            "shopping": "хожу по магазинам",
            "exercise": "занимаюсь спортом"
        }
        
        # Специальные описания для Марин
        if character and 'марин' in character.get('name', '').lower():
            marin_humanizations = {
                "hobby": "работаю над новым косплеем",
                "rest": "лежу и смотрю аниме",
                "social": "болтаю с подругами о косплее",
                "cosplay": "шью детали для костюма",
                "work": "сижу на парах, думаю о косплее",
                "study": "учусь, но мысли об аниме"
            }
            basic_humanizations.update(marin_humanizations)
        
        # Используем оригинальное описание как fallback fallback'а
        humanized = basic_humanizations.get(activity_type, plan.get('description', f'занимаюсь делами ({activity_type})'))
        
        return humanized
    
    async def get_current_context_for_ai_async(self) -> str:
        """Асинхронная версия с полноценной AI-гуманизацией"""
        
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
        
        # Гуманизируем текущую активность через AI
        if current_plan:
            try:
                time_left = (datetime.fromisoformat(current_plan['end_time']) - current_time).total_seconds() / 3600
                
                if self.activity_humanizer:
                    try:
                        humanized_activity = await self.activity_humanizer.humanize_activity(
                            activity_type=current_plan['activity_type'],
                            start_time=current_plan['start_time'].split(' ')[1][:5] if ' ' in current_plan['start_time'] else current_plan['start_time'][:5],
                            importance=current_plan.get('importance', 5),
                            emotional_reason=current_plan.get('emotional_reason', '')
                        )
                        
                        context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {humanized_activity}")
                        self.logger.info(f"🎭 AI гуманизировал: {current_plan['activity_type']} -> {humanized_activity}")
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка AI гуманизации: {e}")
                        humanized_activity = self._get_humanized_fallback(current_plan)
                        context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {humanized_activity}")
                else:
                    humanized_activity = self._get_humanized_fallback(current_plan)
                    context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {humanized_activity}")
                
                context_parts.append(f"Осталось времени: {time_left:.1f} часов")
                context_parts.append(f"Важность: {current_plan['importance']}/10")
                
            except Exception as e:
                self.logger.error(f"Ошибка формирования контекста текущей активности: {e}")
        else:
            context_parts.append("АКТИВНОСТЬ: Сейчас свободна")
        
        # Гуманизируем ближайшие планы
        if upcoming_plans and self.activity_humanizer:
            context_parts.append(f"\nМОИ БЛИЖАЙШИЕ ПЛАНЫ:")
            
            for plan in upcoming_plans[:3]:  # Ограничиваем чтобы не тратить много токенов
                try:
                    plan_start = datetime.fromisoformat(plan['start_time'])
                    time_str = plan_start.strftime('%H:%M')
                    importance_marker = "🔥" if plan.get('importance', 5) >= 8 else "📋"
                    
                    # AI гуманизация
                    try:
                        humanized_plan = await self.activity_humanizer.humanize_activity(
                            activity_type=plan['activity_type'],
                            start_time=time_str,
                            importance=plan.get('importance', 5)
                        )
                        context_parts.append(f"• {time_str} {importance_marker} {humanized_plan}")
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка AI гуманизации плана: {e}")
                        fallback_desc = self._get_humanized_fallback(plan)
                        context_parts.append(f"• {time_str} {importance_marker} {fallback_desc}")
                    
                except Exception as e:
                    self.logger.error(f"Ошибка форматирования плана: {e}")
                    continue
        elif upcoming_plans:
            # Нет AI гуманизатора, используем fallback
            context_parts.append(f"\nМОИ БЛИЖАЙШИЕ ПЛАНЫ:")
            for plan in upcoming_plans[:5]:
                try:
                    plan_start = datetime.fromisoformat(plan['start_time'])
                    time_str = plan_start.strftime('%H:%M')
                    importance_marker = "🔥" if plan.get('importance', 5) >= 8 else "📋"
                    fallback_desc = self._get_humanized_fallback(plan)
                    context_parts.append(f"• {time_str} {importance_marker} {fallback_desc}")
                except Exception:
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
        """Начинает активность и обновляет статус в БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Обновляем статус активности
                cursor.execute("""
                    UPDATE virtual_activities 
                    SET status = 'active'
                    WHERE id = ?
                """, (activity_id,))
                
                conn.commit()
                self.logger.info(f"✅ Активность {activity_id} помечена как активная в БД")
                
        except Exception as e:
            self.logger.error(f"Ошибка начала активности в БД: {e}")
    
    def _end_activity(self, activity_id: int):
        """Заканчивает активность и обновляет статус в БД"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE virtual_activities 
                    SET status = 'completed'
                    WHERE id = ?
                """, (activity_id,))
                
                conn.commit()
                self.logger.info(f"✅ Активность {activity_id} помечена как завершённая в БД")

        except Exception as e:
            self.logger.error(f"Ошибка завершения активности в БД: {e}")

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
        
        # Получаем ИИ-планы
        ai_plans = self._get_today_ai_plans()
        current_time = datetime.now()
        
        # Ищем ТОЛЬКО активные и будущие планы
        current_plan = None
        upcoming_plans = []
        
        for plan in ai_plans:
            try:
                plan_start = datetime.fromisoformat(plan['start_time'])
                plan_end = datetime.fromisoformat(plan['end_time'])
                
                # Только если активность СЕЙЧАС происходит
                if (plan_start <= current_time < plan_end and 
                    plan.get('status') == 'active'):
                    current_plan = plan
                # Или будет происходить в будущем
                elif (plan_start > current_time and 
                      plan.get('status') in ['planned', None]):
                    upcoming_plans.append(plan)
                    
            except Exception as e:
                self.logger.error(f"Ошибка обработки времени плана: {e}")
                continue
        
        # Обрабатываем текущую активность
        if current_plan:
            try:
                time_left = (datetime.fromisoformat(current_plan['end_time']) - current_time).total_seconds() / 3600
                
                context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {current_plan['description']}")
                context_parts.append(f"Тип: {current_plan['activity_type']}")
                context_parts.append(f"Осталось времени: {time_left:.1f} часов")
                context_parts.append(f"Важность: {current_plan['importance']}/10")
                
                if current_plan['emotional_reason']:
                    context_parts.append(f"Причина: {current_plan['emotional_reason']}")
                
                # Контекст поведения
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
        
        # Ближайшие планы (только первые 3)
        if upcoming_plans:
            context_parts.append(f"\nМОИ БЛИЖАЙШИЕ ПЛАНЫ:")
            for plan in upcoming_plans[:3]:
                try:
                    plan_start = datetime.fromisoformat(plan['start_time'])
                    time_str = plan_start.strftime('%H:%M')
                    importance_marker = "🔥" if plan['importance'] >= 8 else "📋"
                    
                    context_parts.append(f"• {time_str} {importance_marker} {plan['description']}")
                    
                except Exception as e:
                    self.logger.error(f"Ошибка форматирования плана: {e}")
                    continue
            
            context_parts.append("\nИНСТРУКЦИЯ: При вопросах о планах называй конкретное время и активность!")
        else:
            context_parts.append(f"\nПЛАНОВ НА СЕГОДНЯ: нет или уже выполнены")
        
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
