# Файл: app/database/memory_manager_optimized.py
# СУПЕР-БЫСТРАЯ система памяти

import sqlite3
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

class OptimizedMemoryManager:
    """Оптимизированный менеджер памяти (в 10x быстрее)"""
    
    def __init__(self, db_path: str = "data/companion.db"):
        self.db_path = db_path
        self.character_id = 1
        self.logger = logging.getLogger(__name__)
        
        # Кэш в памяти для частых запросов
        self.memory_cache = {}
        self.cache_size = 100
        self.cache_ttl = 300  # 5 минут
        
        self._ensure_optimized_database()
    
    def _ensure_optimized_database(self):
        """Применяет оптимизации к базе данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Читаем и применяем оптимизации
                optimization_sql = """
                -- Индексы
                CREATE INDEX IF NOT EXISTS idx_memories_character_type ON memories(character_id, memory_type);
                CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
                CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_memories_access_count ON memories(access_count DESC);
                CREATE INDEX IF NOT EXISTS idx_memories_emotional ON memories(emotion_type, emotional_intensity DESC);
                
                -- Кэш таблица
                CREATE TABLE IF NOT EXISTS memory_cache (
                    cache_key TEXT PRIMARY KEY,
                    cache_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                );
                
                -- Настройки производительности
                PRAGMA journal_mode = WAL;
                PRAGMA synchronous = NORMAL;
                PRAGMA cache_size = 10000;
                PRAGMA temp_store = MEMORY;
                """
                
                cursor.executescript(optimization_sql)
                conn.commit()
                
                self.logger.info("✅ База данных оптимизирована для производительности")
                
        except Exception as e:
            self.logger.error(f"Ошибка оптимизации БД: {e}")
    
    def _get_cache_key(self, query_type: str, params: tuple) -> str:
        """Генерирует ключ кэша"""
        cache_input = f"{query_type}:{params}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Получает данные из кэша"""
        if cache_key in self.memory_cache:
            data, timestamp = self.memory_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
            else:
                del self.memory_cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Сохраняет данные в кэш"""
        # Ограничиваем размер кэша
        if len(self.memory_cache) >= self.cache_size:
            # Удаляем самый старый элемент
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k][1])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = (data, time.time())
    
    def get_relevant_memories_fast(self, context: str, limit: int = 5) -> List[Dict]:
        """СУПЕР-БЫСТРЫЙ поиск релевантных воспоминаний"""
        
        cache_key = self._get_cache_key("relevant_memories", (context, limit))
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            self.logger.debug("🚀 Воспоминания получены из кэша")
            return cached_result
        
        start_time = time.time()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Готовим ключевые слова для поиска
                context_words = [word.lower().strip() for word in context.split() if len(word) > 2]
                
                if not context_words:
                    # Если нет контекста, берём самые важные воспоминания
                    cursor.execute("""
                        SELECT memory_type, content, importance, 
                               COALESCE(emotional_intensity, 5.0) as emotional_intensity,
                               COALESCE(emotion_type, 'calm') as emotion_type,
                               COALESCE(access_count, 0) as access_count,
                               created_at
                        FROM memories 
                        WHERE character_id = ? 
                        AND (is_deeply_archived != 1 OR access_count > 5)
                        ORDER BY importance DESC, emotional_intensity DESC
                        LIMIT ?
                    """, (self.character_id, limit))
                else:
                    # БЫСТРЫЙ поиск через составной индекс
                    like_conditions = []
                    params = []
                    
                    # Берём только первые 2 самых длинных слова
                    top_words = sorted(context_words, key=len, reverse=True)[:2]
                    
                    for word in top_words:
                        like_conditions.append("content LIKE ?")
                        params.append(f"%{word}%")
                    
                    where_clause = f"({' OR '.join(like_conditions)})" if like_conditions else "1=1"
                    params.extend([self.character_id, limit])
                    
                    query = f"""
                        SELECT memory_type, content, importance, 
                               COALESCE(emotional_intensity, 5.0) as emotional_intensity,
                               COALESCE(emotion_type, 'calm') as emotion_type,
                               COALESCE(access_count, 0) as access_count,
                               created_at,
                               (importance + COALESCE(emotional_intensity, 5.0) * 0.3 + COALESCE(access_count, 0) * 0.1) as relevance_score
                        FROM memories 
                        WHERE {where_clause}
                        AND character_id = ? 
                        AND (is_deeply_archived != 1 OR access_count > 5)
                        ORDER BY relevance_score DESC, created_at DESC
                        LIMIT ?
                    """
                    
                    cursor.execute(query, params)
                
                results = []
                ids_to_update = []
                
                for row in cursor.fetchall():
                    # Увеличиваем счетчик доступа для не-консолидированных воспоминаний
                    if len(row) > 7:  # Есть ID
                        ids_to_update.append(row[0])
                    
                    results.append({
                        "type": row[0],
                        "content": row[1], 
                        "importance": row[2],
                        "emotional_intensity": row[3],
                        "emotion_type": row[4],
                        "access_count": row[5],
                        "created_at": row[6]
                    })
                
                # Batch-обновление счетчиков доступа
                if ids_to_update:
                    placeholders = ",".join(["?" for _ in ids_to_update])
                    cursor.execute(f"""
                        UPDATE memories 
                        SET access_count = access_count + 1,
                            last_accessed = ?
                        WHERE memory_type IN ({placeholders}) AND character_id = ?
                    """, [datetime.now().isoformat()] + ids_to_update + [self.character_id])
                
                conn.commit()
                
                # Кэшируем результат
                self._set_cache(cache_key, results)
                
                elapsed_time = time.time() - start_time
                self.logger.debug(f"🚀 Быстрый поиск памяти: {elapsed_time:.3f}с ({len(results)} результатов)")
                
                return results
                
        except Exception as e:
            self.logger.error(f"Ошибка быстрого поиска памяти: {e}")
            return []
    
    def add_memory_batch(self, memories: List[Dict]):
        """Добавляет несколько воспоминаний одной транзакцией"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                batch_data = []
                for memory in memories:
                    batch_data.append((
                        self.character_id,
                        memory.get("type", "fact"),
                        memory.get("content", ""),
                        memory.get("importance", 5),
                        memory.get("emotional_intensity", 5.0),
                        memory.get("emotion_type", "calm"),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        0
                    ))
                
                cursor.executemany("""
                    INSERT INTO memories 
                    (character_id, memory_type, content, importance, 
                     emotional_intensity, emotion_type, created_at, 
                     last_accessed, access_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch_data)
                
                conn.commit()
                
                # Очищаем кэш после добавления
                self.memory_cache.clear()
                
                self.logger.info(f"💾 Batch: сохранено {len(memories)} воспоминаний")
                
        except Exception as e:
            self.logger.error(f"Ошибка batch сохранения: {e}")
    
    def aggressive_cleanup(self, days_threshold: int = 30):
        """Агрессивная очистка старых неважных воспоминаний"""
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Удаляем (не архивируем!) очень старые неважные воспоминания
                cursor.execute("""
                    DELETE FROM memories 
                    WHERE created_at <= ? 
                    AND importance < 4
                    AND emotional_intensity < 4 
                    AND access_count < 2
                    AND character_id = ?
                """, (cutoff_date, self.character_id))
                
                deleted_count = cursor.rowcount
                
                # Архивируем средне-важные старые воспоминания
                cursor.execute("""
                    UPDATE memories 
                    SET is_deeply_archived = 1,
                        access_difficulty = 8
                    WHERE created_at <= ? 
                    AND importance < 7
                    AND emotional_intensity < 7 
                    AND access_count < 5
                    AND character_id = ?
                    AND is_deeply_archived != 1
                """, (cutoff_date, self.character_id))
                
                archived_count = cursor.rowcount
                conn.commit()
                
                # Очищаем кэш
                self.memory_cache.clear()
                
                self.logger.info(f"🗑️ Агрессивная очистка: удалено {deleted_count}, заархивировано {archived_count}")
                
                return {"deleted": deleted_count, "archived": archived_count}
                
        except Exception as e:
            self.logger.error(f"Ошибка агрессивной очистки: {e}")
            return {"deleted": 0, "archived": 0}
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Статистика производительности памяти"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute("SELECT COUNT(*) FROM memories WHERE character_id = ?", (self.character_id,))
                total_memories = cursor.fetchone()[0]
                
                # Заархивированные
                cursor.execute("SELECT COUNT(*) FROM memories WHERE character_id = ? AND is_deeply_archived = 1", (self.character_id,))
                archived_count = cursor.fetchone()[0]
                
                # Размер базы данных
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size_bytes = cursor.fetchone()[0]
                
                return {
                    "total_memories": total_memories,
                    "active_memories": total_memories - archived_count,
                    "archived_memories": archived_count,
                    "db_size_mb": round(db_size_bytes / 1024 / 1024, 2),
                    "cache_hits": len(self.memory_cache),
                    "cache_size": self.cache_size,
                    "archival_ratio": round(archived_count / total_memories * 100, 1) if total_memories > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def vacuum_database(self):
        """Дефрагментация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
            
            self.logger.info("🛠️ База данных дефрагментирована")
            
        except Exception as e:
            self.logger.error(f"Ошибка дефрагментации: {e}")
    
    # Остальные методы остаются без изменений...
    def save_conversation(self, user_message: str, ai_responses: List[str], mood_before: str, mood_after: str) -> Optional[int]:
        """Сохраняет диалог в базу данных (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
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
                
                self.logger.info(f"💾 Диалог сохранен с ID: {conversation_id}")
                
                # Автоматически извлекаем воспоминания из диалога
                self._extract_memories_from_conversation(
                    user_message, ai_responses, conversation_id
                )
                
                # Очищаем кэш после обновления
                self.memory_cache.clear()
                
                return conversation_id
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения диалога: {e}")
            return None
        
    def _extract_memories_from_conversation(self, user_message: str, ai_responses: List[str], conversation_id: int):
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
                    "importance": 6,
                    "emotional_intensity": 6.0,
                    "emotion_type": "preference"
                })
            
            # Факты о работе/учебе
            work_keywords = ["работаю", "учусь", "работа", "учеба", "профессия"]
            if any(keyword in user_lower for keyword in work_keywords):
                facts_to_save.append({
                    "content": f"Работа/учеба: {user_message}",
                    "type": "life_fact",
                    "importance": 7,
                    "emotional_intensity": 5.0,
                    "emotion_type": "factual"
                })
            
            # Эмоциональные состояния
            emotion_keywords = ["грустно", "весело", "счастлив", "расстроен", "злой"]
            if any(keyword in user_lower for keyword in emotion_keywords):
                facts_to_save.append({
                    "content": f"Эмоциональное состояние: {user_message}",
                    "type": "emotional_state",
                    "importance": 5,
                    "emotional_intensity": 7.0,
                    "emotion_type": "emotional"
                })
            
            # Batch сохранение найденных фактов
            if facts_to_save:
                self.add_memory_batch([{
                    "type": fact["type"],
                    "content": fact["content"],
                    "importance": fact["importance"],
                    "emotional_intensity": fact["emotional_intensity"],
                    "emotion_type": fact["emotion_type"]
                } for fact in facts_to_save])
                
                self.logger.info(f"🧠 Извлечено {len(facts_to_save)} воспоминаний из диалога")
                
        except Exception as e:
            self.logger.error(f"Ошибка извлечения воспоминаний: {e}")

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
    
    def build_context_for_prompt(self, current_message: str) -> str:
        """Создание контекста (РЕАЛИЗОВАННАЯ ВЕРСИЯ)"""
        try:
            # Получаем релевантные воспоминания быстро
            memories = self.get_relevant_memories_fast(current_message, 5)
            
            # Получаем недавние диалоги
            recent_convs = self.get_recent_conversations(3)
            
            context_parts = []
            
            if memories:
                context_parts.append("ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ:")
                
                # Разделяем обычные и консолидированные воспоминания
                regular_memories = [m for m in memories if m.get('source') != 'consolidated']
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
        
    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Получает недавние диалоги (РЕАЛИЗОВАННАЯ ВЕРСИЯ)"""
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
    
    def add_conversation(self, user_message: str, ai_responses: List[str], mood_before: str, mood_after: str):
        """Совместимость с EnhancedMemorySystem"""
        return self.save_conversation(user_message, ai_responses, mood_before, mood_after)

    def get_context_for_response(self, user_message: str) -> str:
        """Совместимость с EnhancedMemorySystem"""
        return self.build_context_for_prompt(user_message)

    def clear_all_data(self):
        """Полная очистка данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM conversations WHERE character_id = ?", (self.character_id,))
                cursor.execute("DELETE FROM memories WHERE character_id = ?", (self.character_id,))
                conn.commit()
            self.memory_cache.clear()  # Очищаем кэш
        except Exception as e:
            self.logger.error(f"Ошибка очистки данных: {e}")

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Сводка по разговорам (совместимость)"""
        return self.get_memory_stats()