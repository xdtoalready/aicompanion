# Основной модуль AI-компаньона с многосообщенческими ответами

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

# Добавляем корневой путь в sys.path ОДИН РАЗ
sys.path.append(str(Path(__file__).parent.parent.parent))

# Относительные импорты для модулей внутри core
from .psychology import PsychologicalCore
from .memory import AdvancedMemorySystem
from .ai_client import OptimizedAI
from .typing_simulator import TypingSimulator, TypingIndicator

# Абсолютный импорт для database (так как sys.path добавлен)
from app.database.memory_manager import EnhancedMemorySystem

class RealisticAICompanion:
    """Реалистичный AI-компаньон с многосообщенческими ответами"""
    
def __init__(self, config: Dict[str, Any]):
    self.config = config
    
    # Инициализация компонентов
    self.psychological_core = PsychologicalCore()
    
    # НОВОЕ: Используем базу данных для памяти
    db_path = config.get('database', {}).get('path', 'data/companion.db')
    self.enhanced_memory = EnhancedMemorySystem(db_path)
    
    # Оставляем старую систему для совместимости
    self.memory_system = AdvancedMemorySystem()
    
    # AI клиент
    self.ai_client = AsyncOpenAI(
        api_key=config['ai']['openrouter_api_key'],
        base_url="https://openrouter.ai/api/v1"
    )
    
    self.optimized_ai = OptimizedAI(self.ai_client, config)
    
    # Система печатания
    typing_config = config.get('typing', {})
    self.typing_simulator = TypingSimulator({
        'typing_mode': typing_config.get('mode', 'fast'),
        'show_typing_indicator': typing_config.get('show_typing_indicator', True),
        'natural_pauses': typing_config.get('natural_pauses', True)
    })
    self.typing_indicator = TypingIndicator()
    
    # Планировщик
    self.scheduler = AsyncIOScheduler()
    
    # Состояние
    self.last_message_time = None
    self.daily_message_count = 0
    self.conversation_history = []
    
    self.commands_enabled = True
    
    logging.basicConfig(level=logging.INFO)
    self.logger = logging.getLogger(__name__)
    
    self.setup_realistic_scheduler()
    
    def setup_realistic_scheduler(self):
        """Настройка реалистичного планировщика"""
        
        # Основной цикл сознания - каждые 30 минут
        self.scheduler.add_job(
            self.consciousness_cycle,
            IntervalTrigger(minutes=30),
            id='consciousness'
        )
        
        # Обновление физиологического состояния - каждый час
        self.scheduler.add_job(
            self.update_physical_state,
            IntervalTrigger(hours=1),
            id='physical_update'
        )
        
        # Консолидация памяти - раз в день
        self.scheduler.add_job(
            self.daily_memory_consolidation,
            IntervalTrigger(days=1),
            id='memory_consolidation'
        )
        
        self.scheduler.start()
    
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
        """Реалистичное решение об инициативе"""
        
        initiative_desire = current_state.get("initiative_desire", 0)
        
        # Базовые условия
        if initiative_desire < 4:
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
        
        # Рабочее время - реже пишет
        if activity_context == "work_time" and random.random() < 0.7:
            return False
        
        # Вечер - больше желания общаться
        if activity_context == "evening_time":
            initiative_desire += 2
        
        # Финальная проверка с рандомом
        threshold = 6 - (initiative_desire * 0.3)
        return random.random() > (threshold / 10)
    
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
    """Обработка сообщения пользователя с БД контекстом"""
    
    try:
        # Получаем настроение ДО обработки
        mood_before = self.psychological_core.emotional_momentum["current_emotion"]
        
        # Обновляем эмоциональное состояние от получения сообщения
        self.psychological_core.update_emotional_state("positive_interaction", 1.0)
        
        # Получаем текущее состояние
        current_state = await self.optimized_ai.get_simple_mood_calculation(
            self.psychological_core
        )
        
        # НОВОЕ: Получаем контекст из базы данных
        db_context = self.enhanced_memory.get_context_for_response(message)
        current_state['memory_context'] = db_context
        
        # Логируем контекст для отладки
        self.logger.info(f"Контекст из БД: {db_context[:100]}...")
        
        # Генерируем ответ с контекстом
        ai_messages = await self.optimized_ai.generate_split_response(message, current_state)
        
        # Получаем настроение ПОСЛЕ обработки
        mood_after = self.psychological_core.emotional_momentum["current_emotion"]
        
        # НОВОЕ: Сохраняем диалог в базу данных
        conversation_id = self.enhanced_memory.add_conversation(
            message, ai_messages, mood_before, mood_after
        )
        
        self.logger.info(f"Диалог сохранен в БД с ID: {conversation_id}")
        
        # Сохраняем также в локальную историю для совместимости
        await self.save_conversation(message, ai_messages)
        
        self.last_message_time = datetime.now()
        return ai_messages
        
    except Exception as e:
        self.logger.error(f"Ошибка обработки сообщения: {e}")
        return ["Извини, что-то пошло не так... 😅 Попробуй еще раз!"]
    
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
        """Статистика разговоров"""
        if not self.conversation_history:
            return {"total_conversations": 0}
        
        total_user_messages = len(self.conversation_history)
        total_ai_messages = sum(conv.get('message_count', 1) for conv in self.conversation_history)
        avg_messages_per_response = total_ai_messages / total_user_messages if total_user_messages > 0 else 0
        
        return {
            "total_conversations": total_user_messages,
            "total_ai_messages": total_ai_messages,
            "avg_messages_per_response": round(avg_messages_per_response, 1),
            "daily_initiatives_sent": self.daily_message_count,
            "last_conversation": self.conversation_history[-1]['timestamp'].strftime('%H:%M:%S') if self.conversation_history else None
        }
    
    async def start(self):
        """Запуск компаньона"""
        self.logger.info("Реалистичный AI-компаньон с многосообщенческими ответами запущен")
        
        while True:
            await asyncio.sleep(1)
    
    def stop(self):
        """Остановка компаньона"""
        self.scheduler.shutdown()
        self.logger.info("AI-компаньон остановлен")
