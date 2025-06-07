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

from .psychology import PsychologicalCore
from .memory import AdvancedMemorySystem
from .ai_client import OptimizedAI
from .typing_simulator import TypingSimulator, TypingIndicator

class RealisticAICompanion:
    """Реалистичный AI-компаньон с многосообщенческими ответами"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Инициализация компонентов
        self.psychological_core = PsychologicalCore()
        self.memory_system = AdvancedMemorySystem()
        
        # AI клиент
        self.ai_client = AsyncOpenAI(
            api_key=config['ai']['openrouter_api_key'],
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.optimized_ai = OptimizedAI(self.ai_client, config)
        
        # НОВОЕ: Система печатания
        self.typing_simulator = TypingSimulator(config)
        self.typing_indicator = TypingIndicator()
        
        # Планировщик
        self.scheduler = AsyncIOScheduler()
        
        # Состояние
        self.last_message_time = None
        self.daily_message_count = 0
        self.conversation_history = []
        
        # Флаг для отключения команд (будет использоваться позже)
        self.commands_enabled = True  # TODO: установить в False после тестирования
        
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
        """Отправка инициативных сообщений с реалистичным печатанием"""
        
        # Получаем релевантные воспоминания
        recent_memories = self.memory_system.get_relevant_memories("пользователь общение", 3)
        
        # Добавляем контекст памяти в состояние
        memory_context = "\n".join([m["content"] for m in recent_memories])
        current_state['memory_context'] = memory_context if memory_context else 'Еще мало знаешь о пользователе'
        
        try:
            # НОВОЕ: Генерируем множественные сообщения
            messages = await self.optimized_ai.generate_split_response(
                "Хочу написать пользователю что-то интересное", 
                current_state
            )
            
            # Отправляем сообщения с реалистичными паузами
            await self.deliver_messages_with_timing(
                messages, 
                current_state, 
                message_type="initiative"
            )
            
            # Обновляем состояние
            self.psychological_core.update_emotional_state("positive_interaction", 0.5)
            self.last_message_time = datetime.now()
            
            self.logger.info(f"Инициативные сообщения отправлены: {len(messages)} шт.")
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации инициативы: {e}")
    
    async def process_user_message(self, message: str) -> List[str]:
        """Обработка сообщения пользователя с многосообщенческим ответом"""
        
        try:
            # Обновляем эмоциональное состояние от получения сообщения
            self.psychological_core.update_emotional_state("positive_interaction", 1.0)
            
            # Получаем текущее состояние
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            
            # Получаем релевантные воспоминания
            relevant_memories = self.memory_system.get_relevant_memories(message, 4)
            memory_context = "\n".join([f"- {m['content']}" for m in relevant_memories])
            
            # Добавляем контекст воспоминаний
            current_state['memory_context'] = memory_context if memory_context else 'Новое знакомство'
            
            # НОВОЕ: Генерируем множественные сообщения-ответы
            ai_messages = await self.optimized_ai.generate_split_response(message, current_state)
            
            # Сохраняем диалог и извлекаем факты
            await self.save_conversation(message, ai_messages)
            await self.extract_memories(message, ai_messages)
            
            self.last_message_time = datetime.now()
            return ai_messages
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            return ["Извини, что-то пошло не так... 😅"]
    
    async def deliver_messages_with_timing(self, messages: List[str], 
                                         current_state: Dict[str, Any],
                                         message_type: str = "response"):
        """Доставка сообщений с реалистичным печатанием"""
        
        emotional_state = current_state.get('dominant_emotion', 'calm')
        energy_level = current_state.get('energy_level', 50)
        
        # Создаем callback'и для системы печатания
        async def send_callback(msg):
            await self.deliver_message(msg, message_type)
        
        async def typing_callback(is_typing):
            # Будет переопределено в интеграциях
            if is_typing:
                self.logger.debug("Показываем 'печатает...'")
            else:
                self.logger.debug("Скрываем 'печатает...'")
        
        # Показываем сводку времени (для отладки)
        timing_summary = self.typing_simulator.get_realistic_delays_summary(
            messages, emotional_state, energy_level
        )
        self.logger.info(f"Планируемое время отправки: {timing_summary['total_time']}с")
        
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