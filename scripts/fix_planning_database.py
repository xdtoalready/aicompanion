#!/usr/bin/env python3
"""
СРОЧНОЕ исправление схемы базы данных для планирования
scripts/fix_planning_database.py
"""

import sqlite3
import os
import logging
from pathlib import Path

def fix_planning_database(db_path: str = "data/companion.db"):
    """Исправляет схему БД для планирования"""
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🔧 Исправление схемы БД для планирования...")
            
            # 1. Создаём таблицу planning_sessions если её нет
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS planning_sessions (
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
                )
            """)
            print("✅ Таблица planning_sessions создана")
            
            # 2. Проверяем существование virtual_activities
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS virtual_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER DEFAULT 1,
                    activity_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    status TEXT DEFAULT 'planned',
                    mood_effect REAL DEFAULT 0,
                    energy_cost INTEGER DEFAULT 20,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Таблица virtual_activities создана")
            
            # 3. Добавляем новые колонки в virtual_activities
            new_columns = [
                ("planning_date", "DATE"),
                ("generated_by_ai", "BOOLEAN DEFAULT FALSE"),
                ("flexibility", "INTEGER DEFAULT 5"),
                ("importance", "INTEGER DEFAULT 5"),
                ("planned_by", "TEXT DEFAULT 'auto'"),
                ("emotional_reason", "TEXT"),
                ("can_reschedule", "BOOLEAN DEFAULT TRUE"),
                ("weather_dependent", "BOOLEAN DEFAULT FALSE")
            ]
            
            for column_name, column_def in new_columns:
                try:
                    cursor.execute(f"ALTER TABLE virtual_activities ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Добавлена колонка: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"⚠️  Колонка уже существует: {column_name}")
                    else:
                        print(f"❌ Ошибка добавления {column_name}: {e}")
                        return False
            
            # 4. Создаём индексы для быстрого поиска
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_activities_planning_date ON virtual_activities(planning_date, generated_by_ai)",
                "CREATE INDEX IF NOT EXISTS idx_activities_start_time ON virtual_activities(start_time)",
                "CREATE INDEX IF NOT EXISTS idx_planning_sessions_date ON planning_sessions(planning_date)",
                "CREATE INDEX IF NOT EXISTS idx_activities_character ON virtual_activities(character_id, status)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            print("✅ Индексы созданы")
            
            # 5. Проверяем что всё работает
            cursor.execute("SELECT COUNT(*) FROM virtual_activities")
            activities_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM planning_sessions")
            sessions_count = cursor.fetchone()[0]
            
            conn.commit()
            
            print(f"\n✅ Исправление завершено!")
            print(f"📊 Активностей в БД: {activities_count}")
            print(f"📅 Сессий планирования: {sessions_count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Критическая ошибка исправления БД: {e}")
        return False

def test_fixed_database(db_path: str = "data/companion.db"):
    """Тестирует исправленную БД"""
    
    print("\n🧪 Тестирование исправленной БД...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Тест 1: Вставляем план с новыми полями
            from datetime import date, datetime
            today = date.today()
            
            cursor.execute("""
                INSERT INTO virtual_activities 
                (character_id, activity_type, description, start_time, end_time,
                 planning_date, generated_by_ai, flexibility, importance, planned_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1, "test", "Тестовая активность", 
                f"{today} 10:00:00", f"{today} 11:00:00",
                today.isoformat(), True, 7, 6, "ai_planner"
            ))
            
            # Тест 2: Вставляем сессию планирования
            cursor.execute("""
                INSERT INTO planning_sessions
                (planning_date, day_of_week, character_mood, total_activities_planned, success)
                VALUES (?, ?, ?, ?, ?)
            """, (today.isoformat(), "понедельник", "хорошее", 1, True))
            
            conn.commit()
            
            # Тест 3: Проверяем что можем получить планы
            cursor.execute("""
                SELECT activity_type, description, start_time, importance, flexibility
                FROM virtual_activities
                WHERE DATE(start_time) = ? AND generated_by_ai = 1
            """, (today.isoformat(),))
            
            test_plans = cursor.fetchall()
            
            if test_plans:
                print(f"✅ Найдено {len(test_plans)} тестовых планов")
                for plan in test_plans:
                    print(f"   - {plan[0]}: {plan[1]} в {plan[2]} (важность: {plan[3]})")
            else:
                print("❌ Тестовые планы не найдены")
                return False
            
            # Очистка тестовых данных
            cursor.execute("DELETE FROM virtual_activities WHERE activity_type = 'test'")
            cursor.execute("DELETE FROM planning_sessions WHERE day_of_week = 'понедельник'")
            conn.commit()
            
            print("🧹 Тестовые данные очищены")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

if __name__ == "__main__":
    print("🔧 СРОЧНОЕ ИСПРАВЛЕНИЕ БД ДЛЯ ПЛАНИРОВАНИЯ")
    print("=" * 50)
    
    # Исправляем БД
    if fix_planning_database():
        # Тестируем
        if test_fixed_database():
            print("\n🎉 БД исправлена и готова к работе!")
            print("\n💡 Теперь можно:")
            print("   • Запустить /test_planning в Telegram")
            print("   • Проверить /plans")
            print("   • Использовать /activity")
        else:
            print("\n⚠️  БД исправлена, но тестирование провалилось")
    else:
        print("\n❌ Не удалось исправить БД!")