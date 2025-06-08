# Система работы с базой данных для памяти

import sqlite3
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

class DatabaseMemoryManager:
    """Менеджер с поддержкой эмоциональной памяти"""
    
    def __init__(self, db_path: str = "data/companion.db"):
        self.db_path = db_path
        self.character_id = 1  # По умолчанию персонаж с ID 1
        self.logger = logging.getLogger(__name__)
        
        # Проверяем что база данных существует
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Проверяет что база данных существует и имеет нужные таблицы"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем существование таблицы memories
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='memories'
                """)
                
                if not cursor.fetchone():
                    self.logger.error("Таблица memories не найдена в БД")
                    raise Exception("База данных не инициализирована. Запустите scripts/setup_db.py")
                    
        except Exception as e:
            self.logger.error(f"Ошибка проверки БД: {e}")
            raise
    
    @contextmanager
    def get_db_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.row_factory = sqlite3.Row  # Для удобного доступа к колонкам
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Ошибка БД: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_conversation(self, user_message: str, ai_responses: List[str], 
                         mood_before: str, mood_after: str) -> Optional[int]:
        """Сохраняет диалог в базу данных"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Объединяем множественные ответы
                ai_response_text = " || ".join(ai_responses)
                
                cursor.execute("""
                    INSERT INTO conversations 
                    (character_id, user_message, ai_response, mood_before, mood_after, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.character_id, user_message, ai_response_text, 
                    mood_before, mood_after, datetime.now().isoformat()
                ))
                
                conversation_id = cursor.lastrowid
                conn.commit()
                
                # Автоматически извлекаем воспоминания из диалога
                self._extract_memories_from_conversation(
                    user_message, ai_responses, conversation_id
                )
                
                return conversation_id
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения диалога: {e}")
            return None
    
    def _extract_memories_from_conversation(self, user_message: str, 
                                          ai_responses: List[str], conversation_id: int):
        """Извлекает факты из диалога для сохранения в память"""
        
        try:
            # Простое извлечение фактов по ключевым словам
            facts_to_save = []
            
            user_lower = user_message.lower()
            
            # Факты о предпочтениях
            preference_keywords = ["люблю", "нравится", "обожаю", "не люблю", "ненавижу"]
            if any(keyword in user_lower for keyword in preference_keywords):
                facts_to_save.append({
                    "content": f"Предпочтения: {user_message}",
                    "type": "preference", 
                    "importance": 6
                })
            
            # Факты о работе/учебе
            work_keywords = ["работаю", "учусь", "работа", "учеба", "профессия"]
            if any(keyword in user_lower for keyword in work_keywords):
                facts_to_save.append({
                    "content": f"Работа/учеба: {user_message}",
                    "type": "life_fact",
                    "importance": 7
                })
            
            # Эмоциональные состояния
            emotion_keywords = ["грустно", "весело", "счастлив", "расстроен", "злой"]
            if any(keyword in user_lower for keyword in emotion_keywords):
                facts_to_save.append({
                    "content": f"Эмоциональное состояние: {user_message}",
                    "type": "emotional_state",
                    "importance": 5
                })
            
            # Сохраняем найденные факты
            for fact in facts_to_save:
                self.add_memory(
                    fact["content"], fact["type"], fact["importance"], 
                    conversation_id=conversation_id
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка извлечения воспоминаний: {e}")
    
    def add_memory(self, content: str, memory_type: str, importance: int,
                   conversation_id: int = None):
        """Добавляет обычное воспоминание"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO memories 
                    (character_id, memory_type, content, importance, 
                     source_conversation_id, created_at, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.character_id, memory_type, content, importance,
                    conversation_id, datetime.now().isoformat(), 
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self.logger.info(f"Сохранено воспоминание: {memory_type} (важность: {importance})")
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения воспоминания: {e}")

    def add_emotional_memory(self, content: str, memory_type: str, importance: int,
                           emotion_type: str = "calm", emotional_intensity: float = 5.0,
                           conversation_id: int = None):
        """Добавляет воспоминание с эмоциональными метаданными"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO memories 
                    (character_id, memory_type, content, importance, 
                     emotional_intensity, emotion_type, source_conversation_id,
                     created_at, last_accessed, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.character_id, memory_type, content, importance,
                    emotional_intensity, emotion_type, conversation_id,
                    datetime.now().isoformat(), datetime.now().isoformat(), 0
                ))
                
                conn.commit()
                self.logger.info(f"💕 Сохранено эмоциональное воспоминание: {emotion_type}({emotional_intensity:.1f})")
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения эмоциональной памяти: {e}")

    def get_relevant_memories(self, context: str, limit: int = 5) -> List[Dict]:
        """Получает релевантные воспоминания по контексту"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Простой поиск по содержимому + учет важности
                context_words = context.lower().split()
                
                if context_words:
                    # Создаем LIKE запрос для каждого слова
                    like_conditions = []
                    params = []
                    
                    for word in context_words[:3]:  # Только первые 3 слова
                        if len(word) > 2:  # Игнорируем короткие слова
                            like_conditions.append("LOWER(content) LIKE ?")
                            params.append(f"%{word}%")
                    
                    if like_conditions:
                        where_clause = "WHERE (" + " OR ".join(like_conditions) + ")"
                    else:
                        where_clause = ""
                else:
                    where_clause = ""
                    params = []
                
                # Добавляем общие условия
                if where_clause:
                    where_clause += " AND character_id = ? AND (is_deeply_archived != 1 OR access_count > 5)"
                else:
                    where_clause = "WHERE character_id = ? AND (is_deeply_archived != 1 OR access_count > 5)"
                
                params.append(self.character_id)
                
                query = f"""
                    SELECT memory_type, content, importance, 
                           COALESCE(emotional_intensity, 5.0) as emotional_intensity,
                           COALESCE(emotion_type, 'calm') as emotion_type,
                           COALESCE(access_count, 0) as access_count,
                           created_at,
                           CASE 
                               WHEN is_consolidated = 1 THEN 'consolidated'
                               ELSE 'regular'
                           END as source,
                           (importance + COALESCE(emotional_intensity, 5.0) * 0.3 + COALESCE(access_count, 0) * 0.1) as relevance_score
                    FROM memories 
                    {where_clause}
                    ORDER BY relevance_score DESC, created_at DESC
                    LIMIT ?
                """
                
                params.append(limit)
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    # Увеличиваем счетчик доступа
                    if row['source'] == 'regular':  # Только для обычных воспоминаний
                        cursor.execute("""
                            UPDATE memories 
                            SET access_count = access_count + 1,
                                last_accessed = ?
                            WHERE content = ? AND character_id = ?
                        """, (datetime.now().isoformat(), row['content'], self.character_id))
                    
                    results.append({
                        "type": row['memory_type'],
                        "content": row['content'], 
                        "importance": row['importance'],
                        "emotional_intensity": row['emotional_intensity'],
                        "emotion_type": row['emotion_type'],
                        "access_count": row['access_count'],
                        "created_at": row['created_at'],
                        "source": row['source'],
                        "relevance_score": row['relevance_score']
                    })
                
                conn.commit()  # Сохраняем обновления access_count
                return results
                
        except Exception as e:
            self.logger.error(f"Ошибка получения воспоминаний: {e}")
            return []

    def get_emotional_memories(self, emotion_type: str = None, min_intensity: float = 0.0, limit: int = 10) -> List[Dict]:
        """Получает воспоминания по эмоциональным критериям"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                if emotion_type:
                    cursor.execute("""
                        SELECT memory_type, content, importance, emotional_intensity, emotion_type,
                               access_count, created_at,
                               (importance + emotional_intensity * 0.3 + access_count * 0.1) as total_score
                        FROM memories 
                        WHERE character_id = ? 
                        AND emotion_type = ?
                        AND emotional_intensity >= ?
                        AND (is_deeply_archived != 1 OR access_count > 5)
                        ORDER BY total_score DESC, created_at DESC
                        LIMIT ?
                    """, (self.character_id, emotion_type, min_intensity, limit))
                else:
                    cursor.execute("""
                        SELECT memory_type, content, importance, emotional_intensity, emotion_type,
                               access_count, created_at,
                               (importance + emotional_intensity * 0.3 + access_count * 0.1) as total_score
                        FROM memories 
                        WHERE character_id = ? 
                        AND emotional_intensity >= ?
                        AND (is_deeply_archived != 1 OR access_count > 5)
                        ORDER BY total_score DESC, created_at DESC
                        LIMIT ?
                    """, (self.character_id, min_intensity, limit))
                
                results = []
                for row in cursor.fetchall():
                    # Увеличиваем счётчик доступа
                    cursor.execute("""
                        UPDATE memories 
                        SET access_count = access_count + 1,
                            last_accessed = ?
                        WHERE content = ? AND character_id = ?
                    """, (datetime.now().isoformat(), row[1], self.character_id))
                    
                    results.append({
                        "type": row[0],
                        "content": row[1],
                        "importance": row[2],
                        "emotional_intensity": row[3],
                        "emotion_type": row[4],
                        "access_count": row[5],
                        "created_at": row[6],
                        "total_score": row[7]
                    })
                
                conn.commit()
                return results
                
        except Exception as e:
            self.logger.error(f"Ошибка получения эмоциональных воспоминаний: {e}")
            return []

    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Получает недавние диалоги"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_message, ai_response, mood_before, mood_after, timestamp
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
                        "mood_before": row[2], 
                        "mood_after": row[3],
                        "timestamp": row[4]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Ошибка получения диалогов: {e}")
            return []

    def build_context_for_prompt(self, current_message: str) -> str:
        """Создание контекста с учётом консолидированной памяти"""
        try:
            # Получаем релевантные воспоминания
            memories = self.get_relevant_memories(current_message, 5)
            
            # Получаем недавние диалоги
            recent_convs = self.get_recent_conversations(3)
            
            context_parts = []
            
            if memories:
                context_parts.append("ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ:")
                
                # Разделяем обычные и консолидированные воспоминания
                regular_memories = [m for m in memories if m.get('source') == 'regular']
                consolidated_memories = [m for m in memories if m.get('source') == 'consolidated']
                
                # Сначала консолидированные (долгосрочная память)
                if consolidated_memories:
                    context_parts.append("Долгосрочные воспоминания:")
                    for mem in consolidated_memories[:2]:
                        emotion_info = f"({mem['emotion_type']}: {mem['emotional_intensity']:.1f})" if mem.get('emotion_type') else ""
                        context_parts.append(f"- {mem['content']} {emotion_info}")
                
                # Потом обычные (краткосрочная память)
                if regular_memories:
                    context_parts.append("Недавние воспоминания:")
                    for mem in regular_memories[:3]:
                        emotion_info = f"({mem['emotion_type']}: {mem['emotional_intensity']:.1f})" if mem.get('emotion_type') else ""
                        context_parts.append(f"- {mem['content']} {emotion_info}")
            
            if recent_convs:
                context_parts.append("\nНЕДАВНИЕ ДИАЛОГИ:")
                for conv in recent_convs[-2:]:  # Последние 2
                    context_parts.append(f"Пользователь: {conv['user_message']}")
                    # Если это многосообщенческий ответ, показываем только первое
                    ai_response = conv['ai_response'].split('||')[0].strip() if '||' in conv['ai_response'] else conv['ai_response']
                    context_parts.append(f"Ты: {ai_response}")
            
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