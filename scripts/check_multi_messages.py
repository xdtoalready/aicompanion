#!/usr/bin/env python3
"""
Исправленный тестовый скрипт для проверки многосообщенческих ответов
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Правильное добавление пути к проекту
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Теперь импорты должны работать
try:
    from app.core.companion import RealisticAICompanion
    from app.core.typing_simulator import TypingSimulator
    from app.core.character_loader import get_character_loader
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь что запускаете скрипт из корня проекта")
    sys.exit(1)

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
        },
        "typing": {
            "mode": "fast",
            "show_typing_indicator": True,
            "natural_pauses": True
        },
        "messaging": {
            "min_messages": 3,
            "max_messages": 7,
            "target_sentences": 3,
            "use_emojis": True,
            "max_emojis": 2
        }
    }
    
    # Создаем директории для тестов
    os.makedirs("data", exist_ok=True)
    
    try:
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
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тестировании: {e}")
        import traceback
        print(f"Детали: {traceback.format_exc()}")
        return False

async def test_message_connection():
    """Тестирование определения связности сообщений"""
    
    print("\n🔗 Тестирование связности сообщений:")
    
    typing_sim = TypingSimulator()
    
    # Тестовые пары сообщений
    test_pairs = [
        ("Привет! Как дела?", "А у меня все отлично!"),  # связанные (ответ на вопрос)
        ("Сегодня хорошая погода.", "И настроение тоже хорошее."),  # связанные (И в начале)
        ("Что думаешь об этом?", "Хм, сложный вопрос..."),  # связанные (реакция на вопрос)
        ("Привет!", "Кстати, я вчера фильм смотрела."),  # связанные (кстати)
        ("Работаю над проектом.", "Проект интересный, но сложный."),  # связанные (общее слово "проект")
        ("Иду в магазин.", "Погода сегодня отличная!"),  # НЕ связанные
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

async def test_character_loader():
    """Тестирование загрузчика персонажей"""
    
    print("\n👤 Тестирование загрузчика персонажей:")
    
    try:
        loader = get_character_loader()
        
        # Тестируем получение доступных персонажей
        available = loader.get_available_characters()
        print(f"   Найдено персонажей: {len(available)}")
        
        for char in available:
            print(f"   - {char['name']} ({char['id']})")
        
        # Тестируем загрузку персонажа
        if available:
            first_char = available[0]
            loaded = loader.load_character(first_char['id'])
            
            if loaded:
                print(f"   ✅ Персонаж загружен: {loaded['name']}")
                print(f"   Возраст: {loaded.get('age', 'не указан')}")
                print(f"   Описание: {loaded.get('personality', {}).get('description', 'нет')[:50]}...")
            else:
                print(f"   ❌ Не удалось загрузить персонажа {first_char['id']}")
        
        # Тестируем контекст для AI
        context = loader.get_character_context_for_ai()
        print(f"   Контекст для AI: {len(context)} символов")
        print(f"   Начало контекста: {context[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка тестирования character_loader: {e}")
        import traceback
        print(f"   Детали: {traceback.format_exc()}")
        return False

async def main():
    """Основная функция тестирования"""
    
    print("🧪 ИСПРАВЛЕННОЕ ТЕСТИРОВАНИЕ AI-КОМПАНЬОНА")
    print("=" * 50)
    
    tests = [
        ("Загрузчик персонажей", test_character_loader),
        ("Система печатания", test_split_responses),
        ("Связность сообщений", test_message_connection),
        ("Сложность текста", test_complexity_calculation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name.upper()} {'='*20}")
            
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: УСПЕШНО")
            else:
                print(f"❌ {test_name}: ПРОВАЛЕН")
                
        except Exception as e:
            print(f"❌ {test_name}: критическая ошибка - {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")
    
    passed = 0
    failed_tests = []
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed_tests.append(test_name)
    
    print(f"\nРезультат: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Многосообщенческая система работает.")
        print("\n💡 Следующие шаги:")
        print("  1. Настройте API ключи в config/config.json")
        print("  2. Запустите: python main.py")
        print("  3. Протестируйте с реальным API")
    else:
        print(f"\n⚠️ {len(results) - passed} тестов провалено: {', '.join(failed_tests)}")
        print("\n🔧 Проверьте импорты и структуру проекта")

if __name__ == "__main__":
    asyncio.run(main())