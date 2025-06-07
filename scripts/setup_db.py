"""
Скрипт для инициализации базы данных
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from app.database import init_database

def main():
    """Основная функция инициализации БД"""
    
    db_path = "data/companion.db"
    
    print("🗄️  Инициализация базы данных...")
    
    try:
        init_database(db_path)
        print(f"✅ База данных создана: {db_path}")
        
        # Проверяем созданные таблицы
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("📋 Созданные таблицы:")
            for table in tables:
                print(f"   - {table[0]}")
                
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()