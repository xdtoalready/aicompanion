# Продвинутая система памяти с приоритизацией и интеграцией с базой данных

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

class AdvancedMemorySystem:
    """Продвинутая система памяти с приоритизацией и интеграцией с базой данных"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.memories = []  # Кэш воспоминаний для быстрого доступа
        self.conversation_patterns = {}
        self.user_preferences = {}
        self.relationship_history = []
        self.logger = logging.getLogger(__name__)
        
        # Загружаем воспоминания из базы данных, если она доступна
        if self.db_manager:
            self._load_memories_from_db()
    
    def _load_memories_from_db(self):
        """Загрузка воспоминаний из базы данных"""
        try:
            # Получаем все воспоминания из базы данных
            db_memories = self.db_manager.get_relevant_memories("", 100)  # Пустой запрос для получения всех
            
            # Преобразуем в формат для кэша
            for memory in db_memories:
                self.memories.append({
                    "content": memory["content"],
                    "type": memory["type"],
                    "importance": memory["importance"],
                    "emotional_charge": 0.0,  # Значение по умолчанию
                    "timestamp": datetime.fromisoformat(memory["created_at"]) if isinstance(memory["created_at"], str) else memory["created_at"],
                    "access_count": 0,
                    "last_accessed": datetime.fromisoformat(memory["last_accessed"]) if isinstance(memory["last_accessed"], str) else memory["last_accessed"],
                    "decay_factor": 1.0,
                    "db_id": memory["id"]  # Сохраняем ID из базы данных
                })
            
            self.logger.info(f"Загружено {len(self.memories)} воспоминаний из базы данных")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки воспоминаний из базы данных: {e}")
    
    def add_memory(self, content: str, memory_type: str, importance: int, 
                   emotional_charge: float = 0.0, source_conversation_id: int = None):
        """Добавляет воспоминание с автоматической категоризацией"""
        
        memory = {
            "content": content,
            "type": memory_type,
            "importance": importance,
            "emotional_charge": emotional_charge,
            "timestamp": datetime.now(),
            "access_count": 0,
            "last_accessed": datetime.now(),
            "decay_factor": 1.0
        }
        
        # Добавляем в локальный кэш
        self.memories.append(memory)
        
        # Сохраняем в базу данных, если она доступна
        if self.db_manager:
            try:
                memory_id = self.db_manager.save_memory(
                    memory_type=memory_type,
                    content=content,
                    importance=importance,
                    source_conversation_id=source_conversation_id
                )
                
                if memory_id > 0:
                    memory["db_id"] = memory_id
                    self.logger.info(f"Воспоминание сохранено в базу данных, ID={memory_id}")
                else:
                    self.logger.warning("Не удалось сохранить воспоминание в базу данных")
                    
            except Exception as e:
                self.logger.error(f"Ошибка сохранения воспоминания в базу данных: {e}")
        
        self._consolidate_memories()
    
    def _consolidate_memories(self):
        """Консолидация памяти - перенос важного в долгосрочную"""
        
        # Удаляем старые неважные воспоминания из кэша
        cutoff_time = datetime.now() - timedelta(days=7)
        self.memories = [
            m for m in self.memories 
            if m["timestamp"] > cutoff_time or m["importance"] >= 7
        ]
        
        # Применяем забывание
        for memory in self.memories:
            days_old = (datetime.now() - memory["timestamp"]).days
            memory["decay_factor"] = max(0.1, 1.0 - (days_old * 0.1))
    
    def get_relevant_memories(self, context: str, limit: int = 5) -> List[Dict]:
        """Получает релевантные воспоминания с учетом контекста"""
        
        # Если доступна база данных, используем её для поиска
        if self.db_manager and context:
            try:
                db_memories = self.db_manager.get_relevant_memories(context, limit)
                
                # Преобразуем в формат для возврата
                return db_memories
                
            except Exception as e:
                self.logger.error(f"Ошибка получения воспоминаний из базы данных: {e}")
                # Продолжаем с локальным поиском
        
        # Локальный поиск по ключевым словам
        context_words = set(context.lower().split())
        
        scored_memories = []
        for memory in self.memories:
            content_words = set(memory["content"].lower().split())
            overlap = len(context_words.intersection(content_words))
            
            # Скор: релевантность + важность + эмоциональная связь
            score = (
                overlap * 2 +
                memory["importance"] +
                abs(memory["emotional_charge"]) +
                memory["access_count"] * 0.1
            ) * memory["decay_factor"]
            
            scored_memories.append((score, memory))
        
        # Сортируем и возвращаем топ
        scored_memories.sort(reverse=True, key=lambda x: x[0])
        
        # Обновляем счетчики доступа
        for _, memory in scored_memories[:limit]:
            memory["access_count"] += 1
            memory["last_accessed"] = datetime.now()
        
        return [memory for _, memory in scored_memories[:limit]]
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Возвращает краткую сводку памяти для контекста"""
        
        # Группируем по типам
        by_type = {}
        for memory in self.memories:
            mem_type = memory["type"]
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(memory)
        
        # Берем самые важные из каждого типа
        summary = {}
        for mem_type, memories in by_type.items():
            sorted_memories = sorted(memories, 
                                   key=lambda m: m["importance"] * m["decay_factor"], 
                                   reverse=True)
            summary[mem_type] = [m["content"] for m in sorted_memories[:3]]
        
        return summary
    
    def add_user_preference(self, preference: str, strength: float):
        """Добавляет предпочтение пользователя"""
        self.user_preferences[preference] = {
            "strength": strength,
            "discovered": datetime.now(),
            "confirmations": 1
        }
        
        # Сохраняем как воспоминание
        self.add_memory(
            content=f"Пользователь предпочитает: {preference}",
            memory_type="preference",
            importance=min(10, int(strength * 10)),
            emotional_charge=0.0
        )
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Возвращает профиль пользователя"""
        return {
            "preferences": self.user_preferences,
            "conversation_patterns": self.conversation_patterns,
            "relationship_stage": self._assess_relationship_stage()
        }
    
    def _assess_relationship_stage(self) -> str:
        """Оценивает стадию отношений с пользователем"""
        total_conversations = len([m for m in self.memories if m["type"] == "conversation"])
        
        if total_conversations < 5:
            return "знакомство"
        elif total_conversations < 20:
            return "дружеское общение"
        elif total_conversations < 50:
            return "близкое знакомство"
        else:
            return "долгие отношения"
    
    def update_conversation_pattern(self, user_message: str, ai_response: str):
        """Обновляет паттерны общения"""
        hour = datetime.now().hour
        
        if hour not in self.conversation_patterns:
            self.conversation_patterns[hour] = {
                "frequency": 0,
                "user_mood_indicators": [],
                "typical_topics": []
            }
        
        self.conversation_patterns[hour]["frequency"] += 1
        
        # Простой анализ настроения по ключевым словам
        positive_words = ["хорошо", "отлично", "рад", "счастлив", "весело"]
        negative_words = ["плохо", "грустно", "устал", "проблемы", "тяжело"]
        
        user_lower = user_message.lower()
        if any(word in user_lower for word in positive_words):
            self.conversation_patterns[hour]["user_mood_indicators"].append("positive")
        elif any(word in user_lower for word in negative_words):
            self.conversation_patterns[hour]["user_mood_indicators"].append("negative")
    
    def get_optimal_contact_times(self) -> List[int]:
        """Определяет оптимальное время для контакта"""
        if not self.conversation_patterns:
            return [9, 13, 19]  # дефолтные часы
        
        # Сортируем часы по частоте общения
        sorted_hours = sorted(self.conversation_patterns.items(), 
                            key=lambda x: x[1]["frequency"], reverse=True)
        
        return [hour for hour, _ in sorted_hours[:3]]
    
    def extract_facts_from_conversation(self, user_message: str, ai_responses: List[str], 
                                      conversation_id: Optional[int] = None):
        """Извлекает факты из диалога и сохраняет их как воспоминания"""
        
        # Простое извлечение фактов по ключевым словам
        facts_found = []
        
        # Ключевые слова для фактов
        if any(word in user_message.lower() for word in ["работаю", "работа", "job"]):
            facts_found.append(("работа пользователя", "fact", 6))
        
        if any(word in user_message.lower() for word in ["люблю", "нравится", "обожаю"]):
            facts_found.append((f"предпочтения: {user_message[:100]}", "preference", 5))
        
        if any(word in user_message.lower() for word in ["грустно", "плохо", "устал"]):
            facts_found.append(("эмоциональное состояние пользователя", "emotion", 4))
        
        # Проверяем упоминания манги и аниме
        if any(word in user_message.lower() for word in ["манга", "аниме", "manga", "anime"]):
            facts_found.append((f"интересуется мангой/аниме: {user_message[:100]}", "interest", 7))
        
        # Сохраняем найденные факты
        for content, memory_type, importance in facts_found:
            self.add_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                emotional_charge=0.0,
                source_conversation_id=conversation_id
            )
        
        return len(facts_found)

