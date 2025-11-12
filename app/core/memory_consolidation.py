# Улучшенная система памяти с эмоциональным интеллектом

import asyncio
import logging
import sqlite3
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

class EmotionalMemoryConsolidator:
    """Система памяти с эмоциональным интеллектом и динамическими порогами"""
    
    def __init__(self, db_path: str, api_manager, config: Dict):
        self.db_path = db_path
        self.api_manager = api_manager  # Теперь используем manager
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Эмоциональные модификаторы памяти
        self.emotion_memory_impact = {
            "joy": 1.5,         # Радостные моменты запоминаются ярче
            "love": 1.8,        # Любовь - самые сильные воспоминания
            "excitement": 1.3,  # Возбуждение усиливает память
            "surprise": 1.4,    # Неожиданное лучше запоминается
            "anger": 1.2,       # Сильные негативные эмоции тоже важны
            "sadness": 1.1,     # Грусть умеренно усиливает память
            "fear": 1.6,        # Страх - эволюционно важен для выживания
            "disgust": 0.8,     # Отвращение склонны забывать
            "calm": 1.0,        # Нейтральный базовый уровень
            "boredom": 0.6      # Скучное быстро забывается
        }
        
        # Расписание консолидации (дни -> уровень)
        self.consolidation_schedule = {
            1: "immediate",     # 1 день - немедленная обработка
            5: "short_term",    # 5 дней - первая консолидация
            30: "medium_term",  # 30 дней - средняя консолидация
            90: "long_term",    # 90 дней - долгосрочная память
            365: "lifetime"     # 1 год - пожизненные воспоминания
        }
    
    async def run_emotional_consolidation_cycle(self):
        """Основной цикл эмоциональной консолидации памяти"""
        self.logger.info("🧠💕 Запуск эмоциональной консолидации памяти...")
        
        try:
            # Получаем контекст пользователя для динамических порогов
            user_context = await self._analyze_user_context()
            
            # Консолидируем память разных уровней
            for days, level in self.consolidation_schedule.items():
                await self._consolidate_emotional_memories(days, level, user_context)
            
            # Архивируем старые воспоминания (не удаляем!)
            await self._archive_old_memories(user_context)
            
            # Обновляем частоту доступа
            await self._update_access_patterns()
            
            self.logger.info("✅ Эмоциональная консолидация завершена")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка эмоциональной консолидации: {e}")
    
    async def _analyze_user_context(self) -> Dict[str, Any]:
        """Анализирует контекст пользователя для динамических порогов"""
        
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Активность пользователя (сообщений за последнюю неделю)
                week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute("""
                    SELECT COUNT(*) FROM conversations 
                    WHERE timestamp >= ?
                """, (week_ago,))
                
                weekly_activity = cursor.fetchone()[0] or 0
                
                # Средняя эмоциональная интенсивность
                cursor.execute("""
                    SELECT AVG(emotional_intensity), AVG(importance)
                    FROM memories 
                    WHERE created_at >= ? AND emotional_intensity IS NOT NULL
                """, (week_ago,))
                
                result = cursor.fetchone()
                avg_emotion = result[0] if result[0] else 5.0
                avg_importance = result[1] if result[1] else 5.0
                
                # Стадия отношений (из character_loader)
                relationship_stage = self._get_relationship_stage()
                
                # Общий эмоциональный фон
                cursor.execute("""
                    SELECT emotion_type, COUNT(*) 
                    FROM memories 
                    WHERE created_at >= ? AND emotion_type IS NOT NULL
                    GROUP BY emotion_type
                    ORDER BY COUNT(*) DESC
                """, (week_ago,))
                
                dominant_emotions = dict(cursor.fetchall())
                
                return {
                    "weekly_activity": weekly_activity,
                    "avg_emotional_intensity": avg_emotion,
                    "avg_importance": avg_importance,
                    "relationship_stage": relationship_stage,
                    "dominant_emotions": dominant_emotions,
                    "activity_level": self._calculate_activity_level(weekly_activity)
                }
                
        except Exception as e:
            self.logger.error(f"Ошибка анализа контекста: {e}")
            return {
                "weekly_activity": 10,
                "avg_emotional_intensity": 5.0,
                "avg_importance": 5.0,
                "relationship_stage": "развитие",
                "dominant_emotions": {},
                "activity_level": "medium"
            }
    
    def _calculate_activity_level(self, weekly_messages: int) -> str:
        """Определяет уровень активности пользователя"""
        if weekly_messages > 50:
            return "high"
        elif weekly_messages > 20:
            return "medium"
        elif weekly_messages > 5:
            return "low"
        else:
            return "minimal"
    
    def _get_relationship_stage(self) -> str:
        """Получает стадию отношений из character_loader"""
        try:
            from .character_loader import character_loader
            character = character_loader.get_current_character()
            
            if character:
                relationship = character.get('current_relationship', {})
                stage = relationship.get('stage', 'развитие')
                intimacy = relationship.get('intimacy_level', 5)
                
                # Уточняем стадию по уровню близости
                if intimacy <= 3:
                    return "знакомство"
                elif intimacy <= 6:
                    return "дружба"
                elif intimacy <= 8:
                    return "близость"
                else:
                    return "глубокие_отношения"
            
            return "развитие"
            
        except Exception:
            return "развитие"
    
    def _calculate_dynamic_threshold(self, level: str, user_context: Dict) -> float:
        """Рассчитывает динамический порог важности"""
        
        # Базовые пороги
        base_thresholds = {
            "immediate": 3.0,
            "short_term": 4.0,
            "medium_term": 6.0,
            "long_term": 7.5,
            "lifetime": 9.0
        }
        
        threshold = base_thresholds.get(level, 5.0)
        
        # Модификации на основе контекста
        activity_level = user_context.get("activity_level", "medium")
        relationship_stage = user_context.get("relationship_stage", "развитие")
        avg_emotion = user_context.get("avg_emotional_intensity", 5.0)
        
        # Активные пользователи - запоминаем больше
        if activity_level == "high":
            threshold -= 1.0
        elif activity_level == "low":
            threshold += 0.5
        elif activity_level == "minimal":
            threshold += 1.0
            
        # В начале отношений всё важнее
        if relationship_stage == "знакомство":
            threshold -= 1.5
        elif relationship_stage == "дружба":
            threshold -= 0.5
        elif relationship_stage == "глубокие_отношения":
            threshold += 0.5  # Более избирательны в долгих отношениях
        
        # Эмоционально активные периоды
        if avg_emotion > 7.0:
            threshold -= 0.5
        elif avg_emotion < 3.0:
            threshold += 0.5
        
        # Никогда не опускаемся ниже минимума
        return max(1.0, threshold)
    
    async def _consolidate_emotional_memories(self, days_old: int, level: str, user_context: Dict):
        """Консолидация с учётом эмоций"""
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Динамический порог важности
        importance_threshold = self._calculate_dynamic_threshold(level, user_context)
        
        memories_to_consolidate = self._get_emotional_memories_for_consolidation(
            cutoff_date, level, importance_threshold
        )
        
        if not memories_to_consolidate:
            return
        
        self.logger.info(f"💕 Эмоциональная консолидация {len(memories_to_consolidate)} воспоминаний уровня {level} (порог: {importance_threshold:.1f})")
        
        # Группируем по эмоциональным контекстам
        grouped_memories = self._group_by_emotional_context(memories_to_consolidate)
        
        for group_key, group_memories in grouped_memories.items():
            try:
                consolidated = await self._emotionally_compress_memories(group_memories, level, user_context)
                
                if consolidated:
                    await self._save_emotional_consolidated_memory(group_memories, consolidated, level, user_context)
                    
            except Exception as e:
                self.logger.error(f"Ошибка эмоциональной консолидации группы {group_key}: {e}")
    
    def _get_emotional_memories_for_consolidation(self, cutoff_date: datetime, level: str, threshold: float) -> List[Dict]:
        """Получает воспоминания с учётом эмоциональной важности"""
        
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Сложная формула важности с эмоциями
                cursor.execute("""
                    SELECT id, memory_type, content, importance, created_at,
                           emotional_intensity, emotion_type, access_count,
                           consolidation_level, last_consolidated,
                           (importance + COALESCE(emotional_intensity * 0.3, 0) + COALESCE(access_count * 0.1, 0)) as total_importance
                    FROM memories 
                    WHERE created_at <= ? 
                    AND (consolidation_level IS NULL OR consolidation_level != ?)
                    AND (importance + COALESCE(emotional_intensity * 0.3, 0) + COALESCE(access_count * 0.1, 0)) >= ?
                    AND is_deeply_archived != 1
                    ORDER BY total_importance DESC, created_at ASC
                """, (cutoff_date.isoformat(), level, threshold))
                
                memories = []
                for row in cursor.fetchall():
                    memories.append({
                        "id": row[0],
                        "memory_type": row[1],
                        "content": row[2],
                        "importance": row[3],
                        "created_at": row[4],
                        "emotional_intensity": row[5] or 5.0,
                        "emotion_type": row[6] or "calm",
                        "access_count": row[7] or 0,
                        "consolidation_level": row[8],
                        "last_consolidated": row[9],
                        "total_importance": row[10]
                    })
                
                return memories
                
        except Exception as e:
            self.logger.error(f"Ошибка получения эмоциональных воспоминаний: {e}")
            return []
    
    def _group_by_emotional_context(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """Группирует воспоминания по эмоциональному контексту"""
        
        groups = {}
        
        for memory in memories:
            # Группируем по дате, типу эмоции и важности
            date_key = memory["created_at"][:10]  # YYYY-MM-DD
            emotion_type = memory["emotion_type"]
            emotion_intensity = memory["emotional_intensity"]
            
            # Определяем группу эмоциональной интенсивности
            if emotion_intensity >= 8:
                intensity_group = "high"
            elif emotion_intensity >= 6:
                intensity_group = "medium"
            else:
                intensity_group = "low"
            
            group_key = f"{date_key}_{emotion_type}_{intensity_group}_{memory['memory_type']}"
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(memory)
        
        return groups
    
    async def _emotionally_compress_memories(self, memories: List[Dict], level: str, user_context: Dict) -> str:
        """Сжимает воспоминания с учётом эмоционального контекста"""
        
        if not memories:
            return ""
        
        # Анализируем эмоциональный контекст группы
        emotions = [m["emotion_type"] for m in memories]
        avg_intensity = sum(m["emotional_intensity"] for m in memories) / len(memories)
        dominant_emotion = max(set(emotions), key=emotions.count)
        
        # Подготавливаем текст с эмоциональными метками
        memory_texts = []
        for memory in memories:
            emotion_marker = f"[{memory['emotion_type']}:{memory['emotional_intensity']:.1f}]"
            access_marker = f"[доступ:{memory['access_count']}]" if memory['access_count'] > 3 else ""
            memory_texts.append(f"{emotion_marker}{access_marker} {memory['content']}")
        
        full_text = "\n".join(memory_texts)
        
        # Создаём эмоционально-адаптивный промпт
        compression_prompt = self._build_emotional_compression_prompt(level, dominant_emotion, avg_intensity, user_context)
        
        try:
            # ИЗМЕНЕНО: Используем analytics API для консолидации
            from .multi_api_manager import APIUsageType
            
            response = await self.api_manager.make_request(
                APIUsageType.ANALYTICS,  # Используем analytics пул
                model=self.config.get('ai', {}).get('model', 'deepseek/deepseek-chat'),
                messages=[
                    {"role": "system", "content": compression_prompt},
                    {"role": "user", "content": f"Воспоминания для эмоциональной консолидации:\n{full_text}"}
                ],
                max_tokens=250,
                temperature=0.2
            )
            
            compressed = response.choices[0].message.content.strip()
            
            # Добавляем эмоциональные метаданные к сжатой памяти
            emotional_summary = f"[Эмоциональный контекст: {dominant_emotion}, интенсивность: {avg_intensity:.1f}] {compressed}"
            
            self.logger.debug(f"Эмоциональное сжатие: {len(full_text)} -> {len(emotional_summary)} символов")
            return emotional_summary
            
        except Exception as e:
            self.logger.error(f"Ошибка эмоционального сжатия: {e}")
            return ""
    
    def _build_emotional_compression_prompt(self, level: str, dominant_emotion: str, avg_intensity: float, user_context: Dict) -> str:
        """Создаёт эмоционально-адаптивный промпт для сжатия"""
        
        relationship_stage = user_context.get("relationship_stage", "развитие")
        
        base_prompt = f"""Ты система эмоциональной памяти AI-компаньона в отношениях на стадии "{relationship_stage}".
Консолидируешь воспоминания с доминирующей эмоцией "{dominant_emotion}" (интенсивность {avg_intensity:.1f}).

ПРИНЦИПЫ ЭМОЦИОНАЛЬНОЙ КОНСОЛИДАЦИИ:
• Сохраняй эмоциональную окраску воспоминаний
• Учитывай что эмоционально яркие моменты важнее обычных фактов
• Помни о развитии отношений и личностном росте
• Сохраняй уникальные черты личности пользователя"""
        
        level_specific = {
            "immediate": "Первичная обработка: сохрани все эмоции и детали, убери только повторы.",
            
            "short_term": f"""Краткосрочная консолидация: 
• Сохрани основные эмоциональные моменты
• Убери мелкие детали, но оставь то что влияет на отношения
• Особое внимание эмоции "{dominant_emotion}" - она была важна для пользователя""",

            "medium_term": f"""Среднесрочная консолидация:
• Сжми до ключевых эмоциональных паттернов
• Сохрани как эмоция "{dominant_emotion}" повлияла на отношения  
• Убери конкретные детали, оставь эмоциональную суть""",

            "long_term": f"""Долгосрочная консолидация:
• Создай эмоциональную сводку самого важного
• Как эта эмоция "{dominant_emotion}" характеризует пользователя?
• Максимальное сжатие с сохранением эмоциональной связи""",

            "lifetime": f"""Пожизненная память:
• Только самые важные эмоциональные вехи отношений
• Ключевые черты личности через эмоцию "{dominant_emotion}"
• Фундаментальные моменты, определившие отношения"""
        }
        
        # Дополнительные инструкции на основе эмоции
        emotion_instructions = {
            "love": "Особое внимание моментам нежности и привязанности - они основа отношений",
            "joy": "Сохрани источники радости - что делает пользователя счастливым",
            "excitement": "Отметь что вызывает у пользователя энтузиазм и интерес", 
            "anger": "Запомни триггеры конфликтов - важно для предотвращения проблем",
            "sadness": "Сохрани что расстраивает пользователя - для поддержки в будущем",
            "fear": "Отметь страхи и беспокойства - для понимания и помощи",
            "surprise": "Запомни что удивляет пользователя - для будущих приятных моментов"
        }
        
        emotion_instruction = emotion_instructions.get(dominant_emotion, "Сохрани эмоциональную окраску момента")
        
        return f"{base_prompt}\n\n{level_specific.get(level, '')}\n\nСПЕЦИАЛЬНО ДЛЯ ЭМОЦИИ: {emotion_instruction}"
    
    async def _save_emotional_consolidated_memory(self, original_memories: List[Dict], 
                                                consolidated_text: str, level: str, user_context: Dict):
        """Сохраняет эмоционально консолидированную память"""
        
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Рассчитываем сводную эмоциональную информацию
                emotions = [m["emotion_type"] for m in original_memories]
                avg_intensity = sum(m["emotional_intensity"] for m in original_memories) / len(original_memories)
                dominant_emotion = max(set(emotions), key=emotions.count)
                max_importance = max(m["importance"] for m in original_memories)
                total_access = sum(m["access_count"] for m in original_memories)
                
                # Применяем эмоциональный модификатор к важности
                emotion_boost = self.emotion_memory_impact.get(dominant_emotion, 1.0)
                final_importance = min(10.0, max_importance * emotion_boost)
                
                # Создаём консолидированную запись с эмоциональными метаданными
                cursor.execute("""
                    INSERT INTO memories 
                    (character_id, memory_type, content, importance, created_at,
                     emotional_intensity, emotion_type, access_count,
                     consolidation_level, last_consolidated, is_consolidated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1,  # character_id
                    "emotional_consolidated",
                    consolidated_text,
                    final_importance,
                    datetime.now().isoformat(),
                    avg_intensity,
                    dominant_emotion,
                    total_access,
                    level,
                    datetime.now().isoformat(),
                    True
                ))
                
                # Архивируем оригинальные воспоминания (не удаляем!)
                original_ids = [str(m["id"]) for m in original_memories]
                placeholders = ",".join(["?" for _ in original_ids])
                
                cursor.execute(f"""
                    UPDATE memories 
                    SET consolidation_level = ?, 
                        last_consolidated = ?,
                        is_archived = ?,
                        access_difficulty = 3
                    WHERE id IN ({placeholders})
                """, [level, datetime.now().isoformat(), True] + original_ids)
                
                conn.commit()
                
                self.logger.info(f"💾💕 Сохранена эмоциональная память: {dominant_emotion} (важность: {final_importance:.1f})")
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения эмоциональной памяти: {e}")
    
    async def _archive_old_memories(self, user_context: Dict):
        """Архивирует старые воспоминания (не удаляет!)"""
        
        # Более гибкие сроки архивирования
        activity_level = user_context.get("activity_level", "medium")
        
        if activity_level == "high":
            archive_days = 365  # Активные пользователи - архив через год
        elif activity_level == "medium":  
            archive_days = 180  # Средняя активность - полгода
        else:
            archive_days = 90   # Низкая активность - 3 месяца
        
        cutoff_date = datetime.now() - timedelta(days=archive_days)
        
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Архивируем вместо удаления
                cursor.execute("""
                    UPDATE memories 
                    SET is_deeply_archived = 1,
                        access_difficulty = 8
                    WHERE created_at <= ? 
                    AND importance < 6
                    AND emotional_intensity < 6 
                    AND access_count < 2
                    AND is_archived = 1
                    AND is_deeply_archived != 1
                """, (cutoff_date.isoformat(),))
                
                archived_count = cursor.rowcount
                conn.commit()
                
                if archived_count > 0:
                    self.logger.info(f"📦 Заархивировано {archived_count} старых воспоминаний (доступны но с низким приоритетом)")
                    
        except Exception as e:
            self.logger.error(f"Ошибка архивирования: {e}")
    
    async def _update_access_patterns(self):
        """Обновляет паттерны доступа к воспоминаниям"""
        
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Уменьшаем access_difficulty для часто используемых воспоминаний
                cursor.execute("""
                    UPDATE memories 
                    SET access_difficulty = CASE 
                        WHEN access_count > 10 THEN 1
                        WHEN access_count > 5 THEN 2  
                        WHEN access_count > 2 THEN 3
                        ELSE COALESCE(access_difficulty, 5)
                    END
                    WHERE access_count > 0
                """)
                
                # Постепенно увеличиваем сложность доступа к старым неиспользуемым воспоминаниям
                month_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute("""
                    UPDATE memories 
                    SET access_difficulty = COALESCE(access_difficulty, 5) + 1
                    WHERE last_accessed < ? 
                    AND access_count = 0
                    AND access_difficulty < 8
                """, (month_ago,))
                
                conn.commit()
                
                self.logger.debug("🔄 Паттерны доступа к памяти обновлены")
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления паттернов доступа: {e}")

# Функция для добавления эмоциональной информации в существующие воспоминания
async def enhance_existing_memories_with_emotions(db_path: str, ai_client, config: Dict):
    """Анализирует существующие воспоминания и добавляет эмоциональные метаданные"""
    
    try:
        with sqlite3.connect(db_path, timeout=30) as conn:
            cursor = conn.cursor()
            
            # Получаем воспоминания без эмоциональных меток
            cursor.execute("""
                SELECT id, content, importance 
                FROM memories 
                WHERE emotional_intensity IS NULL 
                AND content IS NOT NULL
                AND LENGTH(content) > 10
                LIMIT 50
            """)
            
            memories_to_enhance = cursor.fetchall()
            
            if not memories_to_enhance:
                return
            
            logging.info(f"🎭 Добавление эмоций к {len(memories_to_enhance)} существующим воспоминаниям...")
            
            for memory_id, content, importance in memories_to_enhance:
                try:
                    # Анализируем эмоциональный контекст
                    emotion_analysis = await analyze_memory_emotion(content, ai_client, config)
                    
                    if emotion_analysis:
                        cursor.execute("""
                            UPDATE memories 
                            SET emotional_intensity = ?,
                                emotion_type = ?
                            WHERE id = ?
                        """, (
                            emotion_analysis["intensity"],
                            emotion_analysis["emotion"],
                            memory_id
                        ))
                    
                except Exception as e:
                    logging.error(f"Ошибка анализа эмоций для памяти {memory_id}: {e}")
            
            conn.commit()
            logging.info("✅ Эмоциональное улучшение воспоминаний завершено")
            
    except Exception as e:
        logging.error(f"Ошибка улучшения воспоминаний: {e}")

async def analyze_memory_emotion(content: str, ai_client, config: Dict) -> Optional[Dict[str, Any]]:
    """Анализирует эмоциональный контекст воспоминания"""
    
    try:
        from .gemini_api_manager import APIUsageType

        prompt = """Проанализируй эмоциональный контекст этого воспоминания AI-компаньона.

Определи:
1. Основную эмоцию (joy, love, excitement, surprise, anger, sadness, fear, disgust, calm, boredom)
2. Интенсивность эмоции от 1 до 10

Ответь в формате: emotion_type:intensity
Например: joy:8 или sadness:3"""

        response = await ai_client.make_request(
            APIUsageType.ANALYTICS,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Воспоминание: {content}"}
            ]
        )
        
        result = response.choices[0].message.content.strip()
        
        # Парсим ответ
        if ":" in result:
            emotion, intensity_str = result.split(":", 1)
            emotion = emotion.strip().lower()
            
            try:
                intensity = float(intensity_str.strip())
                intensity = max(1.0, min(10.0, intensity))  # Ограничиваем диапазон
                
                return {
                    "emotion": emotion,
                    "intensity": intensity
                }
            except ValueError:
                pass
        
        return None
        
    except Exception as e:
        logging.error(f"Ошибка анализа эмоций: {e}")
        return None