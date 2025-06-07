# Интеграция с Telegram Bot API с поддержкой многосообщенческих ответов

import asyncio
import logging
from typing import Dict, Any, List
from telegram import Update, Bot
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

from ..core.companion import RealisticAICompanion

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
        
        # Команды (временно оставляем для отладки)
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Команды для отладки (будут убраны позже)
        if self.commands_enabled:
            self.app.add_handler(CommandHandler("status", self.status_command))
            self.app.add_handler(CommandHandler("mood", self.mood_command))
            self.app.add_handler(CommandHandler("memories", self.memories_command))
            self.app.add_handler(CommandHandler("stats", self.stats_command))
            self.app.add_handler(CommandHandler("dbcheck", self.dbcheck_command))        

        # Обработка текстовых сообщений
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработка ошибок
        self.app.add_error_handler(self.error_handler)
    
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
