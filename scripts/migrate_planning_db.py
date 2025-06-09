#!/usr/bin/env python3
"""
Миграция базы данных для ИИ-планирования
"""

import sqlite3
import os
import logging
from pathlib import Path

def migrate_planning_database(db_path: str = "data/companion.db"):
    """Применяет миграцию для ИИ-планирования"""
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("📅 Миграция БД для ИИ-планирования...")
            
            # Список миграций
            migrations = [
                # Расширение virtual_activities
                "ALTER TABLE virtual_activities ADD COLUMN planned_by TEXT DEFAULT 'auto'",
                "ALTER TABLE virtual_activities ADD COLUMN flexibility INTEGER DEFAULT 5",
                "ALTER TABLE virtual_activities ADD COLUMN importance INTEGER DEFAULT 5", 
                "ALTER TABLE virtual_activities ADD COLUMN emotional_reason TEXT",
                "ALTER TABLE virtual_activities ADD COLUMN can_reschedule BOOLEAN DEFAULT TRUE",
                "ALTER TABLE virtual_activities ADD COLUMN weather_dependent BOOLEAN DEFAULT FALSE",
                "ALTER TABLE virtual_activities ADD COLUMN planning_date DATE",
                "ALTER TABLE virtual_activities ADD COLUMN generated_by_ai BOOLEAN DEFAULT FALSE",
                
                # Новые таблицы
                """CREATE TABLE IF NOT EXISTS planning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER DEFAULT 1,
                    planning_date DATE NOT NULL,
                    planning_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    day_of_week TEXT,
                    character_mood TEXT,
                    weather_context TEXT,
                    total_activities_planned INTEGER DEFAULT 0,
                    planning_prompt TEXT,
                    ai_response TEXT,
                    success BOOLEAN DEFAULT TRUE
                )""",
                
                """CREATE TABLE IF NOT EXISTS future_desires (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER DEFAULT 1,
                    desire_text TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    category TEXT,
                    deadline DATE,
                    attempts_count INTEGER DEFAULT 0,
                    last_mentioned DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fulfilled BOOLEAN DEFAULT FALSE
                )""",
                
                # Индексы
                "CREATE INDEX IF NOT EXISTS idx_activities_planning_date ON virtual_activities(planning_date, generated_by_ai)",
                "CREATE INDEX IF NOT EXISTS idx_activities_flexibility ON virtual_activities(flexibility, importance)",
                "CREATE INDEX IF NOT EXISTS idx_planning_sessions_date ON planning_sessions(planning_date)",
                "CREATE INDEX IF NOT EXISTS idx_desires_priority ON future_desires(priority DESC, deadline ASC)"
            ]
            
            success_count = 0
            for migration in migrations:
                try:
                    cursor.execute(migration)
                    success_count += 1
                    
                    # Определяем что добавляли
                    if "ADD COLUMN" in migration:
                        column_name = migration.split("ADD COLUMN")[1].split()[0]
                        print(f"✅ Добавлена колонка: {column_name}")
                    elif "CREATE TABLE" in migration:
                        table_name = migration.split("CREATE TABLE IF NOT EXISTS")[1].split("(")[0].strip()
                        print(f"✅ Создана таблица: {table_name}")
                    elif "CREATE INDEX" in migration:
                        index_name = migration.split("CREATE INDEX IF NOT EXISTS")[1].split("ON")[0].strip()
                        print(f"✅ Создан индекс: {index_name}")
                        
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"⚠️  Уже существует: {str(e).split(':')[-1].strip()}")
                    else:
                        print(f"❌ Ошибка миграции: {e}")
                        return False
            
            conn.commit()
            
            # Проверяем результат
            cursor.execute("PRAGMA table_info(virtual_activities)")
            columns = [row[1] for row in cursor.fetchall()]
            
            required_columns = ['planned_by', 'flexibility', 'importance', 'generated_by_ai']
            missing = [col for col in required_columns if col not in columns]
            
            if missing:
                print(f"❌ Не удалось добавить колонки: {missing}")
                return False
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['planning_sessions', 'future_desires']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Не удалось создать таблицы: {missing_tables}")
                return False
            
            print(f"\n✅ Миграция завершена успешно!")
            print(f"📊 Применено изменений: {success_count}")
            print(f"📋 Новые колонки: {len(required_columns)}")
            print(f"🗄️  Новые таблицы: {len(required_tables)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Критическая ошибка миграции: {e}")
        return False

def test_planning_database(db_path: str = "data/companion.db"):
    """Тестирует новые возможности БД"""
    
    print("\n🧪 Тестирование БД планирования...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Тест 1: Добавляем план с новыми полями
            cursor.execute("""
                INSERT INTO virtual_activities 
                (character_id, activity_type, description, start_time, end_time,
                 planned_by, flexibility, importance, emotional_reason, generated_by_ai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1, "test_planning", "Тестовая активность ИИ-планирования",
                "2025-06-10 10:00:00", "2025-06-10 11:00:00", 
                "ai_planner", 7, 6, "тестирую новую систему", True
            ))
            
            # Тест 2: Добавляем сессию планирования
            cursor.execute("""
                INSERT INTO planning_sessions
                (planning_date, day_of_week, character_mood, total_activities_planned)
                VALUES (?, ?, ?, ?)
            """, ("2025-06-10", "monday", "optimistic", 5))
            
            # Тест 3: Добавляем желание
            cursor.execute("""
                INSERT INTO future_desires
                (desire_text, priority, category, deadline)
                VALUES (?, ?, ?, ?)
            """, ("хочу заняться новым хобби", 7, "hobby", "2025-07-01"))
            
            conn.commit()
            
            # Проверяем что всё сохранилось
            cursor.execute("SELECT COUNT(*) FROM virtual_activities WHERE generated_by_ai = 1")
            ai_activities = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM planning_sessions")
            sessions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM future_desires")
            desires = cursor.fetchone()[0]
            
            print(f"✅ ИИ-активности: {ai_activities}")
            print(f"✅ Сессии планирования: {sessions}")
            print(f"✅ Желания: {desires}")
            
            # Очищаем тестовые данные
            cursor.execute("DELETE FROM virtual_activities WHERE activity_type = 'test_planning'")
            cursor.execute("DELETE FROM planning_sessions WHERE day_of_week = 'monday'")
            cursor.execute("DELETE FROM future_desires WHERE category = 'hobby'")
            conn.commit()
            
            print("🧹 Тестовые данные очищены")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    print("📅 МИГРАЦИЯ БД ДЛЯ ИИ-ПЛАНИРОВАНИЯ")
    print("=" * 50)
    
    # Применяем миграцию
    if migrate_planning_database():
        # Тестируем
        if test_planning_database():
            print("\n🎉 БД готова для ИИ-планирования!")
            print("\n💡 Следующие шаги:")
            print("   1. Создать DailyPlanningSystem")
            print("   2. Добавить утреннее планирование в 6:00")
            print("   3. Интегрировать с персонажами")
        else:
            print("\n⚠️  Миграция прошла, но тестирование провалилось")
    else:
        print("\n❌ Миграция провалилась!")