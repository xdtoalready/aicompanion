"""
Система ИИ-планирования для автоматического создания планов дня
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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
    """Система ежедневного ИИ-планирования"""
    
    def __init__(self, db_path: str, api_manager, character_loader, config: Dict[str, Any]):
        self.db_path = db_path
        self.api_manager = api_manager
        self.character_loader = character_loader
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Кэш последнего планирования (чтобы не планировать дважды в день)
        self.last_planning_date = None
    
    async def should_plan_today(self) -> bool:
        """Проверяет нужно ли планировать сегодня"""
        
        today = date.today()
        
        # Уже планировали сегодня?
        if self.last_planning_date == today:
            return False
        
        # Проверяем в БД есть ли планы на сегодня
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM virtual_activities 
                    WHERE planning_date = ? AND generated_by_ai = 1
                """, (today.isoformat(),))
                
                existing_plans = cursor.fetchone()[0]
                
                # Если есть больше 3 планов, считаем что уже запланировали
                if existing_plans >= 3:
                    self.logger.info(f"На {today} уже есть {existing_plans} ИИ-планов")
                    self.last_planning_date = today
                    return False
                
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки планов: {e}")
            return True  # В случае ошибки пытаемся планировать
    
    async def generate_daily_plan(self) -> bool:
        """Генерирует план на день"""
        
        today = date.today()
        
        if not await self.should_plan_today():
            return False
        
        self.logger.info(f"🧠📅 Генерирую план на {today}")
        
        try:
            # Получаем контекст для планирования
            planning_context = await self._build_planning_context()
            
            # Создаём промпт
            planning_prompt = self._build_planning_prompt(planning_context)
            
            # Делаем запрос к ИИ через PLANNING API
            from .multi_api_manager import APIUsageType
            
            response = await self.api_manager.make_request(
                APIUsageType.PLANNING,
                model=self.config.get('ai', {}).get('model', 'deepseek/deepseek-chat'),
                messages=[
                    {"role": "system", "content": planning_prompt},
                    {"role": "user", "content": f"Запланируй день для {today.strftime('%A, %d.%m.%Y')}"}
                ],
                max_tokens=800,
                temperature=0.7  # Немного творчества в планах
            )
            
            if not response or not response.choices:
                self.logger.error("Пустой ответ от ИИ планировщика")
                return False
            
            ai_response = response.choices[0].message.content.strip()
            
            # Парсим ответ и сохраняем планы
            success = await self._parse_and_save_plans(ai_response, planning_context)
            
            if success:
                self.last_planning_date = today
                self.logger.info("✅ План дня успешно сгенерирован")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации плана дня: {e}")
            return False
    
    async def _build_planning_context(self) -> Dict[str, Any]:
        """Собирает контекст для планирования"""
        
        today = date.today()
        weekday = today.weekday()  # 0=понедельник
        is_weekend = weekday >= 5
        
        weekday_names = [
            "понедельник", "вторник", "среда", "четверг", 
            "пятница", "суббота", "воскресенье"
        ]
        weekday_name = weekday_names[weekday]
        
        # Получаем информацию о персонаже
        character = self.character_loader.get_current_character()
        character_context = self.character_loader.get_character_context_for_ai() if character else ""
        
        # Получаем предыдущие планы (для анализа паттернов)
        previous_plans = await self._get_recent_plans(days=7)
        
        # Получаем незавершённые желания
        pending_desires = await self._get_pending_desires()
        
        # Симулируем настроение (в будущем будет из psychological_core)
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
        """Создаёт промпт для планирования"""
        
        character_name = context['character_name']
        weekday = context['weekday']
        is_weekend = context['is_weekend']
        current_mood = context['current_mood']
        character_context = context['character_context']
        
        base_prompt = f"""Ты — {character_name}, планируешь свой день.

КОНТЕКСТ:
• День: {weekday} ({'выходной' if is_weekend else 'рабочий день'})
• Настроение: {current_mood}
• Персонаж: {character_context[:200]}...

ПРАВИЛА ПЛАНИРОВАНИЯ:
1. 🕐 Планируй с 8:00 до 22:00 (4-7 активностей)
2. 📋 Каждая активность: тип, описание, время, длительность
3. ⚖️  Важность (1-10) и гибкость (1-10) для каждой активности
4. 💭 Эмоциональная причина ("хочу отдохнуть", "нужно поработать")
5. 🎭 ОБЯЗАТЕЛЬНО учитывай характер персонажа!

ТИПЫ АКТИВНОСТЕЙ:"""
        
        # Персонаж-специфичные активности
        character = self.character_loader.get_current_character()
        if character and 'марин' in character.get('name', '').lower():
            base_prompt += """
• cosplay - работа над костюмами
• anime - просмотр аниме
• social - встречи с друзьями
• shopping - покупки косметики/аксессуаров
• photoshoot - фотосессии в костюмах"""
        else:
            base_prompt += """
• work - работа/учёба  
• hobby - личные увлечения
• social - общение с людьми
• rest - отдых дома
• exercise - физическая активность"""
        
        base_prompt += """

ФОРМАТ ОТВЕТА (обязательно JSON):
```json
{
  "day_mood": "описание общего настроя дня",
  "activities": [
    {
      "activity_type": "work",
      "description": "работаю над проектом",
      "start_hour": 9,
      "start_minute": 0,
      "duration_hours": 3.5,
      "importance": 8,
      "flexibility": 3,
      "emotional_reason": "нужно закончить до дедлайна",
      "can_reschedule": false,
      "weather_dependent": false
    }
  ]
}
```

ВАЖНО:
• Если выходной - НЕ планируй работу, планируй отдых/хобби
• Учитывай характер: активный персонаж = больше активностей
• Гибкость 10 = легко перенести, 1 = нельзя менять
• Важность 10 = критично, 1 = можно пропустить"""
        
        # Добавляем контекст предыдущих планов
        if context['previous_plans']:
            base_prompt += f"""

ПРЕДЫДУЩИЕ ПЛАНЫ (для разнообразия):
{context['previous_plans'][:300]}..."""
        
        # Добавляем незавершённые желания
        if context['pending_desires']:
            base_prompt += f"""

НЕЗАВЕРШЁННЫЕ ЖЕЛАНИЯ (попробуй включить):
{context['pending_desires'][:200]}..."""
        
        return base_prompt
    
    async def _parse_and_save_plans(self, ai_response: str, context: Dict[str, Any]) -> bool:
        """Парсит ответ ИИ и сохраняет планы в БД"""
        
        try:
            # Извлекаем JSON из ответа
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                self.logger.error("JSON не найден в ответе ИИ")
                return False
            
            json_str = ai_response[json_start:json_end]
            plan_data = json.loads(json_str)
            
            activities = plan_data.get('activities', [])
            day_mood = plan_data.get('day_mood', 'обычный день')
            
            if not activities:
                self.logger.error("Нет активностей в плане")
                return False
            
            # Сохраняем в БД
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
                    self._build_planning_prompt(context)[:1000],  # Ограничиваем размер
                    ai_response[:2000],  # Ограничиваем размер
                    True
                ))
                
                # Сохраняем каждую активность
                saved_count = 0
                for activity in activities:
                    try:
                        start_time = datetime.combine(
                            today,
                            datetime.min.time().replace(
                                hour=activity.get('start_hour', 9),
                                minute=activity.get('start_minute', 0)
                            )
                        )
                        
                        end_time = start_time + timedelta(hours=activity.get('duration_hours', 1.0))
                        
                        cursor.execute("""
                            INSERT INTO virtual_activities
                            (character_id, activity_type, description, start_time, end_time,
                             status, planned_by, flexibility, importance, emotional_reason,
                             can_reschedule, weather_dependent, planning_date, generated_by_ai)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            activity.get('weather_dependent', False),
                            today.isoformat(),
                            True
                        ))
                        
                        saved_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"Ошибка сохранения активности: {e}")
                        continue
                
                conn.commit()
                
                self.logger.info(f"📅 Сохранено {saved_count}/{len(activities)} активностей на {today}")
                return saved_count > 0
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON плана: {e}")
            self.logger.debug(f"Ответ ИИ: {ai_response}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка сохранения плана: {e}")
            return False
    
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
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT desire_text, priority, category
                    FROM future_desires
                    WHERE fulfilled = 0
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 3
                """, )
                
                desires = cursor.fetchall()
                
                if not desires:
                    return "Нет незавершённых желаний"
                
                summary = []
                for desire, priority, category in desires:
                    summary.append(f"{desire} (приоритет: {priority})")
                
                return "; ".join(summary)
                
        except Exception as e:
            self.logger.error(f"Ошибка получения желаний: {e}")
            return "Ошибка загрузки желаний"