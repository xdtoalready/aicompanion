# Файл: app/database/memory_manager.py
# Система работы с базой данных для памяти

import sqlite3
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

class DatabaseMemoryManager:
    """Управление памятью через SQLite базу данных с защитой от блокировок"""
    
    def __init__(self, db_path: str = "data/companion.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.character_id = None
        self._init_character_if_needed()
    
    @contextmanager
    def get_db_connection(self, timeout=10):
        """Контекстный менеджер для безопасной работы с БД"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=timeout)
            conn.execute("PRAGMA busy_timeout = 30000")  # 30 секунд ожидания
            conn.execute("PRAGMA journal_mode = WAL")     # Режим WAL для лучшей concurrent работы
            yield conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                self.logger.warning("База данных заблокирована, повторная попытка...")
                time.sleep(1)
                # Вторая попытка
                if conn:
                    conn.close()
                conn = sqlite3.connect(self.db_path, timeout=timeout)
                yield conn
            else:
                raise
        finally:
            if conn:
                conn.close()
    
    def _init_character_if_needed(self):
        """Инициализация персонажа в БД если его нет"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем есть ли персонаж
                cursor.execute("SELECT COUNT(*) FROM character_profile")
                if cursor.fetchone()[0] == 0:
                    # Создаем базовый профиль
                    cursor.execute("""
                        INSERT INTO character_profile 
                        (name, age, gender, personality, background, interests, speech_style)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        "Алиса", 25, "female", 
                        json.dumps({"extraversion": 7, "agreeableness": 8, "openness": 9}),
                        "Дружелюбная AI-компаньон",
                        json.dumps(["аниме", "манга", "общение", "книги"]),
                        "живой и эмоциональный"
                    ))
                    
                    self.character_id = cursor.lastrowid
                    conn.commit()
                    self.logger.info(f"Создан персонаж с ID: {self.character_id}")
                else:
                    cursor.execute("SELECT id FROM character_profile LIMIT 1")
                    self.character_id = cursor.fetchone()[0]
                    
        except Exception as e:
            self.logger.error(f"Ошибка инициализации персонажа: {e}")
            self.character_id = 1  # Fallback ID
    
    def save_conversation(self, user_message: str, ai_responses: List[str], 
                         mood_before: str, mood_after: str):
        """Сохранение диалога в базу"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Объединяем ответы AI в одну строку
                ai_response_text = " | ".join(ai_responses)
                
                cursor.execute("""
                    INSERT INTO conversations 
                    (character_id, user_message, ai_response, mood_before, mood_after, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.character_id, user_message, ai_response_text, 
                    mood_before, mood_after, datetime.now()
                ))
                
                conversation_id = cursor.lastrowid
                conn.commit()
                
                # Извлекаем и сохраняем факты из сообщения
                self._extract_and_save_facts(user_message, ai_response_text, conversation_id)
                
                return conversation_id
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения диалога: {e}")
            return None
    
    def _extract_and_save_facts(self, user_message: str, ai_response: str, conversation_id: int):
        """Извлечение фактов из диалога"""
        try:
            facts = []
            user_lower = user_message.lower()
            
            # Интересы пользователя
            if any(word in user_lower for word in ["люблю", "нравится", "обожаю", "фанат"]):
                facts.append(("preference", f"Пользователь: {user_message}", 7))
            
            # Упоминания конкретных вещей
            if "манга" in user_lower or "аниме" in user_lower:
                facts.append(("interest", f"Интересуется аниме/манга: {user_message}", 6))
            
            if any(word in user_lower for word in ["работаю", "работа", "учусь", "университет"]):
                facts.append(("fact", f"О работе/учебе: {user_message}", 8))
            
            if any(word in user_lower for word in ["грустно", "плохо", "устал", "болею"]):
                facts.append(("emotion", f"Эмоциональное состояние: {user_message}", 6))
            
            # Сохраняем факты в базу
            if facts:
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    for memory_type, content, imp in facts:
                        cursor.execute("""
                            INSERT INTO memories 
                            (character_id, memory_type, content, importance, source_conversation_id)
                            VALUES (?, ?, ?, ?, ?)
                        """, (self.character_id, memory_type, content, imp, conversation_id))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Ошибка извлечения фактов: {e}")
    
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """Получение релевантных воспоминаний"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                if not query.strip():
                    # Если запрос пустой, возвращаем последние важные воспоминания
                    cursor.execute("""
                        SELECT memory_type, content, importance, created_at
                        FROM memories 
                        WHERE character_id = ?
                        ORDER BY importance DESC, created_at DESC
                        LIMIT ?
                    """, (self.character_id, limit))
                else:
                    # Простой поиск по ключевым словам
                    query_words = query.lower().split()
                    search_pattern = '%' + '%'.join(query_words) + '%'
                    
                    cursor.execute("""
                        SELECT memory_type, content, importance, created_at
                        FROM memories 
                        WHERE character_id = ? AND LOWER(content) LIKE ?
                        ORDER BY importance DESC, created_at DESC
                        LIMIT ?
                    """, (self.character_id, search_pattern, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "type": row[0],
                        "content": row[1],
                        "importance": row[2],
                        "created_at": row[3]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Ошибка получения воспоминаний: {e}")
            return []
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Получение недавних диалогов для контекста"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_message, ai_response, timestamp, mood_before, mood_after
                    FROM conversations 
                    WHERE character_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (self.character_id, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "user_message": row[0],
                        "ai_response": row[1],
                        "timestamp": row[2],
                        "mood_before": row[3],
                        "mood_after": row[4]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Ошибка получения диалогов: {e}")
            return []
    
    def build_context_for_prompt(self, current_message: str) -> str:
        """Создание контекста для промпта"""
        try:
            # Получаем релевантные воспоминания
            memories = self.get_relevant_memories(current_message, 3)
            
            # Получаем недавние диалоги
            recent_convs = self.get_recent_conversations(3)
            
            context_parts = []
            
            if memories:
                context_parts.append("ВАЖНЫЕ ФАКТЫ О ПОЛЬЗОВАТЕЛЕ:")
                for mem in memories:
                    context_parts.append(f"- {mem['content']}")
            
            if recent_convs:
                context_parts.append("\nНЕДАВНИЕ ДИАЛОГИ:")
                for conv in recent_convs[-2:]:  # последние 2
                    context_parts.append(f"Пользователь: {conv['user_message']}")
                    context_parts.append(f"Ты: {conv['ai_response']}")
            
            return "\n".join(context_parts) if context_parts else "Новое знакомство"
            
        except Exception as e:
            self.logger.error(f"Ошибка создания контекста: {e}")
            return "Новое знакомство"

class EnhancedMemorySystem:
    """Улучшенная система памяти с базой данных"""
    
    def __init__(self, db_path: str = "data/companion.db"):
        self.db_manager = DatabaseMemoryManager(db_path)
        self.logger = logging.getLogger(__name__)
    
    def add_conversation(self, user_message: str, ai_responses: List[str], 
                        mood_before: str, mood_after: str):
        """Добавление диалога"""
        try:
            return self.db_manager.save_conversation(
                user_message, ai_responses, mood_before, mood_after
            )
        except Exception as e:
            self.logger.error(f"Ошибка добавления диалога: {e}")
            return None
    
    def get_context_for_response(self, user_message: str) -> str:
        """Получение контекста для ответа"""
        try:
            return self.db_manager.build_context_for_prompt(user_message)
        except Exception as e:
            self.logger.error(f"Ошибка получения контекста: {e}")
            return "Новое знакомство"
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Сводка по разговорам"""
        try:
            recent = self.db_manager.get_recent_conversations(10)
            memories = self.db_manager.get_relevant_memories("", 10)
            
            return {
                "recent_conversations": len(recent),
                "total_memories": len(memories),
                "last_conversation": recent[0]['timestamp'] if recent else None
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения сводки: {e}")
            return {
                "recent_conversations": 0,
                "total_memories": 0,
                "last_conversation": None
            }
