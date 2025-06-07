"""
Модуль работы с базой данных
"""

import sqlite3
import os
from pathlib import Path

def init_database(db_path: str = "data/companion.db"):
    """Инициализация базы данных из схемы"""
    
    # Создаем директорию если не существует
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Путь к схеме
    schema_path = Path(__file__).parent / "schema.sql"
    
    # Создаем базу данных
    with sqlite3.connect(db_path) as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.commit()
    
    return db_path

__all__ = ['init_database']