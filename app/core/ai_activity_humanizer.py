# AI-система для гуманизации технических активностей

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from .prompt_manager import get_prompt_manager

class AIActivityHumanizer:
    """Превращает технические активности в живые описания через AI"""
    
    def __init__(self, api_manager, character_loader, config: Dict[str, Any]):
        self.api_manager = api_manager
        self.character_loader = character_loader
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Prompt Manager
        self.prompt_manager = get_prompt_manager()

        # Кэш для похожих запросов (экономим токены)
        self.humanization_cache = {}
        self.cache_ttl = 3600  # 1 час
    
    async def humanize_activity(self, 
                              activity_type: str, 
                              start_time: str = None,
                              duration: float = 1.0,
                              importance: int = 5,
                              emotional_reason: str = "",
                              current_mood: str = "нормальное") -> str:
        """Превращает техническую активность в живое описание"""
        
        # Проверяем кэш
        cache_key = f"{activity_type}_{start_time}_{current_mood}_{importance}"
        if cache_key in self.humanization_cache:
            cached_result, timestamp = self.humanization_cache[cache_key]
            if (datetime.now().timestamp() - timestamp) < self.cache_ttl:
                self.logger.debug(f"💾 Взяли из кэша: {activity_type} -> {cached_result}")
                return cached_result
        
        try:
            # Получаем контекст персонажа
            character = self.character_loader.get_current_character()
            character_context = self._build_character_context(character)
            
            # Строим промпт для гуманизации
            humanization_prompt = self._build_humanization_prompt(
                activity_type, start_time, duration, importance, 
                emotional_reason, current_mood, character_context
            )
            
            # Запрос к AI (используем analytics API для экономии dialogue лимитов)
            from .gemini_api_manager import APIUsageType
            
            response = await self.api_manager.make_request(
                APIUsageType.ANALYTICS,
                model=self.config.get('ai', {}).get('model', 'deepseek/deepseek-chat'),
                messages=[
                    {"role": "system", "content": humanization_prompt},
                    {"role": "user", "content": f"Гуманизируй активность: {activity_type}"}
                ],
                max_tokens=150,
                temperature=0.8  # Больше креативности
            )
            
            if not response or not response.choices:
                self.logger.error("Пустой ответ от AI гуманизатора")
                return self._get_fallback_description(activity_type, character)
            
            humanized = response.choices[0].message.content.strip()
            
            # Очищаем от лишнего
            humanized = self._clean_ai_response(humanized)
            
            # Кэшируем результат
            self.humanization_cache[cache_key] = (humanized, datetime.now().timestamp())
            
            self.logger.info(f"🎭 AI гуманизация: {activity_type} -> {humanized}")
            return humanized
            
        except Exception as e:
            self.logger.error(f"Ошибка AI гуманизации: {e}")
            return self._get_fallback_description(activity_type, character)
    
    def _build_character_context(self, character: Dict[str, Any]) -> str:
        """Строит контекст персонажа для гуманизации"""
        
        if not character:
            return "дружелюбная девушка"
        
        name = character.get('name', 'AI')
        age = character.get('age', 25)
        
        # Основные черты
        key_traits = character.get('personality', {}).get('key_traits', [])
        traits_text = ", ".join(key_traits[:3]) if key_traits else "дружелюбная"
        
        # Интересы
        interests = character.get('interests', [])
        interests_text = ", ".join(interests[:4]) if interests else "общение"
        
        # Стиль речи
        speech_style = character.get('speech', {}).get('style', 'эмоциональный')
        
        context = f"""ПЕРСОНАЖ: {name} ({age} лет)
ХАРАКТЕР: {traits_text}
ИНТЕРЕСЫ: {interests_text}
СТИЛЬ РЕЧИ: {speech_style}"""

        # Специфика для Марин
        if 'марин' in name.lower() or 'китагава' in name.lower():
            context += "\nСПЕЦИАЛЬНОСТЬ: косплей, аниме, создание костюмов"
        
        return context
    
    def _build_humanization_prompt(self, activity_type: str, start_time: str,
                                 duration: float, importance: int,
                                 emotional_reason: str, current_mood: str,
                                 character_context: str) -> str:
        """Строит промпт для гуманизации активности (из темплейта)"""

        current_hour = datetime.now().hour

        template_context = {
            'character_context': character_context,
            'current_hour': current_hour,
            'start_time': start_time,
            'duration': duration,
            'importance': importance,
            'current_mood': current_mood,
            'emotional_reason': emotional_reason
        }

        return self.prompt_manager.render('humanize_activity.jinja2', template_context)
    
    def _clean_ai_response(self, response: str) -> str:
        """Очищает ответ AI от лишнего"""
        
        # Убираем кавычки
        response = response.strip('"\'`')
        
        # Убираем объяснения AI
        if ":" in response:
            response = response.split(":", 1)[-1].strip()
        
        # Убираем префиксы типа "Я сейчас"
        prefixes_to_remove = [
            "я сейчас ", "сейчас я ", "в данный момент ", 
            "в настоящее время ", "на данный момент "
        ]
        
        response_lower = response.lower()
        for prefix in prefixes_to_remove:
            if response_lower.startswith(prefix):
                response = response[len(prefix):]
                break
        
        # Ограничиваем длину
        if len(response) > 50:
            response = response[:47] + "..."
        
        return response.strip()
    
    def _get_fallback_description(self, activity_type: str, character: Dict[str, Any]) -> str:
        """Fallback описания если AI не сработал"""
        
        fallbacks = {
            "hobby": "занимаюсь любимым делом",
            "work": "работаю",
            "rest": "отдыхаю дома", 
            "social": "общаюсь с друзьями",
            "cosplay": "работаю над костюмом",
            "sleep": "готовлюсь ко сну",
            "eat": "кушаю",
            "study": "учусь"
        }
        
        # Специальные fallback для Марин
        if character and 'марин' in character.get('name', '').lower():
            marin_fallbacks = {
                "hobby": "работаю над новым косплеем",
                "rest": "лежу и смотрю аниме",
                "social": "болтаю с подругами о косплее"
            }
            fallbacks.update(marin_fallbacks)
        
        return fallbacks.get(activity_type, f"занимаюсь делами ({activity_type})")
    
    async def humanize_multiple_activities(self, activities: List[Dict[str, Any]]) -> List[str]:
        """Гуманизирует сразу несколько активностей"""
        
        results = []
        
        # Batch обработка для экономии API запросов
        for activity in activities:
            humanized = await self.humanize_activity(
                activity_type=activity.get('activity_type', 'unknown'),
                start_time=activity.get('start_time', ''),
                duration=activity.get('duration_hours', 1.0),
                importance=activity.get('importance', 5),
                emotional_reason=activity.get('emotional_reason', ''),
                current_mood=activity.get('mood_context', 'нормальное')
            )
            
            results.append(humanized)
            
            # Небольшая пауза между запросами
            await asyncio.sleep(0.1)
        
        return results
    
    def clear_cache(self):
        """Очищает кэш гуманизации"""
        self.humanization_cache.clear()
        self.logger.info("🗑️ Кэш AI гуманизатора очищен")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Статистика кэша"""
        
        # Убираем устаревшие записи
        current_time = datetime.now().timestamp()
        expired_keys = []
        
        for key, (_, timestamp) in self.humanization_cache.items():
            if (current_time - timestamp) > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.humanization_cache[key]
        
        return {
            "cached_humanizations": len(self.humanization_cache),
            "cache_hit_rate": "неизвестно",  # можно добавить трекинг
            "expired_cleaned": len(expired_keys)
        }

# Интеграция в виртуальную жизнь
class EnhancedVirtualLifeManager:
    """Расширенный менеджер виртуальной жизни с AI-гуманизацией"""
    
    def __init__(self, db_path: str, character_loader, api_manager, config):
        # ... существующая инициализация ...
        self.activity_humanizer = AIActivityHumanizer(api_manager, character_loader, config)
    
    async def get_current_context_for_ai_enhanced(self) -> str:
        """Улучшенный контекст с гуманизированными активностями"""
        
        context_parts = []
        
        # Получаем сегодняшние планы
        ai_plans = self._get_today_ai_plans()
        current_time = datetime.now()
        
        # Ищем текущую активность
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
            except Exception:
                continue
        
        # Гуманизируем текущую активность
        if current_plan:
            try:
                humanized_activity = await self.activity_humanizer.humanize_activity(
                    activity_type=current_plan['activity_type'],
                    start_time=current_plan['start_time'].split(' ')[1][:5],  # HH:MM
                    importance=current_plan.get('importance', 5),
                    emotional_reason=current_plan.get('emotional_reason', '')
                )
                
                time_left = (datetime.fromisoformat(current_plan['end_time']) - current_time).total_seconds() / 3600
                
                context_parts.append(f"ТЕКУЩАЯ АКТИВНОСТЬ: {humanized_activity}")
                context_parts.append(f"Осталось времени: {time_left:.1f} часов")
                
            except Exception as e:
                self.logger.error(f"Ошибка гуманизации текущей активности: {e}")
                context_parts.append(f"АКТИВНОСТЬ: {current_plan['description']}")
        else:
            context_parts.append("АКТИВНОСТЬ: Сейчас свободна")
        
        # Гуманизируем ближайшие планы
        if upcoming_plans:
            context_parts.append(f"\nМОИ БЛИЖАЙШИЕ ПЛАНЫ:")
            
            for plan in upcoming_plans[:3]:
                try:
                    plan_start = datetime.fromisoformat(plan['start_time'])
                    time_str = plan_start.strftime('%H:%M')
                    
                    # Гуманизируем описание
                    humanized = await self.activity_humanizer.humanize_activity(
                        activity_type=plan['activity_type'],
                        start_time=time_str,
                        importance=plan.get('importance', 5)
                    )
                    
                    importance_marker = "🔥" if plan.get('importance', 5) >= 8 else "📋"
                    context_parts.append(f"• {time_str} {importance_marker} {humanized}")
                    
                except Exception as e:
                    # Fallback на оригинальное описание
                    self.logger.error(f"Ошибка гуманизации плана: {e}")
                    context_parts.append(f"• {plan.get('description', 'запланированное дело')}")
        
        return "\n".join(context_parts)