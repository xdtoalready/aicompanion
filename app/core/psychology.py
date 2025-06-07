# Файл: app/core/psychology.py
# Модуль психологии с реалистичной эмоциональной инерцией

import math
import random
from datetime import datetime, timedelta
from typing import Dict, Any

class PsychologicalCore:
    """Психологическое ядро с реалистичной эмоциональной инерцией"""
    
    def __init__(self):
        # Базовые ценности (неизменные)
        self.core_values = {
            "family_importance": 8,
            "career_ambition": 6,
            "creativity_drive": 9,
            "social_connection": 7
        }
        
        # Долгосрочные черты (медленно меняются)
        self.personality_traits = {
            "extraversion": 6.5,
            "agreeableness": 7.8,
            "conscientiousness": 6.2,
            "neuroticism": 4.1,
            "openness": 8.3
        }
        
        # Физиологическое состояние
        self.physical_state = {
            "energy_base": 75,
            "health_status": "normal",
            "sleep_debt": 0,  # часы недосыпа
            "stress_level": 3,  # 0-10
            "biorhythm_phase": "peak"  # peak/decline/low/recovery
        }
        
        # Эмоциональная инерция
        self.emotional_momentum = {
            "current_emotion": "calm",
            "emotion_intensity": 5.0,
            "emotion_duration": 0,  # минуты в текущем состоянии
            "emotion_decay_rate": 0.1,  # как быстро затухает
            "mood_baseline": 6.0  # базовое настроение
        }
        
        # Привычки и рутины
        self.habits = {
            "morning": ["coffee", "check_phone", "plan_day"],
            "work": ["emails", "meetings", "creative_work"],
            "evening": ["unwind", "social_media", "prepare_tomorrow"],
            "night": ["read", "reflect", "sleep"]
        }
    
    def calculate_current_mood(self, external_factors: Dict = None) -> float:
        """Рассчитывает текущее настроение на основе всех факторов"""
        
        # Базовое настроение от личности
        personality_mood = (
            self.personality_traits["extraversion"] * 0.3 +
            (10 - self.personality_traits["neuroticism"]) * 0.4 +
            self.personality_traits["agreeableness"] * 0.2 +
            self.personality_traits["openness"] * 0.1
        )
        
        # Физиологические факторы
        energy_factor = self.physical_state["energy_base"] / 100
        stress_penalty = self.physical_state["stress_level"] * 0.5
        sleep_penalty = min(self.physical_state["sleep_debt"] * 0.8, 3)
        
        # Эмоциональная инерция
        momentum_effect = self.emotional_momentum["emotion_intensity"] * 0.3
        if self.emotional_momentum["current_emotion"] in ["happy", "excited", "content"]:
            momentum_effect = abs(momentum_effect)
        elif self.emotional_momentum["current_emotion"] in ["sad", "angry", "anxious"]:
            momentum_effect = -abs(momentum_effect)
        
        # Внешние факторы (погода, события)
        external_bonus = 0
        if external_factors:
            if external_factors.get("weather") == "sunny":
                external_bonus += 0.5
            if external_factors.get("weekend"):
                external_bonus += 0.8
        
        # Итоговое настроение
        final_mood = (
            personality_mood * 0.4 +
            energy_factor * 3 +
            momentum_effect +
            external_bonus -
            stress_penalty -
            sleep_penalty
        )
        
        return max(1, min(10, final_mood))
    
    def update_emotional_state(self, trigger_event: str, intensity: float):
        """Обновляет эмоциональное состояние с инерцией"""
        
        # Новая эмоция
        emotion_map = {
            "positive_interaction": ("happy", 2.0),
            "accomplishment": ("satisfied", 1.5),
            "stress": ("anxious", -2.0),
            "conflict": ("frustrated", -1.8),
            "surprise": ("excited", 1.2),
            "rest": ("calm", 0.5)
        }
        
        if trigger_event in emotion_map:
            new_emotion, base_intensity = emotion_map[trigger_event]
            
            # Учитываем личность при интенсивности
            if self.personality_traits["neuroticism"] > 7:
                base_intensity *= 1.3  # более острые реакции
            if self.personality_traits["extraversion"] > 7:
                base_intensity *= 1.1  # более выраженные эмоции
            
            # Применяем эмоциональную инерцию
            current_intensity = self.emotional_momentum["emotion_intensity"]
            decay_factor = 1.0 - (self.emotional_momentum["emotion_duration"] * 0.01)
            
            # Смешиваем старую и новую эмоцию
            mixed_intensity = (current_intensity * decay_factor * 0.6) + (base_intensity * intensity * 0.4)
            
            self.emotional_momentum.update({
                "current_emotion": new_emotion,
                "emotion_intensity": mixed_intensity,
                "emotion_duration": 0
            })
    
    def decay_emotions(self, minutes_passed: int):
        """Естественное затухание эмоций со временем"""
        self.emotional_momentum["emotion_duration"] += minutes_passed
        
        # Экспоненциальное затухание
        decay = math.exp(-self.emotional_momentum["emotion_decay_rate"] * minutes_passed)
        self.emotional_momentum["emotion_intensity"] *= decay
        
        # Возврат к базовому настроению
        if self.emotional_momentum["emotion_intensity"] < 0.5:
            self.emotional_momentum["current_emotion"] = "calm"
            self.emotional_momentum["emotion_intensity"] = 0.5
    
    def get_personality_description(self) -> str:
        """Возвращает описание личности для промптов"""
        traits = []
        
        if self.personality_traits["extraversion"] > 7:
            traits.append("общительная")
        elif self.personality_traits["extraversion"] < 4:
            traits.append("интровертная")
        
        if self.personality_traits["agreeableness"] > 7:
            traits.append("доброжелательная")
        
        if self.personality_traits["conscientiousness"] > 7:
            traits.append("ответственная")
        
        if self.personality_traits["neuroticism"] > 7:
            traits.append("эмоциональная")
        elif self.personality_traits["neuroticism"] < 4:
            traits.append("спокойная")
        
        if self.personality_traits["openness"] > 7:
            traits.append("открытая к новому")
        
        return ", ".join(traits) if traits else "уравновешенная"
    
    def adjust_traits(self, changes: Dict[str, float]):
        """Корректирует черты характера от жизненного опыта"""
        for trait, change in changes.items():
            if trait in self.personality_traits:
                current_value = self.personality_traits[trait]
                new_value = max(0, min(10, current_value + change))
                self.personality_traits[trait] = new_value
    
    def get_current_activity(self) -> str:
        """Определяет текущую активность по времени и привычкам"""
        current_hour = datetime.now().hour
        
        if 6 <= current_hour <= 9:
            return random.choice(self.habits["morning"])
        elif 9 <= current_hour <= 17:
            return random.choice(self.habits["work"])
        elif 17 <= current_hour <= 22:
            return random.choice(self.habits["evening"])
        else:
            return random.choice(self.habits["night"])