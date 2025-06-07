# Интеграция с Telegram Bot API

import asyncio
import logging
from typing import Dict, Any
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
    """AI-компаньон с интеграцией Telegram"""
    
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
        
        self.logger.info("Telegram интеграция инициализирована")
    
    def setup_handlers(self):
        """Настройка обработчиков Telegram"""
        
        # Команды
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("mood", self.mood_command))
        self.app.add_handler(CommandHandler("memories", self.memories_command))
        
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
        
        welcome_message = """Привет! 😊 

Я твой AI-компаньон. Я не просто отвечаю на сообщения - я живу своей жизнью, у меня есть настроения, планы и желания. Иногда я сама буду тебе писать, когда захочется поболтать!

Доступные команды:
/mood - моё текущее настроение
/status - что я сейчас делаю
/memories - что я помню о тебе
/help - помощь

Просто пиши мне что хочешь - давай общаться! ✨"""
        
        await update.message.reply_text(welcome_message)
        self.logger.info(f"Новый пользователь начал общение: {user_id}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        help_text = """🤖 Как я работаю:

Я - живой AI-компаньон с собственной личностью. У меня есть:
• Настроения и эмоции
• Планы и желания  
• Память о наших разговорах
• Свой распорядок дня

📱 Команды:
/mood - узнать моё настроение
/status - что я делаю сейчас
/memories - что помню о тебе

💬 Особенности:
• Иногда я сама напишу тебе
• Моё настроение влияет на общение
• Я помню наши разговоры
• У меня есть свои дела и события

Просто общайся со мной как с живым человеком! 😊"""
        
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать текущее состояние AI"""
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
    
    async def mood_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подробная информация о настроении"""
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
        user_memories = self.memory_system.get_relevant_memories("пользователь", 5)
        
        if not user_memories:
            memories_text = "🤔 Пока я мало что знаю о тебе... Давай поговорим больше!"
        else:
            memories_text = "🧠 Что я помню о тебе:\n\n"
            for i, memory in enumerate(user_memories, 1):
                importance_stars = "⭐" * min(memory['importance'], 5)
                memories_text += f"{i}. {memory['content']} {importance_stars}\n"
            
            memories_text += f"\n💭 Всего воспоминаний: {len(self.memory_system.memories)}"
        
        await update.message.reply_text(memories_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Проверка разрешенных пользователей
        if self.allowed_users and user_id not in self.allowed_users:
            return
        
        try:
            # Показываем что печатаем
            await update.message.chat.send_action("typing")
            
            # Обрабатываем сообщение через базовый класс
            ai_response = await self.process_user_message(user_message)
            
            # Отправляем ответ
            await update.message.reply_text(ai_response)
            
            # Обновляем активность пользователя
            if user_id in self.user_states:
                self.user_states[user_id]["last_activity"] = update.message.date
            
            self.logger.info(f"Обработано сообщение от {user_id}: {user_message[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
            await update.message.reply_text(
                "Ой, что-то пошло не так... 😅 Попробуй написать еще раз!"
            )
    
    async def deliver_message(self, message: str, message_type: str):
        """Отправка инициативного сообщения пользователям"""
        if not self.allowed_users:
            self.logger.warning("Нет разрешенных пользователей для отправки сообщений")
            return
        
        for user_id in self.allowed_users:
            try:
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=message
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
        self.logger.info("Запуск Telegram бота...")
        
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