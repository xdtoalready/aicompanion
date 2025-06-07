"""
Модуль работы с базой данных
"""

import sqlite3
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

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

class DatabaseManager:
    """Менеджер базы данных для AI-компаньона"""
    
    def __init__(self, db_path: str = "data/companion.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Проверяем существование базы данных
        if not os.path.exists(db_path):
            self.logger.info(f"База данных не найдена, инициализируем: {db_path}")
            init_database(db_path)
            self._initialize_character()
        else:
            self.logger.info(f"Подключение к существующей базе данных: {db_path}")
    
    def _get_connection(self):
        """Получение соединения с базой данных"""
        return sqlite3.connect(self.db_path)
    
    def _initialize_character(self):
        """Инициализация базового персонажа"""
        character_data = {
            "name": "Алиса",
            "age": 25,
            "gender": "женский",
            "personality": json.dumps({
                "extraversion": 7.0,
                "agreeableness": 8.0,
                "conscientiousness": 6.0,
                "neuroticism": 4.0,
                "openness": 9.0
            }),
            "background": "Живет в большом городе, любит читать мангу и смотреть аниме. Интересуется технологиями и искусством.",
            "interests": json.dumps([
                "манга", "аниме", "технологии", "искусство", "музыка", "психология"
            ]),
            "speech_style": "Дружелюбный, эмоциональный, с использованием эмодзи и разговорных выражений"
        }
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Вставляем базовый профиль
                cursor.execute("""
                INSERT INTO character_profile 
                (name, age, gender, personality, background, interests, speech_style)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    character_data["name"],
                    character_data["age"],
                    character_data["gender"],
                    character_data["personality"],
                    character_data["background"],
                    character_data["interests"],
                    character_data["speech_style"]
                ))
                
                character_id = cursor.lastrowid
                
                # Инициализируем состояние
                cursor.execute("""
                INSERT INTO character_state 
                (character_id, location, mood, energy_level, current_activity)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    character_id,
                    "дома",
                    "спокойная",
                    80,
                    "отдыхает"
                ))
                
                conn.commit()
                self.logger.info(f"Персонаж '{character_data['name']}' инициализирован в базе данных")
                
        except Exception as e:
            self.logger.error(f"Ошибка инициализации персонажа: {e}")
    
    def save_conversation(self, user_message: str, ai_responses: List[str], 
                         mood_before: str = None, mood_after: str = None,
                         message_type: str = "response") -> int:
        """Сохранение диалога в базу данных"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем ID персонажа
                cursor.execute("SELECT id FROM character_profile LIMIT 1")
                result = cursor.fetchone()
                
                if not result:
                    self.logger.error("Персонаж не найден в базе данных")
                    return -1
                
                character_id = result[0]
                
                # Объединяем ответы AI для хранения
                ai_response_text = " | ".join(ai_responses)
                
                # Создаем краткое описание контекста
                context_summary = f"Пользователь: {user_message[:50]}... AI: {ai_responses[0][:50]}..."
                
                # Вставляем запись диалога
                cursor.execute("""
                INSERT INTO conversations 
                (character_id, user_message, ai_response, context_summary, 
                mood_before, mood_after, message_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    character_id,
                    user_message,
                    ai_response_text,
                    context_summary,
                    mood_before,
                    mood_after,
                    message_type
                ))
                
                conversation_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Диалог сохранен в базу данных, ID: {conversation_id}")
                return conversation_id
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения диалога: {e}")
            return -1
    
    def save_memory(self, memory_type: str, content: str, importance: int = 1, 
                   source_conversation_id: int = None) -> int:
        """Сохранение воспоминания в базу данных"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем ID персонажа
                cursor.execute("SELECT id FROM character_profile LIMIT 1")
                result = cursor.fetchone()
                
                if not result:
                    self.logger.error("Персонаж не найден в базе данных")
                    return -1
                
                character_id = result[0]
                
                # Вставляем запись воспоминания
                cursor.execute("""
                INSERT INTO memories 
                (character_id, memory_type, content, importance, source_conversation_id)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    character_id,
                    memory_type,
                    content,
                    importance,
                    source_conversation_id
                ))
                
                memory_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Воспоминание сохранено в базу данных, ID: {memory_id}")
                return memory_id
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения воспоминания: {e}")
            return -1
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних диалогов"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT id, user_message, ai_response, context_summary, 
                       mood_before, mood_after, timestamp, message_type
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                
                conversations = []
                for row in rows:
                    # Разделяем ответы AI
                    ai_responses = row['ai_response'].split(' | ')
                    
                    conversations.append({
                        'id': row['id'],
                        'user_message': row['user_message'],
                        'ai_responses': ai_responses,
                        'context_summary': row['context_summary'],
                        'mood_before': row['mood_before'],
                        'mood_after': row['mood_after'],
                        'timestamp': row['timestamp'],
                        'message_type': row['message_type']
                    })
                
                return conversations
                
        except Exception as e:
            self.logger.error(f"Ошибка получения диалогов: {e}")
            return []
    
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Получение релевантных воспоминаний по запросу"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Простой поиск по ключевым словам
                search_terms = query.lower().split()
                search_pattern = '%' + '%'.join(search_terms) + '%'
                
                cursor.execute("""
                SELECT id, memory_type, content, importance, created_at, last_accessed
                FROM memories
                WHERE LOWER(content) LIKE ?
                ORDER BY importance DESC, last_accessed DESC
                LIMIT ?
                """, (search_pattern, limit))
                
                rows = cursor.fetchall()
                
                memories = []
                for row in rows:
                    memories.append({
                        'id': row['id'],
                        'type': row['memory_type'],
                        'content': row['content'],
                        'importance': row['importance'],
                        'created_at': row['created_at'],
                        'last_accessed': row['last_accessed']
                    })
                
                # Обновляем время последнего доступа
                if memories:
                    memory_ids = [m['id'] for m in memories]
                    placeholders = ','.join(['?'] * len(memory_ids))
                    cursor.execute(f"""
                    UPDATE memories
                    SET last_accessed = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                    """, memory_ids)
                    conn.commit()
                
                return memories
                
        except Exception as e:
            self.logger.error(f"Ошибка получения воспоминаний: {e}")
            return []
    
    def update_character_state(self, state_data: Dict[str, Any]) -> bool:
        """Обновление состояния персонажа"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Получаем ID персонажа
                cursor.execute("SELECT id FROM character_profile LIMIT 1")
                result = cursor.fetchone()
                
                if not result:
                    self.logger.error("Персонаж не найден в базе данных")
                    return False
                
                character_id = result[0]
                
                # Формируем части запроса
                set_parts = []
                values = []
                
                for key, value in state_data.items():
                    if key in ['location', 'mood', 'energy_level', 'current_outfit', 
                              'current_activity', 'last_meal', 'sleep_quality']:
                        set_parts.append(f"{key} = ?")
                        values.append(value)
                
                if not set_parts:
                    self.logger.warning("Нет данных для обновления состояния персонажа")
                    return False
                
                # Добавляем ID персонажа
                values.append(character_id)
                
                # Выполняем обновление
                cursor.execute(f"""
                UPDATE character_state
                SET {', '.join(set_parts)}
                WHERE character_id = ?
                """, values)
                
                conn.commit()
                
                self.logger.info(f"Состояние персонажа обновлено: {state_data}")
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления состояния персонажа: {e}")
            return False
    
    def get_character_profile(self) -> Dict[str, Any]:
        """Получение профиля персонажа"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT cp.*, cs.location, cs.mood, cs.energy_level, 
                       cs.current_outfit, cs.current_activity
                FROM character_profile cp
                JOIN character_state cs ON cp.id = cs.character_id
                LIMIT 1
                """)
                
                row = cursor.fetchone()
                
                if not row:
                    self.logger.error("Персонаж не найден в базе данных")
                    return {}
                
                # Преобразуем JSON поля
                personality = json.loads(row['personality']) if row['personality'] else {}
                interests = json.loads(row['interests']) if row['interests'] else []
                
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'age': row['age'],
                    'gender': row['gender'],
                    'personality': personality,
                    'background': row['background'],
                    'interests': interests,
                    'speech_style': row['speech_style'],
                    'location': row['location'],
                    'mood': row['mood'],
                    'energy_level': row['energy_level'],
                    'current_activity': row['current_activity']
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка получения профиля персонажа: {e}")
            return {}

__all__ = ['init_database', 'DatabaseManager']

