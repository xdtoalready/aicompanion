"""
Тестовый скрипт для проверки многосообщенческих ответов
"""

import asyncio
import sys
import json
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from app.core.companion import RealisticAICompanion
from app.core.typing_simulator import TypingSimulator

async def test_split_responses():
    """Тестирование алгоритма разделения ответов"""
    
    print("🧪 Тестирование многосообщенческих ответов")
    print("=" * 50)
    
    # Конфигурация для тестов
    config = {
        "ai": {
            "openrouter_api_key": "test_key",  # Для тестов без реального API
            "model": "deepseek/deepseek-chat",
            "max_tokens": 350,
            "temperature": 0.85
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
        "database": {"path": "data/test.db"},
        "behavior": {
            "max_daily_initiatives": 5,
            "min_hours_between_initiatives": 1
        }
    }
    
    # Создаем компаньона
    companion = RealisticAICompanion(config)
    
    print("👤 Персонаж создан:")
    print(f"   Имя: {config['character']['name']}")
    print(f"   Личность: {companion.psychological_core.get_personality_description()}")
    
    # Тестируем TypingSimulator отдельно
    print("\n⌨️  Тестируем систему печатания:")
    
    test_messages = [
        "Привет! Как дела?",
        "У меня сегодня отличное настроение! 😊",
        "Хочется поговорить о чем-то интересном.",
        "А что у тебя нового?"
    ]
    
    typing_sim = TypingSimulator()
    
    for i, msg in enumerate(test_messages, 1):
        typing_time = typing_sim.calculate_typing_time(msg, "happy", 80)
        print(f"   {i}. '{msg}' → {typing_time:.1f}с печатания")
    
    # Тестируем паузы между сообщениями
    print("\n⏸️  Тестируем паузы между сообщениями:")
    
    for i in range(len(test_messages) - 1):
        pause = typing_sim.calculate_pause_between_messages(
            test_messages[i], test_messages[i + 1], "happy"
        )
        print(f"   После '{test_messages[i][:20]}...' → пауза {pause:.1f}с")
    
    # Полная сводка времени
    print("\n📊 Полная сводка времени:")
    
    summary = typing_sim.get_realistic_delays_summary(test_messages, "happy", 80)
    print(f"   Общее время: {summary['total_time']}с")
    print(f"   Среднее на сообщение: {summary['average_per_message']}с")
    print(f"   Эмоциональное состояние: {summary['emotional_state']}")
    
    for detail in summary['details']:
        print(f"   - '{detail['message']}': печать {detail['typing_time']}с + пауза {detail['pause_after']}с")
    
    # Тестируем имитацию отправки
    print("\n📤 Имитация реалистичной отправки:")
    
    sent_messages = []
    
    async def mock_send_callback(message):
        sent_messages.append(message)
        print(f"   📨 Отправлено: {message}")
    
    async def mock_typing_callback(is_typing):
        if is_typing:
            print("   ⌨️  [печатает...]")
        else:
            print("   ✅ [печатание завершено]")
    
    await typing_sim.send_messages_with_realistic_timing(
        messages=test_messages[:2],  # Тестируем первые 2 сообщения
        emotional_state="happy",
        energy_level=80,
        send_callback=mock_send_callback,
        typing_callback=mock_typing_callback
    )
    
    print(f"\n✅ Имитация завершена! Отправлено {len(sent_messages)} сообщений")
    
    # Тестируем разные эмоциональные состояния
    print("\n🎭 Тестируем разные эмоциональные состояния:")
    
    emotions = ["excited", "calm", "anxious", "sad", "angry", "tired"]
    test_msg = "Привет! Как дела у тебя?"
    
    for emotion in emotions:
        time = typing_sim.calculate_typing_time(test_msg, emotion, 50)
        pause = typing_sim.calculate_pause_between_messages(test_msg, "А у меня все хорошо!", emotion)
        print(f"   {emotion:8}: печать {time:.1f}с, пауза {pause:.1f}с")

    # Также добавим простой тест реальной отправки
    print("\n🚀 Тест реальной отправки с разными скоростями:")
    
    emotions_to_test = ["excited", "calm", "tired"]
    short_messages = ["Привет!", "Как дела?", "Отлично! 😊"]
    
    for emotion in emotions_to_test:
        print(f"\n   Эмоция: {emotion}")
        summary = typing_sim.get_realistic_delays_summary(short_messages, emotion, 70)
        print(f"   Общее время: {summary['total_time']}с для {len(short_messages)} сообщений")
        print(f"   Детали:")
        for detail in summary['details']:
            print(f"     - '{detail['message']}': {detail['typing_time']}с + {detail['pause_after']}с")
        
        print(f"   Статус: {'⚡ Быстро' if summary['total_time'] < 10 else '⏳ Медленно' if summary['total_time'] > 20 else '✅ Нормально'}")
    
    # Тестируем новые режимы скорости
    print("\n⚡ Тестируем режимы скорости печатания:")
    
    test_message = "Привет! Как у тебя дела сегодня?"
    modes = ["lightning", "fast", "normal", "slow"]
    
    for mode in modes:
        typing_sim.set_speed_mode(mode)
        time = typing_sim.calculate_typing_time(test_message, "calm", 70)
        print(f"   {mode:9}: {time:.1f}с для '{test_message}'")
    
    # Возвращаем в быстрый режим для остальных тестов
    typing_sim.set_speed_mode("fast")

async def test_message_connection():
    """Тестирование определения связности сообщений"""
    
    print("\n🔗 Тестирование связности сообщений:")
    
    typing_sim = TypingSimulator()
    
    # Тестовые пары сообщений (больше примеров для проверки улучшенного алгоритма)
    test_pairs = [
        ("Привет! Как дела?", "А у меня все отлично!"),  # связанные (ответ на вопрос)
        ("Сегодня хорошая погода.", "И настроение тоже хорошее."),  # связанные (И в начале)
        ("Что думаешь об этом?", "Хм, сложный вопрос..."),  # связанные (реакция на вопрос)
        ("Привет!", "Кстати, я вчера фильм смотрела."),  # связанные (кстати)
        ("Работаю над проектом.", "Проект интересный, но сложный."),  # связанные (общее слово "проект")
        ("Иду в магазин.", "Погода сегодня отличная!"),  # НЕ связанные
        ("Как твои дела?", "Нормально, спасибо!"),  # связанные (вопрос-ответ)
        ("Сложная задача...", "Но я справлюсь!"),  # связанные (но)
        ("Устал сегодня.", "Ну отдохни тогда."),  # связанные (ну)
        ("Купил новую книгу.", "Книги люблю читать."),  # связанные (общее слово "книг")
    ]
    
    for i, (msg1, msg2) in enumerate(test_pairs, 1):
        connected = typing_sim._are_messages_connected(msg1, msg2)
        pause = typing_sim.calculate_pause_between_messages(msg1, msg2, "calm")
        status = "связанные" if connected else "не связанные"
        
        print(f"   {i}. '{msg1}' → '{msg2}'")
        print(f"      Статус: {status}, пауза: {pause:.1f}с")

def test_complexity_calculation():
    """Тестирование расчета сложности текста"""
    
    print("\n🧮 Тестирование расчета сложности:")
    
    typing_sim = TypingSimulator()
    
    test_cases = [
        "Простой текст",
        "Текст с эмодзи! 😊🎉",
        "Сложный текст: с знаками препинания, цифрами 123 и спецсимволами @#$%",
        "Очень длиннющий текст с профессиональными терминами",
        "123 + 456 = 789 (математические вычисления)",
        "😀😁😂🤣😃😄😅😆😉😊"  # много эмодзи
    ]
    
    for text in test_cases:
        complexity = typing_sim._calculate_complexity_factor(text)
        base_time = len(text.split()) / 40 * 60  # базовое время
        modified_time = base_time * complexity
        
        print(f"   '{text}'")
        print(f"     Сложность: {complexity:.2f}x, время: {base_time:.1f}с → {modified_time:.1f}с")

async def main():
    """Основная функция тестирования"""
    
    await test_split_responses()
    await test_message_connection()
    test_complexity_calculation()
    
    print("\n🎉 Все тесты завершены!")
    print("\n💡 Рекомендации:")
    print("   1. Проверьте что TypingSimulator корректно рассчитывает время")
    print("   2. Убедитесь что паузы между сообщениями естественные")
    print("   3. Протестируйте с реальным API для проверки split-ответов")
    print("   4. Настройте эмоциональные модификаторы под ваши предпочтения")
    print("   5. Времена печатания теперь оптимизированы для чатов (быстрее)")

if __name__ == "__main__":
    asyncio.run(main())
