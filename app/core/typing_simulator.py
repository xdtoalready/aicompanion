# Модуль имитации реалистичного печатания сообщений

import re
import random
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime

class TypingSimulator:
    """Система для реалистичной имитации печатания сообщений"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Режимы скорости печатания
        self.speed_modes = {
            "lightning": {  # Мгновенные ответы
                "base_speed": 200,
                "min_time": 0.3,
                "max_time": 2.0
            },
            "fast": {       # Быстрые ответы (по умолчанию)
                "base_speed": 100,
                "min_time": 0.5,
                "max_time": 5.0
            },
            "normal": {     # Обычные ответы
                "base_speed": 60,
                "min_time": 1.0,
                "max_time": 8.0
            },
            "slow": {       # Медленные, задумчивые ответы
                "base_speed": 40,
                "min_time": 2.0,
                "max_time": 12.0
            }
        }
        
        # Устанавливаем режим по умолчанию
        self.current_mode = config.get('typing_mode', 'fast')
        self._apply_speed_mode(self.current_mode)
        
        # Эмоциональные модификаторы (обновлены для быстрого режима)
        self.emotion_modifiers = {
            "excited": 1.4,      # быстрее печатает когда возбуждена
            "happy": 1.2,        # немного быстрее
            "calm": 1.0,         # базовая скорость
            "anxious": 0.7,      # медленнее, неуверенно
            "sad": 0.6,          # медленно и печально
            "angry": 1.5,        # быстро и резко
            "tired": 0.5         # очень медленно
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _apply_speed_mode(self, mode: str):
        """Применяет настройки режима скорости"""
        if mode not in self.speed_modes:
            mode = 'fast'
        
        settings = self.speed_modes[mode]
        self.base_typing_speed = settings['base_speed']
        self.min_typing_time = settings['min_time']
        self.max_typing_time = settings['max_time']
        
        self.logger.debug(f"Режим печатания: {mode} ({self.base_typing_speed} слов/мин)")
    
    def set_speed_mode(self, mode: str):
        """Устанавливает режим скорости печатания"""
        self.current_mode = mode
        self._apply_speed_mode(mode)
    
    def calculate_typing_time(self, message: str, emotional_state: str = "calm", 
                            energy_level: int = 50) -> float:
        """Вычисляет реалистичное время печатания сообщения"""
        
        # Подсчет слов и сложности
        word_count = len(message.split())
        char_count = len(message)
        
        # Учитываем сложность символов
        complexity_factor = self._calculate_complexity_factor(message)
        
        # Базовое время: слова / скорость * 60 секунд
        base_time = (word_count / self.base_typing_speed) * 60
        
        # Применяем модификаторы
        emotion_mod = self.emotion_modifiers.get(emotional_state, 1.0)
        energy_mod = energy_level / 100  # от 0 до 1
        
        # Финальное время
        typing_time = base_time * complexity_factor * emotion_mod * (0.5 + energy_mod * 0.5)
        
        # Добавляем случайность ±20%
        random_factor = random.uniform(0.8, 1.2)
        typing_time *= random_factor
        
        # Ограничиваем время
        typing_time = max(self.min_typing_time, min(self.max_typing_time, typing_time))
        
        self.logger.debug(f"Время печатания для '{message[:30]}...': {typing_time:.1f}с")
        return typing_time
    
    def _calculate_complexity_factor(self, message: str) -> float:
        """Вычисляет коэффициент сложности текста"""
        
        complexity = 1.0
        
        # Знаки препинания замедляют
        punctuation_count = len(re.findall(r'[.!?,:;]', message))
        complexity += punctuation_count * 0.1
        
        # Эмодзи требуют поиска и выбора
        emoji_count = len(re.findall(r'[😀-🿿]', message))
        complexity += emoji_count * 0.2
        
        # Длинные слова сложнее печатать
        words = message.split()
        long_words = len([w for w in words if len(w) > 7])
        complexity += long_words * 0.05
        
        # Цифры и специальные символы
        special_chars = len(re.findall(r'[0-9@#$%^&*()_+=\[\]{}|\\:";\'<>?,./]', message))
        complexity += special_chars * 0.05
        
        return min(complexity, 2.0)  # максимум x2 замедление
    
    def calculate_pause_between_messages(self, prev_message: str, next_message: str,
                                       emotional_state: str = "calm") -> float:
        """Вычисляет паузу между сообщениями"""
        
        # Базовая пауза зависит от связности сообщений
        base_pause = 0.5
        
        # Если сообщения связаны логически - меньше пауза
        if self._are_messages_connected(prev_message, next_message):
            base_pause = random.uniform(0.3, 0.8)
        else:
            base_pause = random.uniform(0.8, 2.0)
        
        # Эмоциональные модификаторы пауз
        emotion_pause_mods = {
            "excited": 0.5,    # быстро переходит к следующей мысли
            "happy": 0.7,      
            "calm": 1.0,
            "anxious": 1.3,    # больше пауз, думает
            "sad": 1.5,        # медленные переходы
            "angry": 0.4,      # резко, без пауз
            "tired": 1.8       # долгие паузы
        }
        
        pause_mod = emotion_pause_mods.get(emotional_state, 1.0)
        final_pause = base_pause * pause_mod
        
        return max(0.2, min(3.0, final_pause))
    
    def _are_messages_connected(self, msg1: str, msg2: str) -> bool:
        """Проверяет логическую связность сообщений (улучшенный алгоритм)"""
        
        msg1_lower = msg1.lower()
        msg2_lower = msg2.lower()
        
        # Если второе сообщение начинается с связок
        connectors = ['и', 'а', 'но', 'да', 'так', 'ну', 'вот', 'кстати', 'кроме того', 
                     'хм', 'ой', 'ага', 'да-да', 'именно', 'точно', 'конечно']
        if any(msg2_lower.startswith(c + ' ') or msg2_lower.startswith(c + ',') for c in connectors):
            return True
        
        # Если много общих значимых слов (исключаем служебные)
        stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'к', 'из', 'что', 'как', 
                     'это', 'тот', 'который', 'а', 'но', 'или', 'же', 'бы', 'был'}
        
        words1 = set(msg1_lower.split()) - stop_words
        words2 = set(msg2_lower.split()) - stop_words
        
        if len(words1) > 0 and len(words2) > 0:
            common_words = words1.intersection(words2)
            overlap_ratio = len(common_words) / min(len(words1), len(words2))
            if overlap_ratio > 0.3:  # 30% общих слов = связанные
                return True
        
        # Если второе продолжает мысль (вопрос после утверждения, ответ на вопрос)
        if msg1.endswith('.') and msg2.endswith('?'):
            return True
        if msg1.endswith('?') and not msg2.endswith('?'):
            return True
        
        # Если содержат вопросительные/ответные паттерны
        question_patterns = ['что', 'как', 'где', 'когда', 'почему', 'зачем', 'кто']
        answer_patterns = ['потому что', 'из-за', 'благодаря', 'например', 'то есть']
        
        has_question = any(pattern in msg1_lower for pattern in question_patterns)
        has_answer = any(pattern in msg2_lower for pattern in answer_patterns)
        
        if has_question and has_answer:
            return True
        
        # Эмоциональная связность (реакции)
        if ('?' in msg1 or '!' in msg1) and any(word in msg2_lower for word in ['хм', 'ну', 'да', 'нет', 'может']):
            return True
        
        return False
    
    async def send_messages_with_realistic_timing(self, messages: List[str], 
                                                emotional_state: str = "calm",
                                                energy_level: int = 50,
                                                send_callback=None,
                                                typing_callback=None) -> None:
        """Отправляет сообщения с реалистичными паузами"""
        
        if not messages:
            return
        
        self.logger.info(f"Начинаю отправку {len(messages)} сообщений с эмоцией: {emotional_state}")
        
        for i, message in enumerate(messages):
            # Показываем "печатает..."
            if typing_callback:
                await typing_callback(True)
            
            # Вычисляем время печатания
            typing_time = self.calculate_typing_time(message, emotional_state, energy_level)
            
            # Имитируем печатание
            await asyncio.sleep(typing_time)
            
            # Убираем "печатает..." и отправляем сообщение
            if typing_callback:
                await typing_callback(False)
            
            if send_callback:
                await send_callback(message)
            
            # Пауза перед следующим сообщением (если есть)
            if i < len(messages) - 1:
                pause_time = self.calculate_pause_between_messages(
                    message, messages[i + 1], emotional_state
                )
                
                self.logger.debug(f"Пауза перед следующим сообщением: {pause_time:.1f}с")
                await asyncio.sleep(pause_time)
        
        self.logger.info("Отправка сообщений завершена")
    
    def get_realistic_delays_summary(self, messages: List[str], 
                                   emotional_state: str = "calm",
                                   energy_level: int = 50) -> Dict[str, Any]:
        """Возвращает сводку по временным задержкам для сообщений"""
        
        if not messages:
            return {"total_time": 0, "details": []}
        
        details = []
        total_time = 0
        
        for i, message in enumerate(messages):
            typing_time = self.calculate_typing_time(message, emotional_state, energy_level)
            
            pause_time = 0
            if i < len(messages) - 1:
                pause_time = self.calculate_pause_between_messages(
                    message, messages[i + 1], emotional_state
                )
            
            message_total = typing_time + pause_time
            total_time += message_total
            
            details.append({
                "message": message[:50] + "..." if len(message) > 50 else message,
                "typing_time": round(typing_time, 1),
                "pause_after": round(pause_time, 1),
                "total": round(message_total, 1)
            })
        
        return {
            "total_time": round(total_time, 1),
            "average_per_message": round(total_time / len(messages), 1),
            "details": details,
            "emotional_state": emotional_state,
            "energy_level": energy_level
        }

class TypingIndicator:
    """Управление индикатором печатания"""
    
    def __init__(self, telegram_app=None):
        self.telegram_app = telegram_app
        self.is_typing = False
    
    async def show_typing(self, chat_id: int):
        """Показать индикатор печатания"""
        if self.telegram_app and not self.is_typing:
            self.is_typing = True
            try:
                await self.telegram_app.bot.send_chat_action(
                    chat_id=chat_id, 
                    action="typing"
                )
            except Exception as e:
                logging.error(f"Ошибка показа typing: {e}")
    
    async def hide_typing(self):
        """Скрыть индикатор печатания"""
        self.is_typing = False
        # В Telegram индикатор исчезает автоматически через 5 секунд
        # или при отправке сообщения
