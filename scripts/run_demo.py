"""
Демо-скрипт для тестирования функций
"""

import asyncio
import json

from app.core.companion import RealisticAICompanion

async def demo():
    """Демонстрация возможностей"""
    
    print("🎭 Демо AI-компаньона")
    print("=" * 30)
    
    # Конфигурация для демо
    config = {
        "ai": {
            "openrouter_api_key": "demo_key",
            "model": "deepseek/deepseek-chat"
        },
        "character": {
            "name": "Алиса",
            "personality_traits": {
                "extraversion": 7.0,
                "agreeableness": 8.0,
                "conscientiousness": 6.0,
                "neuroticism": 4.0,
                "openness": 9.0
            }
        },
        "database": {"path": "data/demo.db"},
        "behavior": {
            "max_daily_initiatives": 5,
            "min_hours_between_initiatives": 1
        }
    }
    
    # Создаем компаньона (без реального AI)
    companion = RealisticAICompanion(config)
    
    print("👤 Персонаж создан:")
    print(f"   Имя: {config['character']['name']}")
    print(f"   Личность: {companion.psychological_core.get_personality_description()}")
    
    # Демонстрируем расчет настроения
    mood = companion.psychological_core.calculate_current_mood()
    print(f"   Настроение: {mood:.1f}/10")
    
    # Демонстрируем эмоциональные изменения
    print("\n🎭 Тестируем эмоциональные реакции:")
    
    events = [
        ("positive_interaction", 2.0, "Получил комплимент"),
        ("stress", 1.5, "Сложная задача на работе"),
        ("rest", 1.0, "Отдохнул дома")
    ]
    
    for event, intensity, description in events:
        companion.psychological_core.update_emotional_state(event, intensity)
        emotion = companion.psychological_core.emotional_momentum["current_emotion"]
        emotion_intensity = companion.psychological_core.emotional_momentum["emotion_intensity"]
        
        print(f"   {description} → {emotion} ({emotion_intensity:.1f})")
    
    # Демонстрируем память
    print("\n🧠 Тестируем систему памяти:")
    
    memories = [
        ("Пользователь любит кофе", "preference", 6),
        ("Работает программистом", "fact", 8),
        ("Грустил вчера", "emotion", 4)
    ]
    
    for content, mem_type, importance in memories:
        companion.memory_system.add_memory(content, mem_type, importance)
        print(f"   💭 {content}")
    
    # Получаем релевантные воспоминания
    relevant = companion.memory_system.get_relevant_memories("программист работа", 2)
    print(f"\n🔍 Релевантные воспоминания для 'программист работа':")
    for memory in relevant:
        print(f"   - {memory['content']} (важность: {memory['importance']})")
    
    print("\n✨ Демо завершено!")

if __name__ == "__main__":
    asyncio.run(demo())