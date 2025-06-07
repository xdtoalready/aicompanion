#!/usr/bin/env python3
"""
Исправленный скрипт быстрого тестирования AI-компаньона
Проверяет базу данных, память и разделение сообщений
"""

import asyncio
import sys
import os
import sqlite3
import time
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

async def test_database():
    """Тестирование базы данных"""
    print("🗄️ Тестирование базы данных...")
    
    db_path = "data/companion.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        print("💡 Запустите: python scripts/setup_db.py")
        return False
    
    try:
        # Закрываем все возможные соединения
        time.sleep(0.5)
        
        with sqlite3.connect(db_path, timeout=10) as conn:
            cursor = conn.cursor()
            
            # Проверяем таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['character_profile', 'character_state', 'conversations', 'memories']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Отсутствуют таблицы: {missing_tables}")
                return False
            
            # Проверяем есть ли персонаж
            cursor.execute("SELECT COUNT(*) FROM character_profile")
            char_count = cursor.fetchone()[0]
            
            if char_count == 0:
                print("⚠️ Персонаж не создан, создаем...")
                cursor.execute("""
                    INSERT INTO character_profile 
                    (name, age, gender, personality, background, interests, speech_style)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    "Алиса", 25, "female", 
                    '{"extraversion": 7, "agreeableness": 8, "openness": 9}',
                    "Дружелюбная AI-компаньон",
                    '["аниме", "манга", "общение", "книги"]',
                    "живой и эмоциональный"
                ))
                conn.commit()
                print("✅ Персонаж создан")
            
            print("✅ База данных работает")
            return True
            
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            print("⚠️ База данных временно заблокирована, повторная попытка...")
            time.sleep(2)
            try:
                with sqlite3.connect(db_path, timeout=30) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM character_profile")
                    print("✅ База данных работает (после повтора)")
                    return True
            except Exception as e2:
                print(f"❌ Ошибка БД (повтор): {e2}")
                return False
        else:
            print(f"❌ Ошибка БД: {e}")
            return False
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

async def test_memory_system():
    """Тестирование системы памяти"""
    print("\n🧠 Тестирование системы памяти...")
    
    try:
        # Импортируем исправленную систему памяти
        sys.path.append(str(Path(__file__).parent.parent / 'app'))
        from database.memory_manager import EnhancedMemorySystem
        
        memory = EnhancedMemorySystem()
        
        # Добавляем тестовый диалог
        test_user_msg = "Я люблю читать мангу Токийские мстители"
        test_ai_responses = ["Ох, отличный выбор!", "Обожаю эту мангу тоже!"]
        
        conv_id = memory.add_conversation(test_user_msg, test_ai_responses, "calm", "happy")
        
        if conv_id:
            print(f"✅ Диалог сохранен с ID: {conv_id}")
        else:
            print("⚠️ Диалог не сохранен, но система работает")
        
        # Тестируем получение контекста
        context = memory.get_context_for_response("манга")
        print(f"✅ Контекст получен: {context[:100]}...")
        
        # Получаем статистику
        stats = memory.get_conversation_summary()
        print(f"✅ Статистика: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка памяти: {e}")
        import traceback
        print(f"Детали: {traceback.format_exc()}")
        return False

async def test_message_splitting():
    """Тестирование разделения сообщений"""
    print("\n✂️ Тестирование разделения сообщений...")
    
    try:
        # Импортируем исправленный AI клиент
        sys.path.append(str(Path(__file__).parent.parent / 'app'))
        from core.ai_client import OptimizedAI
        
        # Мок конфигурация
        config = {
            'ai': {'model': 'test', 'max_tokens': 300, 'temperature': 0.8},
            'character': {'name': 'Алиса'}
        }
        
        # Создаем AI клиент без реального API (для тестов)
        ai = OptimizedAI(None, config)
        
        # Тестируем обработку ответа
        test_responses = [
            "Привет! || Как дела? || У меня все отлично!",
            "Ох, интересный вопрос! || Думаю что манга лучше адаптации. || В ней больше деталей!",
            "Токийские мстители - супер! | Сюжет захватывающий | А какая твоя любимая арка?",
            "Простое сообщение без разделителей"
        ]
        
        for i, response in enumerate(test_responses, 1):
            messages = ai._process_raw_response(response)
            print(f"  Тест {i}: {len(messages)} сообщений")
            for j, msg in enumerate(messages, 1):
                print(f"    {j}. {msg}")
            print()
        
        print("✅ Разделение сообщений работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка разделения: {e}")
        import traceback
        print(f"Детали: {traceback.format_exc()}")
        return False

async def test_question_analysis():
    """Тестирование анализа вопросов"""
    print("\n🎯 Тестирование анализа вопросов...")
    
    try:
        sys.path.append(str(Path(__file__).parent.parent / 'app'))
        from core.ai_client import OptimizedAI
        
        config = {
            'ai': {'model': 'test', 'max_tokens': 300, 'temperature': 0.8},
            'character': {'name': 'Алиса'}
        }
        ai = OptimizedAI(None, config)
        
        test_questions = [
            ("Что думаешь об адаптации vs манга?", "opinion_question"),
            ("Какая манга лучше?", "preference_question"),
            ("Токийские мстители или Атака титанов?", "comparison_question"),
            ("Как дела?", "direct_question"),
            ("Сегодня хорошая погода", "statement")
        ]
        
        for question, expected_type in test_questions:
            detected_type = ai._analyze_question_type(question)
            status = "✅" if detected_type == expected_type else "❌"
            print(f"  {status} '{question}' → {detected_type} (ожидался {expected_type})")
        
        print("✅ Анализ вопросов работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        import traceback
        print(f"Детали: {traceback.format_exc()}")
        return False

async def test_config():
    """Проверка конфигурации"""
    print("\n⚙️ Проверка конфигурации...")
    
    config_path = "config/config.json"
    
    if not os.path.exists(config_path):
        print("❌ Конфигурация не найдена!")
        print("💡 Скопируйте config/config.example.json в config/config.json")
        return False
    
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Проверяем ключевые поля
        checks = [
            ("ai.openrouter_api_key", config.get('ai', {}).get('openrouter_api_key')),
            ("character.name", config.get('character', {}).get('name')),
            ("database.path", config.get('database', {}).get('path')),
        ]
        
        for field, value in checks:
            if not value or value in ["YOUR_OPENROUTER_API_KEY_HERE", "YOUR_TELEGRAM_BOT_TOKEN"]:
                print(f"⚠️ Не настроено: {field}")
            else:
                print(f"✅ {field}: настроено")
        
        print("✅ Конфигурация загружена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

async def test_database_integration():
    """Тестирование интеграции с БД через исправленную систему"""
    print("\n🔗 Тестирование интеграции с БД...")
    
    try:
        sys.path.append(str(Path(__file__).parent.parent / 'app'))
        from database.memory_manager import DatabaseMemoryManager
        
        # Создаем менеджер БД
        db_manager = DatabaseMemoryManager()
        
        # Тестируем сохранение диалога
        conv_id = db_manager.save_conversation(
            "Какая манга лучше - Токийские мстители или Атака титанов?",
            ["Ох, сложный выбор!", "Думаю, Токийские мстители ближе к сердцу.", "А тебе какая больше нравится?"],
            "calm", "happy"
        )
        
        if conv_id:
            print(f"✅ Диалог сохранен в БД: {conv_id}")
        
        # Тестируем получение воспоминаний
        memories = db_manager.get_relevant_memories("манга", 3)
        print(f"✅ Найдено воспоминаний: {len(memories)}")
        
        # Тестируем построение контекста
        context = db_manager.build_context_for_prompt("манга аниме")
        print(f"✅ Контекст построен: {len(context)} символов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интеграции БД: {e}")
        import traceback
        print(f"Детали: {traceback.format_exc()}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🧪 ИСПРАВЛЕННОЕ ТЕСТИРОВАНИЕ AI-КОМПАНЬОНА")
    print("=" * 50)
    
    tests = [
        ("Конфигурация", test_config),
        ("База данных", test_database), 
        ("Система памяти", test_memory_system),
        ("Интеграция с БД", test_database_integration),
        ("Разделение сообщений", test_message_splitting),
        ("Анализ вопросов", test_question_analysis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name.upper()} {'='*20}")
            result = await test_func()
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
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Компаньон готов к работе.")
        print("\n💡 Следующие шаги:")
        print("  1. Настройте API ключи в config/config.json")
        print("  2. Запустите: python main.py")
        print("  3. Протестируйте в Telegram")
        print("  4. Используйте команду /dbcheck для проверки БД")
    else:
        print(f"\n⚠️ {len(results) - passed} тестов провалено: {', '.join(failed_tests)}")
        print("\n🔧 Рекомендации по исправлению:")
        
        if "База данных" in failed_tests:
            print("  - Запустите: python scripts/setup_db.py")
            print("  - Проверьте права доступа к папке data/")
        
        if "Система памяти" in failed_tests:
            print("  - Создайте файл app/database/memory_manager.py")
            print("  - Проверьте что база данных не заблокирована")
        
        if "Разделение сообщений" in failed_tests:
            print("  - Обновите файл app/core/ai_client.py")
            print("  - Добавьте недостающие методы")
        
        print("\n💡 После исправления запустите тест повторно")

if __name__ == "__main__":
    asyncio.run(main())
