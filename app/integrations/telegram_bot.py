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

from ..core.companion import RealisticAICompanion
from ..database import DatabaseManager

class TelegramCompanion(RealisticAICompanion):
    """AI-компаньон с интеграцией Telegram и многосообщенческими ответами"""
    
    def __init__(self, config: Dict[str, Any]):
        # Инициализируем базу данных перед вызовом родительского конструктора
        db_path = config.get('database', {}).get('path', "data/companion.db")
        self.db_manager = DatabaseManager(db_path)
        
        # Вызываем родительский конструктор с передачей db_manager
        super().__init__(config, db_manager=self.db_manager)
        
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
        
        # Команды (временно оставляем для отладки)
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Команды для отладки (будут убраны позже)
        if self.commands_enabled:
            self.app.add_handler(CommandHandler("status", self.status_command))
            self.app.add_handler(CommandHandler("mood", self.mood_command))
            self.app.add_handler(CommandHandler("memories", self.memories_command))
            self.app.add_handler(CommandHandler("stats", self.stats_command))  # НОВАЯ команда
            self.app.add_handler(CommandHandler("speed", self.speed_command))  # НОВАЯ команда
        
        # Обработка текстовых сообщений
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработка ошибок
        self.app.add_error_handler(self.error_handler)
    
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

💬 Всего диалогов: {stats.get('total_conversations', 0)}
📨 Всего сообщений AI: {stats.get('total_ai_messages', 0)}
📊 Среднее сообщений на ответ: {stats.get('avg_messages_per_response', 0)}
🎯 Инициатив сегодня: {stats.get('daily_initiatives_sent', 0)}
🕒 Последний разговор: {stats.get('last_conversation', 'Нет')}

{'🔥 Активное общение!' if stats.get('avg_messages_per_response', 0) > 2 else '📝 Стандартное общение'}"""
        
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
        """Показать воспоминания о пользователе"""
        if not self.commands_enabled:
            return
            
        user_memories = self.memory_system.get_relevant_memories("пользователь", 5)
        
        if not user_memories:
            memories_text = "🤔 Пока я мало что знаю о тебе... Давай поговорим больше!"
        else:
            memories_text = "🧠 Что я помню о тебе:\n\n"
            for i, memory in enumerate(user_memories, 1):
                importance_stars = "⭐" * min(memory.get('importance', 1), 5)
                memories_text += f"{i}. {memory.get('content', '')} {importance_stars}\n"
            
            memories_text += f"\n💭 Всего воспоминаний: {len(self.memory_system.memories)}"
        
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
            # Получаем текущее состояние для сохранения в базу данных
            current_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            mood_before = current_state.get('current_mood', 'спокойная')
            
            # Обрабатываем сообщение через базовый класс (возвращает список)
            ai_messages = await self.process_user_message(user_message)
            
            # Получаем обновленное состояние после обработки сообщения
            updated_state = await self.optimized_ai.get_simple_mood_calculation(
                self.psychological_core
            )
            mood_after = updated_state.get('current_mood', 'спокойная')
            
            # Сохраняем диалог в базу данных
            if self.db_manager:
                conversation_id = self.db_manager.save_conversation(
                    user_message=user_message,
                    ai_responses=ai_messages,
                    mood_before=mood_before,
                    mood_after=mood_after,
                    message_type="response"
                )
                
                # Извлекаем факты из диалога
                facts_found = self.memory_system.extract_facts_from_conversation(
                    user_message=user_message,
                    ai_responses=ai_messages,
                    conversation_id=conversation_id
                )
                
                if facts_found > 0:
                    self.logger.info(f"Извлечено {facts_found} фактов из диалога")
            
            # Отправляем многосообщенческий ответ
            await self.send_telegram_messages_with_timing(
                chat_id=chat_id,
                messages=ai_messages,
                current_state=updated_state
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
        memory_context = "\n".join([m.get("content", "") for m in recent_memories])
        current_state['memory_context'] = memory_context if memory_context else 'Еще мало знаешь о пользователе'
        
        try:
            # Генерируем множественные сообщения
            messages = await self.optimized_ai.generate_split_response(
                "Хочу написать пользователю что-то интересное", 
                current_state
            )
            
            # Сохраняем инициативу в базу данных
            if self.db_manager:
                conversation_id = self.db_manager.save_conversation(
                    user_message="",  # Пустое сообщение пользователя для инициативы
                    ai_responses=messages,
                    mood_before=current_state.get('current_mood', 'спокойная'),
                    mood_after=current_state.get('current_mood', 'спокойная'),
                    message_type="initiative"
                )
                
                self.logger.info(f"Инициатива сохранена в базу данных, ID={conversation_id}")
            
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
            self.daily_message_count += 1
            
            self.logger.info(f"Инициативные сообщения отправлены: {len(messages)} шт.")
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации инициативы: {e}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок Telegram"""
        self.logger.error(f"Ошибка в Telegram: {context.error}")
    
    def _get_status_emoji(self, state: Dict[str, Any]) -> str:
        """Возвращает эмодзи статуса в зависимости от состояния"""
        mood = state.get('current_mood', '')
        emotion = state.get('dominant_emotion', '')
        energy = state.get('energy_level', 50)
        
        if 'отличное' in mood or 'прекрасное' in mood:
            return "😄 Я в отличном настроении и готова общаться!"
        elif 'хорошее' in mood:
            return "🙂 У меня всё хорошо, рада поболтать!"
        elif energy < 30:
            return "😴 Немного устала, но всё равно рада тебя видеть."
        elif 'грустн' in mood or 'sad' in emotion:
            return "😔 Немного грустно сегодня, но общение поднимает настроение."
        else:
            return "😊 Всё в порядке, как у тебя дела?"
    
    def _get_mood_advice(self, mood_value: float) -> str:
        """Возвращает совет в зависимости от настроения"""
        if mood_value >= 8:
            return "💫 Сейчас отличное время для творчества и новых идей!"
        elif mood_value >= 6:
            return "💬 Хорошее время для спокойного общения."
        elif mood_value >= 4:
            return "🤔 Можем поговорить о чём-нибудь интересном?"
        else:
            return "🌧️ Немного грустно, но разговор может поднять настроение."
    
    def run(self):
        """Запуск бота"""
        self.logger.info("Запуск Telegram бота...")
        self.app.run_polling()

