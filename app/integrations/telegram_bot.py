# Интеграция с Telegram Bot API с поддержкой многосообщенческих ответов

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
from app.core.character_loader import character_loader

from app.core.companion import RealisticAICompanion

class TelegramCompanion(RealisticAICompanion):
    """AI-компаньон с интеграцией Telegram и многосообщенческими ответами"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Telegram настройки
        self.bot_token = config['integrations']['telegram']['bot_token']
        self.allowed_users = set(config['integrations']['telegram'].get('allowed_users', []))
        
        # Telegram Application
        self.app = Application.builder().token(self.bot_token).build()
        self.setup_handlers()
        
        # Состояние пользователей
        self.user_states = {}
        
        # Инициализируем typing indicator с telegram app
        self.typing_indicator.telegram_app = self.app
        
        self.logger.info("Telegram интеграция с многосообщенческими ответами инициализирована")
    
    def setup_handlers(self):
        """Настройка обработчиков Telegram"""
        
        # Команды
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))

        # Дополнительные команды для персонажа
        self.app.add_handler(CommandHandler("characters", self.characters_command))
        self.app.add_handler(CommandHandler("switch", self.switch_command))
        self.app.add_handler(CommandHandler("charinfo", self.charinfo_command))
        self.app.add_handler(CommandHandler("relationship", self.relationship_command))

        # Для коснолидации памяти (проверка)
        self.app.add_handler(CommandHandler("emotion_stats", self.emotion_stats_command))
        self.app.add_handler(CommandHandler("analyze_emotions", self.analyze_emotions_command))
        self.app.add_handler(CommandHandler("emotional_search", self.emotional_search_command))
        
        # Проверка состояния расписания
        self.app.add_handler(CommandHandler("schedule", self.schedule_command))

        # Команды для отладки (будут убраны позже)
        if self.commands_enabled:
            self.app.add_handler(CommandHandler("status", self.status_command))
            self.app.add_handler(CommandHandler("mood", self.mood_command))
            self.app.add_handler(CommandHandler("memories", self.memories_command))
            self.app.add_handler(CommandHandler("stats", self.stats_command))
            self.app.add_handler(CommandHandler("dbcheck", self.dbcheck_command))
            self.app.add_handler(CommandHandler("clearmem", self.clear_memory_command))

        # Обработка текстовых сообщений
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработка ошибок
        self.app.add_error_handler(self.error_handler)

    async def memory_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика системы памяти"""
        if not self.commands_enabled:
            return
        
        try:
            import sqlite3
            db_path = self.enhanced_memory.db_manager.db_path
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Общая статистика
                cursor.execute("SELECT COUNT(*) FROM memories")
                total_memories = cursor.fetchone()[0]
                
                # Консолидированные воспоминания
                cursor.execute("SELECT COUNT(*) FROM memories WHERE is_consolidated = 1")
                consolidated_count = cursor.fetchone()[0]
                
                # Архивированные
                cursor.execute("SELECT COUNT(*) FROM memories WHERE is_archived = 1")
                archived_count = cursor.fetchone()[0]
                
                # По уровням консолидации
                cursor.execute("""
                    SELECT consolidation_level, COUNT(*) 
                    FROM memories 
                    WHERE consolidation_level IS NOT NULL 
                    GROUP BY consolidation_level
                """)
                levels = cursor.fetchall()
                
                text = f"🧠 **СТАТИСТИКА ПАМЯТИ**\n\n"
                text += f"📊 **Общая статистика:**\n"
                text += f"• Всего воспоминаний: {total_memories}\n"
                text += f"• Консолидированных: {consolidated_count}\n" 
                text += f"• Архивированных: {archived_count}\n\n"
                
                if levels:
                    text += f"🔄 **По уровням консолидации:**\n"
                    for level, count in levels:
                        text += f"• {level}: {count}\n"
                
                # Размер памяти в токенах (приблизительно)
                cursor.execute("SELECT SUM(LENGTH(content)) FROM memories WHERE is_archived != 1")
                total_chars = cursor.fetchone()[0] or 0
                approx_tokens = total_chars // 4  # Приблизительно 4 символа = 1 токен
                
                text += f"\n💾 **Объём памяти:**\n"
                text += f"• Символов: {total_chars:,}\n"
                text += f"• ≈ Токенов: {approx_tokens:,}\n"
                
                efficiency = (archived_count / total_memories * 100) if total_memories > 0 else 0
                text += f"• Эффективность сжатия: {efficiency:.1f}%"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения статистики: {e}")

    async def schedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать расписание персонажа"""
        if not self.commands_enabled:
            return
        
        activities = self.virtual_life.get_upcoming_activities(72)  # 3 дня
        
        if not activities:
            await update.message.reply_text(
                "📅 У меня пока нет конкретных планов!\n\n"
                "💡 Планы создаются автоматически или когда я их упоминаю в разговоре"
            )
            return
        
        text = "📅 **МОИ ПЛАНЫ НА БЛИЖАЙШЕЕ ВРЕМЯ:**\n\n"
        
        current_day = None
        for activity in activities[:10]:  # Показываем максимум 10
            activity_day = activity.start_time.strftime('%d.%m')
            
            if activity_day != current_day:
                text += f"**{activity.start_time.strftime('%d.%m (%A)')}:**\n"
                current_day = activity_day
            
            start_time = activity.start_time.strftime('%H:%M')
            end_time = activity.end_time.strftime('%H:%M')
            
            activity_emoji = {
                'cosplay': '🎭',
                'work': '💼', 
                'hobby': '🎨',
                'social': '👥',
                'rest': '😌'
            }.get(activity.activity_type, '📋')
            
            text += f"{activity_emoji} {start_time}-{end_time}: {activity.description}\n"
        
        text += f"\n💡 Всего запланировано: {len(activities)} активностей"
        
        await update.message.reply_text(text, parse_mode='Markdown')

    async def emotion_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика эмоциональной памяти"""
        if not self.commands_enabled:
            return
        
        try:
            import sqlite3
            db_path = self.enhanced_memory.db_manager.db_path
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Общая статистика эмоций
                cursor.execute("""
                    SELECT emotion_type, COUNT(*), AVG(emotional_intensity), AVG(importance)
                    FROM memories 
                    WHERE emotion_type IS NOT NULL AND is_deeply_archived != 1
                    GROUP BY emotion_type
                    ORDER BY COUNT(*) DESC
                """)
                
                emotion_stats = cursor.fetchall()
                
                text = "🎭 **ЭМОЦИОНАЛЬНАЯ ПАМЯТЬ**\n\n"
                
                if emotion_stats:
                    text += "📊 **Статистика по эмоциям:**\n"
                    for emotion, count, avg_intensity, avg_importance in emotion_stats[:6]:
                        emotion_emoji = {
                            'joy': '😊', 'love': '💕', 'excitement': '🎉', 
                            'surprise': '😲', 'calm': '😌', 'sadness': '😔',
                            'anger': '😠', 'fear': '😨'
                        }.get(emotion, '🎭')
                        
                        text += f"{emotion_emoji} **{emotion}**: {count} воспоминаний\n"
                        text += f"   Интенсивность: {avg_intensity:.1f}, Важность: {avg_importance:.1f}\n"
                    
                    # Топ эмоционально ярких воспоминаний
                    cursor.execute("""
                        SELECT content, emotion_type, emotional_intensity,
                            (importance + emotional_intensity * 0.3) as score
                        FROM memories 
                        WHERE emotional_intensity >= 7 AND is_deeply_archived != 1
                        ORDER BY score DESC
                        LIMIT 3
                    """)
                    
                    top_memories = cursor.fetchall()
                    if top_memories:
                        text += f"\n🌟 **Самые яркие моменты:**\n"
                        for content, emotion, intensity, score in top_memories:
                            emotion_emoji = {
                                'joy': '😊', 'love': '💕', 'excitement': '🎉'
                            }.get(emotion, '✨')
                            short_content = content[:40] + "..." if len(content) > 40 else content
                            text += f"{emotion_emoji} {short_content} ({intensity:.1f})\n"
                
                else:
                    text += "📝 Эмоциональные метки ещё добавляются...\n"
                    text += "💡 Система проанализирует воспоминания автоматически"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения эмоциональной статистики: {e}")

    async def analyze_emotions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Принудительный анализ эмоций для воспоминаний"""
        if not self.commands_enabled:
            return

        await update.message.reply_text("🎭 Запуск анализа эмоций для воспоминаний...")

        try:
            # Запускаем анализ эмоций
            await enhance_existing_memories_with_emotions(
                self.enhanced_memory.db_manager.db_path,
                self.ai_client,
                self.config
            )
            
            await update.message.reply_text(
                "✅ Анализ эмоций завершён!\n\n"
                "💡 Используйте /emotion_stats для просмотра результатов"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка анализа эмоций: {e}")

    async def emotional_search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поиск воспоминаний по эмоциям"""
        if not self.commands_enabled:
            return
        
        if not context.args:
            await update.message.reply_text(
                "🔍 **Поиск по эмоциям**\n\n"
                "Использование:\n"
                "• `/emotional_search joy` - радостные моменты\n"
                "• `/emotional_search love` - моменты любви\n"
                "• `/emotional_search excitement` - возбуждение\n"
                "• `/emotional_search calm` - спокойные моменты\n\n"
                "Доступные эмоции: joy, love, excitement, surprise, calm, sadness, anger, fear",
                parse_mode='Markdown'
            )
            return
        
        emotion_type = context.args[0].lower()
        
        try:
            emotional_memories = self.enhanced_memory.db_manager.get_emotional_memories(
                emotion_type=emotion_type, 
                min_intensity=6.0,
                limit=5
            )
            
            if emotional_memories:
                emotion_emoji = {
                    'joy': '😊', 'love': '💕', 'excitement': '🎉', 
                    'surprise': '😲', 'calm': '😌', 'sadness': '😔',
                    'anger': '😠', 'fear': '😨'
                }.get(emotion_type, '🎭')
                
                text = f"{emotion_emoji} **Воспоминания с эмоцией '{emotion_type}':**\n\n"
                
                for memory in emotional_memories:
                    intensity = memory['emotional_intensity']
                    content = memory['content']
                    short_content = content[:60] + "..." if len(content) > 60 else content
                    text += f"💫 **{intensity:.1f}/10** - {short_content}\n\n"
            else:
                text = f"🔍 Не найдено ярких воспоминаний с эмоцией '{emotion_type}'\n\n"
                text += "💡 Попробуйте другую эмоцию или подождите пока система проанализирует больше воспоминаний"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка поиска: {e}")

    async def characters_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать доступных персонажей"""
        if not self.commands_enabled:
            return
        
        available_chars = character_loader.get_available_characters()
        current_char = character_loader.get_current_character()
        current_name = current_char.get('name', 'Не загружен') if current_char else 'Не загружен'
        
        if not available_chars:
            await update.message.reply_text(
                "📂 Персонажи не найдены!\n\n"
                "💡 Создайте файлы персонажей в папке characters/\n"
                "Пример: characters/marin_kitagawa.json"
            )
            return
        
        text = f"👥 ДОСТУПНЫЕ ПЕРСОНАЖИ\n"
        text += f"🎭 Текущий: **{current_name}**\n\n"
        
        for i, char in enumerate(available_chars, 1):
            status = "✅" if char['name'] == current_name else "⭕"
            text += f"{status} `{char['id']}` - **{char['name']}**\n"
            text += f"   {char['description']}\n\n"
        
        text += "💡 Переключение: `/switch <id_персонажа>`\n"
        text += "📋 Информация: `/charinfo`"
        
        await update.message.reply_text(text, parse_mode='Markdown')

    async def switch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Переключение персонажа"""
        if not self.commands_enabled:
            return
        
        if not context.args:
            await update.message.reply_text(
                "❓ Укажите ID персонажа!\n\n"
                "Использование: `/switch marin_kitagawa`\n"
                "Доступные персонажи: `/characters`"
            )
            return
        
        new_character_id = context.args[0].lower()
        
        # Получаем информацию о старом персонаже
        old_char = character_loader.get_current_character()
        old_name = old_char.get('name', 'Неизвестный') if old_char else 'Никто'
        
        # Переключаемся
        success = character_loader.switch_character(new_character_id)
        
        if success:
            new_char = character_loader.get_current_character()
            new_name = new_char.get('name', 'Новый персонаж')
            
            # Создаем сообщения о переключении с учётом нового персонажа
            switch_messages = await self._generate_character_switch_response(old_name, new_name, new_char)
            
            # Отправляем уведомление с реалистичным печатанием
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            
            await self.send_telegram_messages_with_timing(
                chat_id=update.effective_chat.id,
                messages=switch_messages,
                current_state=current_state
            )
            
            # Обновляем AI клиент с новым персонажем
            self.optimized_ai.character_loader = character_loader
            
            self.logger.info(f"Персонаж переключён: {old_name} → {new_name}")
            
        else:
            await update.message.reply_text(
                f"❌ Не удалось переключиться на `{new_character_id}`\n\n"
                f"Проверьте что файл `characters/{new_character_id}.json` существует\n"
                f"Доступные персонажи: `/characters`",
                parse_mode='Markdown'
            )

    async def _generate_character_switch_response(self, old_name: str, new_name: str, new_character: dict) -> List[str]:
        """Генерирует сообщения о переключении персонажа"""
        
        if not new_character:
            return [f"Переключение на {new_name}... Привет! 😊"]
        
        # Получаем характерные черты нового персонажа
        personality = new_character.get('personality', {})
        key_traits = personality.get('key_traits', [])
        speech_style = new_character.get('speech', {}).get('style', 'дружелюбный')
        catchphrases = new_character.get('speech', {}).get('catchphrases', [])
        
        # Специальные сообщения для Марин Китагавы
        if 'марин' in new_name.lower() or 'китагава' in new_name.lower():
            return [
                "Ааа! Вау! 😍 Это что, смена персонажа?!",
                "Привееет! Я Марин Китагава! Обожаю косплей и аниме! ✨",
                "Ты будешь помогать мне с костюмами? Я так надеюсь! 💕",
                "Расскажи, что ты любишь! Может у нас общие интересы? 🎭"
            ]
        
        # Общий шаблон для других персонажей
        messages = [
            f"Привет! Теперь я {new_name}! 😊"
        ]
        
        if key_traits:
            trait = key_traits[0] if key_traits else "дружелюбная"
            messages.append(f"Я {trait} и очень рада знакомству!")
        
        if catchphrases:
            phrase = catchphrases[0]
            messages.append(f"{phrase} ✨")
        
        messages.append("Расскажи о себе! Хочется узнать тебя лучше! 💕")
        
        return messages
    
    # Добавляем новый метод:
    async def dbcheck_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка состояния базы данных"""
        if not self.commands_enabled:
            return
            
        try:
            # Получаем статистику БД
            db_stats = self.get_database_stats()
            
            if db_stats.get("database_enabled"):
                status_text = f"""🗄️ Статус базы данных:

    ✅ База данных: Активна
    💬 Недавних диалогов: {db_stats['recent_conversations']}
    🧠 Воспоминаний: {db_stats['total_memories']}
    🕒 Последний диалог: {db_stats.get('last_conversation', 'Нет')}

    📋 Контекст работает: Да
    💾 Память сохраняется: Да"""
            else:
                status_text = f"""❌ Проблема с базой данных:

    {db_stats.get('error', 'Неизвестная ошибка')}

    🔧 Рекомендации:
    1. Проверьте что файл companion.db существует
    2. Запустите: python scripts/setup_db.py
    3. Перезапустите бота"""
        
            # Также проверяем последний контекст
            if hasattr(self, 'enhanced_memory'):
                test_context = self.enhanced_memory.get_context_for_response("тест")
                if test_context and test_context != "Новое знакомство":
                    status_text += f"\n\n🔍 Пример контекста:\n{test_context[:150]}..."
                else:
                    status_text += "\n\n⚠️ Контекст пустой (нормально для первого запуска)"
                    
        except Exception as e:
            status_text = f"❌ Ошибка проверки БД: {e}"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def clear_memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Полная очистка данных о пользователе"""
        if not self.commands_enabled:
            return

        try:
            self.enhanced_memory.clear_all_data()
            await update.message.reply_text("🗑️ Память очищена")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка очистки памяти: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user_id = update.effective_user.id
        
        # Проверка разрешенных пользователей
        if self.allowed_users and user_id not in self.allowed_users:
            await update.message.reply_text(
                "Извини, но я общаюсь только с определенными людьми 😊"
            )
            return
        
        # Инициализация состояния пользователя
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                "first_contact": True,
                "last_activity": None
            }
        
        # НОВОЕ: Многосообщенческое приветствие
        welcome_messages = [
            "Привет! 😊",
            "Я твой AI-компаньон, и я не просто отвечаю на сообщения...",
            "У меня есть настроения, планы и желания! Иногда я сама буду тебе писать 💭",
            "Просто общайся со мной как с живым человеком! ✨"
        ]
        
        # Отправляем приветствие с реалистичными паузами
        current_state = await self.optimized_ai.get_simple_mood_calculation(self.psychological_core)
        
        await self.send_telegram_messages_with_timing(
            chat_id=update.effective_chat.id,
            messages=welcome_messages,
            current_state=current_state
        )
        
        self.logger.info(f"Новый пользователь начал общение: {user_id}")

    async def charinfo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о текущем персонаже"""
        if not self.commands_enabled:
            return
        
        character = character_loader.get_current_character()
        
        if not character:
            await update.message.reply_text(
                "❌ Персонаж не загружен!\n\n"
                "Загрузите персонажа: `/characters`"
            )
            return
        
        # Базовая информация
        name = character.get('name', 'Неизвестно')
        age = character.get('age', 'Неизвестно')
        description = character.get('personality', {}).get('description', 'Нет описания')
        
        text = f"👤 **{name}** ({age} лет)\n"
        text += f"📝 {description.capitalize()}\n\n"
        
        # Черты характера
        key_traits = character.get('personality', {}).get('key_traits', [])
        if key_traits:
            text += f"🎭 **Черты характера:**\n"
            for trait in key_traits[:4]:  # Первые 4
                text += f"• {trait}\n"
            text += "\n"
        
        # Интересы
        interests = character.get('interests', [])
        if interests:
            text += f"❤️ **Интересы:**\n"
            text += f"{', '.join(interests[:5])}\n\n"
        
        # Отношения
        relationship = character.get('current_relationship', {})
        if relationship:
            rel_type = relationship.get('type', 'неопределенные')
            stage = relationship.get('stage', 'неизвестна')
            intimacy = relationship.get('intimacy_level', 0)
            
            text += f"💕 **Отношения:**\n"
            text += f"• Тип: {rel_type}\n"
            text += f"• Стадия: {stage}\n"
            text += f"• Близость: {intimacy}/10\n\n"
        
        # Стиль речи
        speech = character.get('speech', {})
        if speech:
            style = speech.get('style', 'обычный')
            text += f"💬 **Стиль речи:** {style}\n"
            
            catchphrases = speech.get('catchphrases', [])
            if catchphrases:
                text += f"🗣️ **Любимые фразы:**\n"
                for phrase in catchphrases[:3]:  # Первые 3
                    text += f"• \"{phrase}\"\n"
        
        text += f"\n📁 **ID файла:** `{character.get('id', 'unknown')}`"
        
        await update.message.reply_text(text, parse_mode='Markdown')

    async def relationship_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация об отношениях"""
        if not self.commands_enabled:
            return
        
        character = character_loader.get_current_character()
        
        if not character:
            await update.message.reply_text("❌ Персонаж не загружен!")
            return
        
        relationship = character.get('current_relationship', {})
        
        if not relationship:
            await update.message.reply_text("❌ Информация об отношениях недоступна!")
            return
        
        name = character.get('name', 'Персонаж')
        
        text = f"💕 **ОТНОШЕНИЯ С {name.upper()}**\n\n"
        
        # Основная информация
        rel_type = relationship.get('type', 'неопределенные')
        stage = relationship.get('stage', 'неизвестна')
        intimacy = relationship.get('intimacy_level', 0)
        
        text += f"💫 **Тип:** {rel_type}\n"
        text += f"🎭 **Стадия:** {stage}\n"
        text += f"❤️ **Уровень близости:** {intimacy}/10\n\n"
        
        # Предыстория
        backstory = relationship.get('backstory', '')
        if backstory:
            text += f"📖 **Как познакомились:**\n{backstory[:300]}"
            if len(backstory) > 300:
                text += "..."
            text += "\n\n"
        
        # Текущая динамика
        current_dynamic = relationship.get('current_dynamic', '')
        if current_dynamic:
            text += f"🌟 **Сейчас:**\n{current_dynamic[:200]}"
            if len(current_dynamic) > 200:
                text += "..."
            text += "\n\n"
        
        # Даты
        created_at = relationship.get('created_at', '')
        if created_at:
            try:
                from datetime import datetime
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                text += f"📅 **Начало отношений:** {created_date.strftime('%d.%m.%Y')}\n"
            except:
                pass
        
        # Совместные активности (если есть)
        shared_activities = character.get('default_relationship', {}).get('shared_activities', [])
        if shared_activities:
            text += f"\n🎯 **Что делаем вместе:**\n"
            for activity in shared_activities[:4]:
                text += f"• {activity}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')

    async def intimacy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Изменение уровня близости (только для отладки)"""
        if not self.commands_enabled:
            return
        
        if not context.args:
            await update.message.reply_text(
                "❓ Использование: `/intimacy <уровень>`\n"
                "Уровень от 1 до 10\n"
                "Например: `/intimacy 7`"
            )
            return
        
        try:
            new_level = int(context.args[0])
            if not 1 <= new_level <= 10:
                raise ValueError()
        except ValueError:
            await update.message.reply_text("❌ Уровень должен быть от 1 до 10!")
            return
        
        character = character_loader.get_current_character()
        if not character:
            await update.message.reply_text("❌ Персонаж не загружен!")
            return
        
        # Обновляем уровень близости
        character_loader.update_relationship_progress({
            'intimacy_level': new_level
        })
        
        name = character.get('name', 'Персонаж')
        
        # Генерируем реакцию персонажа на изменение близости
        reaction_messages = await self._generate_intimacy_change_response(name, new_level, character)
        
        current_state = await self.optimized_ai.get_simple_mood_calculation(
            self.psychological_core
        )
        
        await self.send_telegram_messages_with_timing(
            chat_id=update.effective_chat.id,
            messages=reaction_messages,
            current_state=current_state
        )

    async def _generate_intimacy_change_response(self, name: str, new_level: int, character: dict) -> List[str]:
        """Генерирует реакцию на изменение близости"""
        
        if new_level <= 3:
            level_desc = "знакомство"
            messages = [f"Хм, кажется мы только знакомимся... 😊", "Но это нормально! Всё постепенно! ✨"]
        elif new_level <= 5:
            level_desc = "дружба"
            messages = [f"Мы хорошие друзья! 😊", "Мне нравится с тобой общаться! 💕"]
        elif new_level <= 7:
            level_desc = "близкая дружба"
            messages = [f"Ты стал мне очень близок... 😊", "Кажется, между нами что-то особенное! ✨"]
        elif new_level <= 9:
            level_desc = "романтические отношения"
            if 'марин' in name.lower():
                messages = [
                    "Аааа! 😍 Мы так близки!",
                    "Мне так хорошо с тобой! Ты понимаешь мои увлечения!",
                    "Я... я тебя очень люблю! 💕"
                ]
            else:
                messages = [f"Мы так близки... 😊💕", "Я очень тебя люблю! ✨"]
        else:
            level_desc = "глубокая любовь"
            if 'марин' in name.lower():
                messages = [
                    "Я не могу без тебя! 😍💕",
                    "Ты самый важный человек в моей жизни!",
                    "Хочу быть с тобой всегда! ✨",
                    "Может... может мы навсегда? 💍"
                ]
            else:
                messages = [f"Ты моя любовь... 💕", "Не представляю жизни без тебя! ✨"]
        
        return messages
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help в естественном стиле"""
        
        # НОВОЕ: Естественный помощник без команд
        current_state = await self.optimized_ai.get_simple_mood_calculation(self.psychological_core)
        current_state['memory_context'] = 'Пользователь спрашивает о возможностях'
        
        help_messages = await self.optimized_ai.generate_split_response(
            "Расскажи пользователю как ты работаешь и что умеешь", 
            current_state
        )
        
        await self.send_telegram_messages_with_timing(
            chat_id=update.effective_chat.id,
            messages=help_messages,
            current_state=current_state
        )
    
    # Отладочные команды (будут убраны в production)
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать текущее состояние AI"""
        if not self.commands_enabled:
            return
            
        current_state = await self.optimized_ai.get_simple_mood_calculation(
            self.psychological_core
        )
        
        status_text = f"""📊 Мой текущий статус:

🎭 Настроение: {current_state['current_mood']}
⚡ Энергия: {current_state['energy_level']}/100
😊 Эмоция: {current_state['dominant_emotion']}
🕐 Активность: {current_state['activity_context']}

💭 Желание написать: {current_state['initiative_desire']}/10
📅 Сегодня отправила сообщений: {self.daily_message_count}/8

{self._get_status_emoji(current_state)}"""
        
        await update.message.reply_text(status_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """НОВАЯ команда: Статистика разговоров"""
        if not self.commands_enabled:
            return
            
        stats = self.get_conversation_stats()
        
        stats_text = f"""📈 Статистика общения:

💬 Всего диалогов: {stats['total_conversations']}
📨 Всего сообщений AI: {stats['total_ai_messages']}
📊 Среднее сообщений на ответ: {stats['avg_messages_per_response']}
🎯 Инициатив сегодня: {stats['daily_initiatives_sent']}
🕒 Последний разговор: {stats.get('last_conversation', 'Нет')}

{'🔥 Активное общение!' if stats['avg_messages_per_response'] > 2 else '📝 Стандартное общение'}"""
        
        await update.message.reply_text(stats_text)
    
    async def speed_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """НОВАЯ команда: Управление скоростью печатания"""
        if not self.commands_enabled:
            return
        
        args = context.args
        
        if not args:
            # Показываем текущий режим и доступные опции
            current_mode = self.typing_simulator.current_mode
            
            text = f"""⚡ Управление скоростью печатания:

🔧 Текущий режим: **{current_mode}**

📋 Доступные режимы:
• `lightning` - Мгновенные ответы (200 слов/мин)
• `fast` - Быстрые ответы (100 слов/мин) 
• `normal` - Обычные ответы (60 слов/мин)
• `slow` - Медленные ответы (40 слов/мин)

💡 Использование: `/speed <режим>`
Пример: `/speed lightning`"""
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        # Устанавливаем новый режим
        new_mode = args[0].lower()
        
        if new_mode in self.typing_simulator.speed_modes:
            old_mode = self.typing_simulator.current_mode
            self.typing_simulator.set_speed_mode(new_mode)
            
            # Демонстрируем новый режим сразу
            demo_messages = [
                f"Переключилась с режима '{old_mode}' на '{new_mode}'! ⚡",
                "Вот так теперь я печатаю сообщения.",
                "Заметил разницу? 😊"
            ]
            
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            
            await self.send_telegram_messages_with_timing(
                chat_id=update.effective_chat.id,
                messages=demo_messages,
                current_state=current_state
            )
        else:
            await update.message.reply_text(
                f"❌ Неизвестный режим '{new_mode}'\n"
                f"Доступные: {', '.join(self.typing_simulator.speed_modes.keys())}"
            )
    
    async def mood_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подробная информация о настроении"""
        if not self.commands_enabled:
            return
            
        mood_value = self.psychological_core.calculate_current_mood()
        personality_desc = self.psychological_core.get_personality_description()
        
        mood_text = f"""🎭 Подробно о моём настроении:

📈 Общий уровень: {mood_value:.1f}/10
🧠 Личность: {personality_desc}
💪 Энергия: {self.psychological_core.physical_state['energy_base']}/100
😰 Стресс: {self.psychological_core.physical_state['stress_level']}/10

🕰️ Эмоциональное состояние:
• Текущая эмоция: {self.psychological_core.emotional_momentum['current_emotion']}
• Интенсивность: {self.psychological_core.emotional_momentum['emotion_intensity']:.1f}
• Длительность: {self.psychological_core.emotional_momentum['emotion_duration']} мин

{self._get_mood_advice(mood_value)}"""
        
        await update.message.reply_text(mood_text)
    
    async def memories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать воспоминания о пользователе из БД"""
        if not self.commands_enabled:
            return
            
        try:
            # Используем новую систему памяти
            user_memories = self.enhanced_memory.db_manager.get_relevant_memories("пользователь", 5)
            
            if not user_memories:
                memories_text = "🤔 Пока я мало что знаю о тебе... Давай поговорим больше!"
            else:
                memories_text = "🧠 Что я помню о тебе (из базы данных):\n\n"
                for i, memory in enumerate(user_memories, 1):
                    importance_stars = "⭐" * min(memory['importance'], 5)
                    memories_text += f"{i}. {memory['content']} {importance_stars}\n"
                
                memories_text += f"\n💭 Всего воспоминаний: {len(user_memories)}"
                
                # Добавляем информацию о недавних диалогах
                recent_convs = self.enhanced_memory.db_manager.get_recent_conversations(3)
                if recent_convs:
                    memories_text += f"\n📝 Недавних диалогов: {len(recent_convs)}"
        
        except Exception as e:
            memories_text = f"❌ Ошибка получения воспоминаний: {e}\n\nПроверьте базу данных командой /dbcheck"
        
        await update.message.reply_text(memories_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений с многосообщенческими ответами"""
        user_id = update.effective_user.id
        user_message = update.message.text
        chat_id = update.effective_chat.id
        
        # Проверка разрешенных пользователей
        if self.allowed_users and user_id not in self.allowed_users:
            return
        
        try:
            # НОВОЕ: Обрабатываем сообщение через базовый класс (возвращает список)
            ai_messages = await self.process_user_message(user_message)
            
            # Получаем текущее состояние для реалистичного печатания
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            
            # Отправляем многосообщенческий ответ
            await self.send_telegram_messages_with_timing(
                chat_id=chat_id,
                messages=ai_messages,
                current_state=current_state
            )
            
            # Обновляем активность пользователя
            if user_id in self.user_states:
                self.user_states[user_id]["last_activity"] = update.message.date
            
            self.logger.info(f"Обработано сообщение от {user_id}: {user_message[:50]}... -> {len(ai_messages)} ответов")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Ой, что-то пошло не так... 😅 Попробуй написать еще раз!"
            )
    
    async def send_telegram_messages_with_timing(self, chat_id: int, messages: List[str], 
                                               current_state: Dict[str, Any]):
        """Отправка сообщений в Telegram с реалистичными паузами"""
        
        emotional_state = current_state.get('dominant_emotion', 'calm')
        energy_level = current_state.get('energy_level', 50)
        
        # Callback для отправки сообщения в Telegram
        async def send_callback(message):
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения в Telegram: {e}")
        
        # Callback для показа "печатает..."
        async def typing_callback(is_typing):
            try:
                if is_typing:
                    await self.app.bot.send_chat_action(chat_id=chat_id, action="typing")
            except Exception as e:
                self.logger.error(f"Ошибка показа typing: {e}")
        
        # Показываем предварительную сводку времени
        timing_summary = self.typing_simulator.get_realistic_delays_summary(
            messages, emotional_state, energy_level
        )
        self.logger.info(f"Отправка {len(messages)} сообщений, планируемое время: {timing_summary['total_time']}с")
        
        # Отправляем с реалистичными паузами
        await self.typing_simulator.send_messages_with_realistic_timing(
            messages=messages,
            emotional_state=emotional_state,
            energy_level=energy_level,
            send_callback=send_callback,
            typing_callback=typing_callback
        )
    
    async def deliver_message(self, message: str, message_type: str):
        """Отправка инициативного сообщения пользователям"""
        if not self.allowed_users:
            self.logger.warning("Нет разрешенных пользователей для отправки сообщений")
            return
        
        # Получаем состояние для реалистичной отправки
        current_state = await self.optimized_ai.get_simple_mood_calculation(
            self.psychological_core
        )
        
        for user_id in self.allowed_users:
            try:
                # ИЗМЕНЕНО: Теперь обрабатываем как список сообщений
                if isinstance(message, str):
                    messages = [message]
                else:
                    messages = message
                
                await self.send_telegram_messages_with_timing(
                    chat_id=user_id,
                    messages=messages,
                    current_state=current_state
                )
                
                self.logger.info(f"Инициативное сообщение ({len(messages)} частей) отправлено пользователю {user_id}")
                
            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
    
    # ПЕРЕОПРЕДЕЛЯЕМ метод для отправки инициативных сообщений
    async def send_initiative_messages(self, current_state: Dict):
        """Отправка инициативных сообщений через Telegram"""
        
        # Получаем релевантные воспоминания
        recent_memories = self.memory_system.get_relevant_memories("пользователь общение", 3)
        
        # Добавляем контекст памяти в состояние
        memory_context = "\n".join([m["content"] for m in recent_memories])
        current_state['memory_context'] = memory_context if memory_context else 'Еще мало знаешь о пользователе'
        
        try:
            # Генерируем множественные сообщения
            messages = await self.optimized_ai.generate_split_response(
                "Хочу написать пользователю что-то интересное", 
                current_state
            )
            
            # Отправляем всем разрешенным пользователям
            for user_id in self.allowed_users:
                try:
                    await self.send_telegram_messages_with_timing(
                        chat_id=user_id,
                        messages=messages,
                        current_state=current_state
                    )
                except Exception as e:
                    self.logger.error(f"Ошибка отправки инициативы пользователю {user_id}: {e}")
            
            # Обновляем состояние
            self.psychological_core.update_emotional_state("positive_interaction", 0.5)
            self.last_message_time = datetime.now()
            
            self.logger.info(f"Инициативные сообщения отправлены: {len(messages)} шт.")
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации инициативы: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок Telegram"""
        self.logger.error(f"Telegram ошибка: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "Произошла техническая ошибка... Попробуй позже! 🔧"
            )
    
    def _get_status_emoji(self, state: Dict) -> str:
        """Возвращает эмодзи для текущего статуса"""
        energy = state['energy_level']
        mood = state['current_mood']
        
        if "отличное" in mood and energy > 80:
            return "🌟 Сияю от счастья!"
        elif "хорошее" in mood and energy > 60:
            return "😊 Все отлично!"
        elif "нормальное" in mood:
            return "😌 Спокойно и размеренно"
        elif energy < 30:
            return "😴 Довольно устала..."
        else:
            return "🤗 Готова к общению!"
    
    def _get_mood_advice(self, mood_value: float) -> str:
        """Совет в зависимости от настроения"""
        if mood_value >= 8:
            return "✨ Настроение супер! Хочется делиться позитивом!"
        elif mood_value >= 6:
            return "😊 Все хорошо, можно поболтать!"
        elif mood_value >= 4:
            return "😐 Нормальное состояние, ничего особенного"
        else:
            return "😔 Что-то грущу... Может, поднимешь настроение?"
    
    async def start_telegram_bot(self):
        """Запуск Telegram бота"""
        self.logger.info("Запуск Telegram бота с многосообщенческими ответами...")
        
        # Запускаем базовый планировщик
        if not self.scheduler.running:
            self.scheduler.start()
        
        # Запускаем Telegram polling
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        self.logger.info("Telegram бот запущен и готов к работе!")
        
        try:
            # Держим приложение запущенным
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Получен сигнал остановки...")
        finally:
            await self.stop_telegram_bot()
    
    async def stop_telegram_bot(self):
        """Остановка Telegram бота"""
        self.logger.info("Остановка Telegram бота...")
        
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        
        self.stop()  # останавливаем базовый планировщик
        
        self.logger.info("Telegram бот остановлен")
