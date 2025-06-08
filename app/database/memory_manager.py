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
    """Менеджер с поддержкой эмоциональной памяти"""
    
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
                    memory_id = row[0] if len(row) > 7 else None
                    if memory_id:
                        cursor.execute("""
                            UPDATE memories 
                            SET access_count = access_count + 1,
                                last_accessed = ?
                            WHERE id = ?
                        """, (datetime.now().isoformat(), memory_id))
                    
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
                        context_parts.append(f"- {mem['content']}")
                
                # Потом обычные (краткосрочная память)
                if regular_memories:
                    context_parts.append("Недавние воспоминания:")
                    for mem in regular_memories[:3]:
                        context_parts.append(f"- {mem['content']}")
            
            if recent_convs:
                context_parts.append("\nНЕДАВНИЕ ДИАЛОГИ:")
                for conv in recent_convs[-2:]:
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
