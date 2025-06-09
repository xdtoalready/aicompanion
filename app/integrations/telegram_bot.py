# Интеграция с Telegram Bot API (ОЧИЩЕННАЯ ВЕРСИЯ)

import asyncio
import logging
import random
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

from app.core.companion import RealisticAICompanion

class TelegramCompanion(RealisticAICompanion):
    """AI-компаньон с интеграцией Telegram (Production версия)"""
    
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
        
        self.logger.info("Telegram интеграция инициализирована (Production)")
    
    def setup_handlers(self):
        """Настройка обработчиков Telegram (только основные команды)"""
        
        # ОСНОВНЫЕ команды (всегда доступны)
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # УПРАВЛЕНИЕ ПЕРСОНАЖАМИ
        self.app.add_handler(CommandHandler("characters", self.characters_command))
        self.app.add_handler(CommandHandler("switch", self.switch_command))
        self.app.add_handler(CommandHandler("charinfo", self.charinfo_command))
        self.app.add_handler(CommandHandler("relationship", self.relationship_command))
        
        # УПРАВЛЕНИЕ ПАМЯТЬЮ (критически важные)
        self.app.add_handler(CommandHandler("clearmem", self.clear_memory_command))
        self.app.add_handler(CommandHandler("reset", self.full_reset_command))
        
        # Обработка текстовых сообщений
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработка ошибок
        self.app.add_error_handler(self.error_handler)

    # =============================================================================
    # ОСНОВНЫЕ КОМАНДЫ
    # =============================================================================

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
        
        # Многосообщенческое приветствие с учётом персонажа
        character = self.character_loader.get_current_character()
        
        if character and "марин" in character.get("name", "").lower():
            welcome_messages = [
                "Привет! 😊 Я Марин Китагава!",
                "Обожаю косплей и аниме! А ещё у меня есть настроения и планы на день! ✨",
                "Иногда я сама буду тебе писать, когда захочется поболтать! 💕",
                "Просто общайся со мной как с живым человеком!"
            ]
        else:
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

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help в естественном стиле"""
        
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

    # =============================================================================
    # УПРАВЛЕНИЕ ПЕРСОНАЖАМИ
    # =============================================================================

    async def characters_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать доступных персонажей"""
        
        available_chars = self.character_loader.get_available_characters()
        current_char = self.character_loader.get_current_character()
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
        
        if not context.args:
            await update.message.reply_text(
                "❓ Укажите ID персонажа!\n\n"
                "Использование: `/switch marin_kitagawa`\n"
                "Доступные персонажи: `/characters`"
            )
            return
        
        new_character_id = context.args[0].lower()
        
        # Получаем информацию о старом персонаже
        old_char = self.character_loader.get_current_character()
        old_name = old_char.get('name', 'Неизвестный') if old_char else 'Никто'
        
        # Переключаемся
        success = self.character_loader.switch_character(new_character_id)
        
        if success:
            new_char = self.character_loader.get_current_character()
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
            self.optimized_ai.character_loader = self.character_loader
            
            self.logger.info(f"Персонаж переключён: {old_name} → {new_name}")
            
        else:
            await update.message.reply_text(
                f"❌ Не удалось переключиться на `{new_character_id}`\n\n"
                f"Проверьте что файл `characters/{new_character_id}.json` существует\n"
                f"Доступные персонажи: `/characters`",
                parse_mode='Markdown'
            )

    async def charinfo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о текущем персонаже"""
        
        character = self.character_loader.get_current_character()
        
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
        
        text += f"📁 **ID файла:** `{character.get('id', 'unknown')}`"
        
        await update.message.reply_text(text, parse_mode='Markdown')

    async def relationship_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация об отношениях"""
        
        character = self.character_loader.get_current_character()
        
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
        
        # Совместные активности (если есть)
        shared_activities = character.get('default_relationship', {}).get('shared_activities', [])
        if shared_activities:
            text += f"🎯 **Что делаем вместе:**\n"
            for activity in shared_activities[:4]:
                text += f"• {activity}\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')

    # =============================================================================
    # УПРАВЛЕНИЕ ПАМЯТЬЮ (важные команды)
    # =============================================================================

    async def clear_memory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Полная очистка памяти о пользователе"""
        try:
            self.enhanced_memory.clear_all_data()
            
            # Также очищаем локальную историю
            self.conversation_history = []
            self.daily_message_count = 0
            self.last_message_time = None
            
            await update.message.reply_text(
                "🗑️ **Память полностью очищена**\n\n"
                "💭 Все диалоги и воспоминания удалены\n"
                "🔄 Начинаем знакомство заново!"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка очистки памяти: {e}")

    async def full_reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ПОЛНАЯ перезагрузка системы"""
        
        try:
            await update.message.reply_text("🔄 Выполняю полную перезагрузку...")
            
            # 1. Очищаем память
            self.enhanced_memory.clear_all_data()
            
            # 2. Сбрасываем состояние
            self.daily_message_count = 0
            self.last_message_time = None
            self.conversation_history = []
            
            # 3. Сбрасываем виртуальную жизнь
            self.virtual_life.current_activity = None
            self.virtual_life.availability = "free"
            self.virtual_life.location = "дома"
            
            # 4. Очищаем кэш AI
            self.optimized_ai.clear_cache()
            
            await update.message.reply_text(
                "✅ **Система полностью перезагружена!**\n\n"
                "🧠 Память: очищена\n"
                "🎭 Состояние: сброшено\n"
                "💾 Кэш: очищен\n\n"
                "Готова к новому общению! 😊"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка перезагрузки: {e}")

    # =============================================================================
    # ОБРАБОТКА СООБЩЕНИЙ
    # =============================================================================

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        user_message = update.message.text
        chat_id = update.effective_chat.id
        
        # Проверка разрешенных пользователей
        if self.allowed_users and user_id not in self.allowed_users:
            return
        
        try:
            # Обрабатываем сообщение через базовый класс
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
            
            # Fallback с учётом персонажа
            character = self.character_loader.get_current_character()
            if character and "марин" in character.get("name", "").lower():
                fallback_msg = "Ой! 😅 Что-то пошло не так... Попробуй написать ещё раз! ✨"
            else:
                fallback_msg = "Извини, что-то пошло не так... 😅 Попробуй еще раз!"
            
            await update.message.reply_text(fallback_msg)

    # =============================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =============================================================================

    async def _generate_character_switch_response(self, old_name: str, new_name: str, new_character: dict) -> List[str]:
        """Генерирует сообщения о переключении персонажа"""
        
        if not new_character:
            return [f"Переключение на {new_name}... Привет! 😊"]
        
        # Специальные сообщения для Марин Китагавы
        if 'марин' in new_name.lower() or 'китагава' in new_name.lower():
            return [
                "Ааа! Вау! 😍 Это что, смена персонажа?!",
                "Привееет! Я Марин Китагава! Обожаю косплей и аниме! ✨",
                "Ты будешь помогать мне с костюмами? Я так надеюсь! 💕",
                "Расскажи, что ты любишь! Может у нас общие интересы? 🎭"
            ]
        
        # Общий шаблон для других персонажей
        messages = [f"Привет! Теперь я {new_name}! 😊"]
        
        key_traits = new_character.get('personality', {}).get('key_traits', [])
        if key_traits:
            trait = key_traits[0] if key_traits else "дружелюбная"
            messages.append(f"Я {trait} и очень рада знакомству!")
        
        catchphrases = new_character.get('speech', {}).get('catchphrases', [])
        if catchphrases:
            phrase = catchphrases[0]
            messages.append(f"{phrase} ✨")
        
        messages.append("Расскажи о себе! Хочется узнать тебя лучше! 💕")
        
        return messages

    async def send_telegram_messages_with_timing(self, chat_id: int, messages: List[str], 
                                           current_state: Dict[str, Any]):
        """Отправка сообщений в Telegram с реалистичными паузами"""
        
        if not messages:
            self.logger.warning("Нет сообщений для отправки")
            return
        
        emotional_state = current_state.get('dominant_emotion', 'calm')
        energy_level = current_state.get('energy_level', 50)
        
        self.logger.info(f"📨 Начинаю отправку {len(messages)} сообщений в chat {chat_id}")
        
        # Callback для отправки сообщения в Telegram
        async def send_callback(message):
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=message)
                self.logger.debug(f"✅ Отправлено: {message[:30]}...")
            except Exception as e:
                self.logger.error(f"❌ Ошибка отправки: {e}")
                raise e
        
        # Callback для показа "печатает..."
        async def typing_callback(is_typing):
            try:
                if is_typing:
                    await self.app.bot.send_chat_action(chat_id=chat_id, action="typing")
            except Exception as e:
                self.logger.error(f"❌ Ошибка typing: {e}")
        
        try:
            # Отправляем с реалистичными паузами
            await self.typing_simulator.send_messages_with_realistic_timing(
                messages=messages,
                emotional_state=emotional_state,
                energy_level=energy_level,
                send_callback=send_callback,
                typing_callback=typing_callback
            )
            
            self.logger.info(f"🎉 Все {len(messages)} сообщений доставлены!")
            
        except Exception as e:
            self.logger.error(f"💥 Критическая ошибка отправки: {e}")
            
            # Fallback: отправляем хотя бы первое сообщение
            if messages:
                try:
                    await self.app.bot.send_message(chat_id=chat_id, text=messages[0])
                    self.logger.info("✅ Fallback сообщение отправлено")
                except Exception as fallback_error:
                    self.logger.error(f"💀 Даже fallback провалился: {fallback_error}")

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
                # Обрабатываем как список сообщений
                if isinstance(message, str):
                    messages = [message]
                else:
                    messages = message
                
                await self.send_telegram_messages_with_timing(
                    chat_id=user_id,
                    messages=messages,
                    current_state=current_state
                )
                
                self.logger.info(f"Инициативное сообщение отправлено пользователю {user_id}")
                
            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок Telegram"""
        self.logger.error(f"Telegram ошибка: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "Произошла техническая ошибка... Попробуй позже! 🔧"
            )

    # =============================================================================
    # ЗАПУСК И ОСТАНОВКА
    # =============================================================================

    async def start_telegram_bot(self):
        """Запуск Telegram бота"""
        self.logger.info("Запуск Telegram бота (Production версия)...")
        
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