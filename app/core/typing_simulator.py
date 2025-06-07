# Модуль имитации реалистичного печатания с учетом эмоционального состояния

import asyncio
import random
import logging
from typing import Dict, Any, List, Callable, Awaitable

class TypingSimulator:
    """Имитатор реалистичного печатания с учетом эмоционального состояния"""
    
    def __init__(self, config: Dict[str, Any]):
        # Инициализируем логгер перед использованием
        self.logger = logging.getLogger(__name__)
        
        # Настройки скорости печатания (слов в минуту)
        self.speed_modes = {
            "lightning": 200,  # Мгновенные ответы
            "fast": 100,       # Быстрые ответы
            "normal": 60,      # Обычные ответы
            "slow": 40         # Медленные ответы
        }
        
        # Текущий режим скорости
        self.current_mode = config.get("default_speed_mode", "normal")
        
        # Базовая скорость печатания (слов в минуту)
        self.base_typing_speed = self.speed_modes[self.current_mode]
        
        # Настройки вариативности
        self.variability = config.get("variability", 0.2)  # 20% вариативность
        
        # Настройки пауз
        self.pause_settings = {
            "between_messages": {
                "min": config.get("min_pause_between_messages", 1.0),
                "max": config.get("max_pause_between_messages", 3.0)
            },
            "thinking_time": {
                "min": config.get("min_thinking_time", 1.5),
                "max": config.get("max_thinking_time", 4.0)
            }
        }
        
        # Эмоциональные модификаторы
        self.emotion_modifiers = {
            "excited": 1.3,    # Быстрее обычного
            "happy": 1.2,      # Немного быстрее
            "calm": 1.0,       # Нормальная скорость
            "sad": 0.8,        # Медленнее
            "angry": 1.4,      # Очень быстро
            "tired": 0.7       # Очень медленно
        }
        
        # Энергетические модификаторы
        self.energy_modifiers = {
            "high": 1.2,       # Высокая энергия - быстрее
            "normal": 1.0,     # Нормальная энергия
            "low": 0.8         # Низкая энергия - медленнее
        }
        
        # Применяем настройки скорости
        self._apply_speed_mode(self.current_mode)
        
        # Telegram app (будет установлен позже)
        self.telegram_app = None
        
        self.logger.info(f"Инициализирован симулятор печатания: режим={self.current_mode}")
    
    def _apply_speed_mode(self, mode: str):
        """Применяет настройки скорости печатания"""
        if mode in self.speed_modes:
            self.current_mode = mode
            self.base_typing_speed = self.speed_modes[mode]
            self.logger.debug(f"Режим печатания: {mode} ({self.base_typing_speed} слов/мин)")
        else:
            self.logger.warning(f"Неизвестный режим печатания: {mode}, используем 'normal'")
            self.current_mode = "normal"
            self.base_typing_speed = self.speed_modes["normal"]
    
    def set_speed_mode(self, mode: str):
        """Устанавливает режим скорости печатания"""
        self._apply_speed_mode(mode)
    
    def _get_energy_level_modifier(self, energy_level: int) -> float:
        """Возвращает модификатор скорости в зависимости от уровня энергии"""
        if energy_level >= 80:
            return self.energy_modifiers["high"]
        elif energy_level >= 40:
            return self.energy_modifiers["normal"]
        else:
            return self.energy_modifiers["low"]
    
    def _get_emotion_modifier(self, emotional_state: str) -> float:
        """Возвращает модификатор скорости в зависимости от эмоционального состояния"""
        # Нормализуем эмоциональное состояние
        emotional_state = emotional_state.lower()
        
        # Маппинг похожих эмоций
        emotion_mapping = {
            "радост": "happy",
            "счаст": "happy",
            "весел": "happy",
            "спокой": "calm",
            "нейтрал": "calm",
            "грус": "sad",
            "печал": "sad",
            "злост": "angry",
            "раздраж": "angry",
            "устал": "tired",
            "сонлив": "tired",
            "возбужд": "excited",
            "взволнов": "excited"
        }
        
        # Определяем базовую эмоцию
        base_emotion = "calm"  # По умолчанию
        for key, value in emotion_mapping.items():
            if key in emotional_state:
                base_emotion = value
                break
        
        return self.emotion_modifiers.get(base_emotion, 1.0)
    
    def _calculate_typing_time(self, message: str, emotional_state: str, energy_level: int) -> float:
        """Рассчитывает время печатания сообщения с учетом эмоционального состояния"""
        # Количество слов в сообщении
        word_count = len(message.split())
        
        # Базовое время в минутах
        base_time_minutes = word_count / self.base_typing_speed
        
        # Применяем модификаторы
        emotion_mod = self._get_emotion_modifier(emotional_state)
        energy_mod = self._get_energy_level_modifier(energy_level)
        
        # Добавляем случайную вариативность
        variability_factor = 1.0 + random.uniform(-self.variability, self.variability)
        
        # Итоговое время в секундах
        typing_time_seconds = (base_time_minutes * 60) / (emotion_mod * energy_mod) * variability_factor
        
        # Минимальное время для реалистичности
        return max(1.0, typing_time_seconds)
    
    def _calculate_thinking_time(self, message_length: int) -> float:
        """Рассчитывает время "обдумывания" перед печатанием"""
        # Базовое время зависит от длины сообщения
        base_thinking_time = self.pause_settings["thinking_time"]["min"]
        
        # Для длинных сообщений увеличиваем время обдумывания
        if message_length > 50:
            base_thinking_time = random.uniform(
                self.pause_settings["thinking_time"]["min"],
                self.pause_settings["thinking_time"]["max"]
            )
        
        # Для режима lightning минимизируем время обдумывания
        if self.current_mode == "lightning":
            return base_thinking_time * 0.3
        
        return base_thinking_time
    
    def _calculate_between_messages_pause(self) -> float:
        """Рассчитывает паузу между сообщениями"""
        # Для режима lightning минимизируем паузы
        if self.current_mode == "lightning":
            return self.pause_settings["between_messages"]["min"] * 0.5
        
        return random.uniform(
            self.pause_settings["between_messages"]["min"],
            self.pause_settings["between_messages"]["max"]
        )
    
    def get_realistic_delays_summary(self, messages: List[str], 
                                   emotional_state: str, energy_level: int) -> Dict[str, Any]:
        """Возвращает сводку о планируемых задержках для отправки сообщений"""
        
        total_typing_time = 0
        total_thinking_time = 0
        total_pause_time = 0
        
        for message in messages:
            typing_time = self._calculate_typing_time(message, emotional_state, energy_level)
            thinking_time = self._calculate_thinking_time(len(message))
            
            total_typing_time += typing_time
            total_thinking_time += thinking_time
            
            if message != messages[-1]:  # Не добавляем паузу после последнего сообщения
                pause_time = self._calculate_between_messages_pause()
                total_pause_time += pause_time
        
        total_time = total_typing_time + total_thinking_time + total_pause_time
        
        return {
            "message_count": len(messages),
            "total_typing_time": round(total_typing_time, 1),
            "total_thinking_time": round(total_thinking_time, 1),
            "total_pause_time": round(total_pause_time, 1),
            "total_time": round(total_time, 1),
            "speed_mode": self.current_mode,
            "emotional_state": emotional_state,
            "energy_level": energy_level
        }
    
    async def send_messages_with_realistic_timing(
        self, 
        messages: List[str],
        emotional_state: str,
        energy_level: int,
        send_callback: Callable[[str], Awaitable[None]],
        typing_callback: Callable[[bool], Awaitable[None]] = None
    ):
        """Отправляет сообщения с реалистичными задержками"""
        
        for i, message in enumerate(messages):
            # Показываем "печатает..." перед первым сообщением
            if typing_callback and i == 0:
                await typing_callback(True)
            
            # Имитируем "обдумывание" перед первым сообщением
            if i == 0:
                thinking_time = self._calculate_thinking_time(len(message))
                await asyncio.sleep(thinking_time)
            
            # Имитируем время печатания
            typing_time = self._calculate_typing_time(message, emotional_state, energy_level)
            
            # Для режима lightning сокращаем время до минимума
            if self.current_mode == "lightning":
                typing_time = min(typing_time, 0.5)
            
            # Показываем "печатает..." для каждого сообщения
            if typing_callback and i > 0:
                await typing_callback(True)
                
            # Ждем время печатания
            await asyncio.sleep(typing_time)
            
            # Отправляем сообщение
            await send_callback(message)
            
            # Пауза между сообщениями (кроме последнего)
            if i < len(messages) - 1:
                pause_time = self._calculate_between_messages_pause()
                await asyncio.sleep(pause_time)

