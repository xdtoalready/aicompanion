"""
Векторный менеджер памяти на базе ChromaDB для семантического поиска
"""

import logging
import chromadb
from chromadb.config import Settings
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class VectorMemoryManager:
    """Менеджер векторной памяти с семантическим поиском"""

    def __init__(self, db_path: str = "data/chroma_memory"):
        self.logger = logging.getLogger(__name__)

        # Путь к ChromaDB
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Инициализируем ChromaDB клиент
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Создаём или получаем коллекции
        self.conversations_collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "История диалогов"}
        )

        self.memories_collection = self.client.get_or_create_collection(
            name="memories",
            metadata={"description": "Долгосрочные воспоминания"}
        )

        self.emotional_memories_collection = self.client.get_or_create_collection(
            name="emotional_memories",
            metadata={"description": "Эмоциональные воспоминания"}
        )

        self.logger.info(f"Vector memory initialized at: {self.db_path}")

    def add_conversation(self,
                        conversation_id: int,
                        user_message: str,
                        ai_response: str,
                        mood_before: str,
                        mood_after: str,
                        timestamp: str) -> bool:
        """Добавляет диалог в векторную память"""
        try:
            # Комбинируем user и AI сообщения для лучшего контекста
            combined_text = f"User: {user_message}\nAI: {ai_response}"

            # Метаданные
            metadata = {
                "conversation_id": conversation_id,
                "mood_before": mood_before,
                "mood_after": mood_after,
                "timestamp": timestamp,
                "type": "conversation"
            }

            # Добавляем в коллекцию
            self.conversations_collection.add(
                documents=[combined_text],
                metadatas=[metadata],
                ids=[f"conv_{conversation_id}"]
            )

            self.logger.debug(f"Added conversation {conversation_id} to vector memory")
            return True

        except Exception as e:
            self.logger.error(f"Error adding conversation to vector memory: {e}")
            return False

    def add_memory(self,
                   memory_id: int,
                   memory_type: str,
                   content: str,
                   importance: int,
                   created_at: str,
                   tags: List[str] = None) -> bool:
        """Добавляет воспоминание в векторную память"""
        try:
            metadata = {
                "memory_id": memory_id,
                "memory_type": memory_type,
                "importance": importance,
                "created_at": created_at,
                "tags": ",".join(tags) if tags else ""
            }

            self.memories_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[f"mem_{memory_id}"]
            )

            self.logger.debug(f"Added memory {memory_id} to vector memory")
            return True

        except Exception as e:
            self.logger.error(f"Error adding memory to vector memory: {e}")
            return False

    def add_emotional_memory(self,
                            memory_id: int,
                            content: str,
                            emotion_type: str,
                            emotional_intensity: float,
                            importance: int,
                            created_at: str) -> bool:
        """Добавляет эмоциональное воспоминание"""
        try:
            metadata = {
                "memory_id": memory_id,
                "emotion_type": emotion_type,
                "emotional_intensity": emotional_intensity,
                "importance": importance,
                "created_at": created_at
            }

            self.emotional_memories_collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[f"emem_{memory_id}"]
            )

            self.logger.debug(f"Added emotional memory {memory_id} to vector memory")
            return True

        except Exception as e:
            self.logger.error(f"Error adding emotional memory: {e}")
            return False

    def search_similar_conversations(self,
                                    query: str,
                                    limit: int = 5,
                                    min_relevance: float = 0.5) -> List[Dict[str, Any]]:
        """
        Ищет похожие диалоги по семантическому смыслу

        Args:
            query: поисковый запрос (обычно текущее сообщение пользователя)
            limit: максимальное количество результатов
            min_relevance: минимальный порог релевантности (0-1)

        Returns:
            Список найденных диалогов с метаданными
        """
        try:
            results = self.conversations_collection.query(
                query_texts=[query],
                n_results=limit
            )

            # Форматируем результаты
            formatted_results = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    # Расстояние ChromaDB (меньше = более похоже)
                    distance = results['distances'][0][i] if 'distances' in results else 0

                    # Преобразуем distance в similarity score (0-1)
                    # ChromaDB использует L2 distance, конвертируем в similarity
                    similarity = 1 / (1 + distance)

                    if similarity >= min_relevance:
                        formatted_results.append({
                            'content': doc,
                            'metadata': results['metadatas'][0][i],
                            'similarity': similarity,
                            'distance': distance
                        })

            self.logger.debug(f"Found {len(formatted_results)} similar conversations")
            return formatted_results

        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []

    def search_similar_memories(self,
                                query: str,
                                limit: int = 5,
                                memory_type: Optional[str] = None,
                                min_importance: int = 0) -> List[Dict[str, Any]]:
        """
        Ищет похожие воспоминания

        Args:
            query: поисковый запрос
            limit: максимальное количество результатов
            memory_type: фильтр по типу памяти (optional)
            min_importance: минимальная важность (0-10)
        """
        try:
            # Формируем фильтр метаданных
            where_filter = {}
            if memory_type:
                where_filter["memory_type"] = memory_type
            if min_importance > 0:
                where_filter["importance"] = {"$gte": min_importance}

            # Поиск
            results = self.memories_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter if where_filter else None
            )

            # Форматируем
            formatted_results = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    similarity = 1 / (1 + distance)

                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i],
                        'similarity': similarity,
                        'distance': distance
                    })

            self.logger.debug(f"Found {len(formatted_results)} similar memories")
            return formatted_results

        except Exception as e:
            self.logger.error(f"Error searching memories: {e}")
            return []

    def search_emotional_memories(self,
                                  query: str,
                                  emotion_type: Optional[str] = None,
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """Ищет эмоциональные воспоминания"""
        try:
            where_filter = {"emotion_type": emotion_type} if emotion_type else None

            results = self.emotional_memories_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )

            formatted_results = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if 'distances' in results else 0
                    similarity = 1 / (1 + distance)

                    formatted_results.append({
                        'content': doc,
                        'metadata': results['metadatas'][0][i],
                        'similarity': similarity
                    })

            return formatted_results

        except Exception as e:
            self.logger.error(f"Error searching emotional memories: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, int]:
        """Возвращает статистику по коллекциям"""
        return {
            "conversations": self.conversations_collection.count(),
            "memories": self.memories_collection.count(),
            "emotional_memories": self.emotional_memories_collection.count()
        }

    def clear_all_collections(self):
        """Очищает все коллекции (осторожно!)"""
        self.conversations_collection.delete(where={})
        self.memories_collection.delete(where={})
        self.emotional_memories_collection.delete(where={})
        self.logger.warning("All vector collections cleared")


# Глобальный инстанс
_vector_memory_instance = None

def get_vector_memory_manager(db_path: str = "data/chroma_memory") -> VectorMemoryManager:
    """Получает глобальный инстанс VectorMemoryManager"""
    global _vector_memory_instance
    if _vector_memory_instance is None:
        _vector_memory_instance = VectorMemoryManager(db_path)
    return _vector_memory_instance
