"""
Скрипт для инициализации базы данных
"""

import sys
import os
import json
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(str(Path(__file__).parent))

from app.database import init_database, DatabaseManager

def main():
    """Основная функция инициализации БД"""
    
    db_path = "data/companion.db"
    
    print("🗄️  Инициализация базы данных...")
    
    try:
        # Инициализируем базу данных
        init_database(db_path)
        print(f"✅ База данных создана: {db_path}")
        
        # Создаем менеджер базы данных
        db_manager = DatabaseManager(db_path)
        
        # Проверяем созданные таблицы
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("📋 Созданные таблицы:")
            for table in tables:
                print(f"   - {table[0]}")
            
            # Проверяем наличие персонажа
            cursor.execute("SELECT id, name FROM character_profile LIMIT 1")
            character = cursor.fetchone()
            
            if character:
                print(f"👤 Персонаж создан: ID={character[0]}, Имя={character[1]}")
            else:
                print("❌ Персонаж не создан")
        
        # Добавляем тестовые данные
        add_test_data(db_manager)
                
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        sys.exit(1)

def add_test_data(db_manager):
    """Добавление тестовых данных в базу"""
    
    print("\n📝 Добавление тестовых данных...")
    
    # Добавляем тестовый диалог
    conversation_id = db_manager.save_conversation(
        user_message="Привет! Как дела?",
        ai_responses=["Привет! 😊", "У меня всё отлично!", "А у тебя как дела?"],
        mood_before="спокойная",
        mood_after="радостная"
    )
    
    if conversation_id > 0:
        print(f"✅ Тестовый диалог добавлен, ID={conversation_id}")
    
    # Добавляем тестовые воспоминания
    memories = [
        {"type": "fact", "content": "Пользователь любит мангу", "importance": 8},
        {"type": "preference", "content": "Пользователь предпочитает аниме-адаптации", "importance": 6},
        {"type": "event", "content": "Пользователь рассказал о своем дне", "importance": 4}
    ]
    
    for memory in memories:
        memory_id = db_manager.save_memory(
            memory_type=memory["type"],
            content=memory["content"],
            importance=memory["importance"],
            source_conversation_id=conversation_id
        )
        
        if memory_id > 0:
            print(f"✅ Воспоминание добавлено: {memory['content']}, ID={memory_id}")
    
    # Обновляем состояние персонажа
    state_updated = db_manager.update_character_state({
        "mood": "радостная",
        "energy_level": 85,
        "current_activity": "общается с пользователем"
    })
    
    if state_updated:
        print("✅ Состояние персонажа обновлено")
    
    print("\n🎉 Тестовые данные успешно добавлены!")

if __name__ == "__main__":
    main()

