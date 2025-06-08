#!/usr/bin/env python3
"""
Миграция базы данных для эмоциональной системы памяти v2.0
"""

import sqlite3
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

def migrate_to_emotional_memory(db_path: str = "data/companion.db"):
    """Добавляет поля для эмоциональной системы памяти"""
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("🧠💕 Обновление базы данных для эмоциональной памяти...")
            
            # Добавляем новые колонки для эмоций
            emotional_migrations = [
                "ALTER TABLE memories ADD COLUMN emotional_intensity REAL DEFAULT 5.0",
                "ALTER TABLE memories ADD COLUMN emotion_type TEXT DEFAULT 'calm'",
                "ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0",
                "ALTER TABLE memories ADD COLUMN last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE memories ADD COLUMN access_difficulty INTEGER DEFAULT 1",
                "ALTER TABLE memories ADD COLUMN is_deeply_archived BOOLEAN DEFAULT FALSE",
                
                # Поля для консолидации (если ещё не добавлены)
                "ALTER TABLE memories ADD COLUMN consolidation_level TEXT DEFAULT NULL",
                "ALTER TABLE memories ADD COLUMN last_consolidated DATETIME DEFAULT NULL",
                "ALTER TABLE memories ADD COLUMN is_consolidated BOOLEAN DEFAULT FALSE", 
                "ALTER TABLE memories ADD COLUMN is_archived BOOLEAN DEFAULT FALSE"
            ]
            
            for migration in emotional_migrations:
                try:
                    cursor.execute(migration)
                    field_name = migration.split('ADD COLUMN')[1].split()[0]
                    print(f"✅ {field_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        field_name = migration.split('ADD COLUMN')[1].split()[0]
                        print(f"⚠️  Поле уже существует: {field_name}")
                    else:
                        raise
            
            # Создаём специализированные индексы для эмоциональной памяти
            emotional_indexes = [
                """CREATE INDEX IF NOT EXISTS idx_memories_emotional 
                   ON memories(emotion_type, emotional_intensity DESC, importance DESC)""",
                
                """CREATE INDEX IF NOT EXISTS idx_memories_access_pattern 
                   ON memories(access_count DESC, last_accessed DESC)""",
                
                """CREATE INDEX IF NOT EXISTS idx_memories_archival 
                   ON memories(is_deeply_archived, access_difficulty, created_at)""",
                
                """CREATE INDEX IF NOT EXISTS idx_memories_consolidation_emotional
                   ON memories(consolidation_level, emotion_type, emotional_intensity DESC)""",
                
                """CREATE INDEX IF NOT EXISTS idx_memories_retrieval_priority
                   ON memories(is_deeply_archived, access_difficulty, 
                               (importance + emotional_intensity * 0.3) DESC)"""
            ]
            
            print("\n🔍 Создание эмоциональных индексов...")
            for idx in emotional_indexes:
                cursor.execute(idx)
                idx_name = idx.split("IF NOT EXISTS")[1].split("ON")[0].strip()
                print(f"✅ {idx_name}")
            
            conn.commit()
            
            # Проверяем что все поля добавлены
            cursor.execute("PRAGMA table_info(memories)")
            columns = [row[1] for row in cursor.fetchall()]
            
            required_emotional_fields = [
                'emotional_intensity', 'emotion_type', 'access_count', 
                'last_accessed', 'access_difficulty', 'is_deeply_archived'
            ]
            
            missing = [field for field in required_emotional_fields if field not in columns]
            
            if missing:
                print(f"⚠️  Не удалось добавить поля: {missing}")
                return False
            
            print("\n✅ Миграция эмоциональной памяти завершена!")
            print(f"💕 Добавлено эмоциональных полей: {len(required_emotional_fields)}")
            print(f"🔍 Создано индексов: {len(emotional_indexes)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

def test_emotional_memory_system(db_path: str = "data/companion.db"):
    """Тестирует эмоциональную систему памяти"""
    
    print("\n🧪 Тестирование эмоциональной системы памяти...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Создаём тестовое эмоциональное воспоминание
            test_memory = {
                "character_id": 1,
                "memory_type": "emotional_test",
                "content": "Пользователь очень обрадовался когда увидел мой новый косплей",
                "importance": 8,
                "emotional_intensity": 9.2,
                "emotion_type": "joy",
                "access_count": 0,
                "access_difficulty": 1
            }
            
            cursor.execute("""
                INSERT INTO memories 
                (character_id, memory_type, content, importance, 
                 emotional_intensity, emotion_type, access_count, access_difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(test_memory.values()))
            
            # Тестируем поиск по эмоциональным критериям
            cursor.execute("""
                SELECT content, emotional_intensity, emotion_type,
                       (importance + emotional_intensity * 0.3) as total_score
                FROM memories 
                WHERE emotion_type = ? AND emotional_intensity >= ?
                ORDER BY total_score DESC
            """, ("joy", 8.0))
            
            results = cursor.fetchall()
            
            if results:
                print("✅ Эмоциональный поиск работает:")
                for result in results[:2]:
                    content, intensity, emotion, score = result
                    print(f"   - {emotion}({intensity:.1f}): {content[:50]}... (скор: {score:.1f})")
                
                # Удаляем тестовую запись
                cursor.execute("DELETE FROM memories WHERE memory_type = ?", ("emotional_test",))
                conn.commit()
                
                return True
            else:
                print("❌ Эмоциональный поиск не работает")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

async def enhance_existing_memories_demo(db_path: str = "data/companion.db"):
    """Демонстрация улучшения существующих воспоминаний"""
    
    print("\n🎭 Демонстрация анализа эмоций существующих воспоминаний...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Находим воспоминания без эмоциональных меток
            cursor.execute("""
                SELECT id, content 
                FROM memories 
                WHERE emotional_intensity IS NULL 
                AND content IS NOT NULL
                AND LENGTH(content) > 20
                LIMIT 5
            """)
            
            memories_without_emotions = cursor.fetchall()
            
            if not memories_without_emotions:
                print("✅ Все воспоминания уже имеют эмоциональные метки")
                return True
            
            print(f"📋 Найдено {len(memories_without_emotions)} воспоминаний без эмоций")
            
            # Добавляем примерные эмоциональные метки (в реальности - через AI)
            sample_emotions = [
                ("joy", 7.5), ("love", 8.2), ("excitement", 6.8), 
                ("calm", 5.0), ("surprise", 7.0)
            ]
            
            for i, (memory_id, content) in enumerate(memories_without_emotions):
                emotion, intensity = sample_emotions[i % len(sample_emotions)]
                
                cursor.execute("""
                    UPDATE memories 
                    SET emotional_intensity = ?, emotion_type = ?
                    WHERE id = ?
                """, (intensity, emotion, memory_id))
                
                print(f"   ✅ Память {memory_id}: {emotion}({intensity:.1f}) - {content[:40]}...")
            
            conn.commit()
            print("🎉 Эмоциональное улучшение воспоминаний завершено!")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка улучшения воспоминаний: {e}")
        return False

def show_emotional_memory_stats(db_path: str = "data/companion.db"):
    """Показывает статистику эмоциональной памяти"""
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            print("\n📊 СТАТИСТИКА ЭМОЦИОНАЛЬНОЙ ПАМЯТИ:")
            
            # Общая статистика
            cursor.execute("SELECT COUNT(*) FROM memories")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memories WHERE emotional_intensity IS NOT NULL")
            with_emotions = cursor.fetchone()[0]
            
            print(f"📈 Общая статистика:")
            print(f"   • Всего воспоминаний: {total}")
            print(f"   • С эмоциональными метками: {with_emotions}")
            print(f"   • Покрытие эмоциями: {(with_emotions/total*100):.1f}%" if total > 0 else "   • Покрытие: 0%")
            
            # Статистика по эмоциям
            cursor.execute("""
                SELECT emotion_type, COUNT(*), AVG(emotional_intensity), AVG(importance)
                FROM memories 
                WHERE emotion_type IS NOT NULL 
                GROUP BY emotion_type
                ORDER BY COUNT(*) DESC
            """)
            
            emotion_stats = cursor.fetchall()
            if emotion_stats:
                print(f"\n🎭 По типам эмоций:")
                for emotion, count, avg_intensity, avg_importance in emotion_stats:
                    print(f"   • {emotion}: {count} воспоминаний (интенсивность: {avg_intensity:.1f}, важность: {avg_importance:.1f})")
            
            # Топ эмоционально ярких воспоминаний
            cursor.execute("""
                SELECT content, emotion_type, emotional_intensity, importance,
                       (importance + emotional_intensity * 0.3) as total_score
                FROM memories 
                WHERE emotional_intensity IS NOT NULL
                ORDER BY total_score DESC
                LIMIT 3
            """)
            
            top_memories = cursor.fetchall()
            if top_memories:
                print(f"\n🌟 Самые яркие воспоминания:")
                for content, emotion, intensity, importance, score in top_memories:
                    print(f"   • {emotion}({intensity:.1f}): {content[:60]}... (скор: {score:.1f})")
            
            # Консолидированная память
            cursor.execute("SELECT COUNT(*) FROM memories WHERE is_consolidated = 1")
            consolidated = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memories WHERE is_deeply_archived = 1")
            archived = cursor.fetchone()[0]
            
            print(f"\n🔄 Состояние консолидации:")
            print(f"   • Консолидированных: {consolidated}")
            print(f"   • Глубоко заархивированных: {archived}")
            print(f"   • Активных в памяти: {total - archived}")
            
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")

def main():
    """Основная функция установки эмоциональной памяти"""
    
    print("🧠💕 УСТАНОВКА ЭМОЦИОНАЛЬНОЙ СИСТЕМЫ ПАМЯТИ v2.0")
    print("=" * 60)
    
    db_path = "data/companion.db"
    
    # Проверяем существование БД
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        print("💡 Сначала запустите: python scripts/setup_db.py")
        return
    
    # Выполняем миграцию
    print("🔄 Шаг 1: Миграция схемы базы данных...")
    if not migrate_to_emotional_memory(db_path):
        print("❌ Миграция провалилась!")
        return
    
    # Тестируем систему
    print("\n🧪 Шаг 2: Тестирование эмоциональной системы...")
    if not test_emotional_memory_system(db_path):
        print("❌ Тестирование провалилось!")
        return
    
    # Улучшаем существующие воспоминания
    print("\n🎭 Шаг 3: Добавление эмоций к существующим воспоминаниям...")
    try:
        # В реальной версии здесь будет вызов enhance_existing_memories_with_emotions
        asyncio.run(enhance_existing_memories_demo(db_path))
    except Exception as e:
        print(f"⚠️  Ошибка улучшения воспоминаний: {e}")
    
    # Показываем финальную статистику
    print("\n📊 Шаг 4: Финальная статистика...")
    show_emotional_memory_stats(db_path)
    
    print("\n🎉 ЭМОЦИОНАЛЬНАЯ СИСТЕМА ПАМЯТИ v2.0 ГОТОВА!")
    print("\n💡 Что добавлено:")
    print("   🧠 Эмоциональная окраска всех воспоминаний")
    print("   📊 Динамические пороги важности")
    print("   🔄 Умная консолидация по эмоциональным контекстам")
    print("   📦 Архивирование вместо удаления")
    print("   🎯 Частота доступа влияет на приоритет")
    print("   💕 Персонализация под стиль общения пользователя")
    
    print("\n🚀 Система будет автоматически:")
    print("   • Анализировать эмоции новых воспоминаний")
    print("   • Консолидировать память каждые 6 часов")
    print("   • Адаптировать пороги под активность пользователя")
    print("   • Сохранять эмоционально важные моменты")

if __name__ == "__main__":
    main()