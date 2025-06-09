# Файл: main.py
# Основной запускаемый файл AI-компаньона

import asyncio
import json
import logging
import os
import sys

from app.integrations.telegram_bot import TelegramCompanion
from app.core.companion import RealisticAICompanion

def load_config(config_path: str = "config/config.json") -> dict:
    """Загрузка конфигурации"""
    
    if not os.path.exists(config_path):
        print(f"❌ Файл конфигурации не найден: {config_path}")
        print("📋 Скопируйте config/config.example.json в config/config.json и заполните настройки")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Проверяем обязательные поля
        required_fields = [
            'ai.openrouter_api_key',
            'character.name'
        ]
        
        for field in required_fields:
            keys = field.split('.')
            value = config
            for key in keys:
                value = value.get(key)
                if value is None:
                    print(f"❌ Отсутствует обязательное поле в конфигурации: {field}")
                    sys.exit(1)
        
        # Проверяем API ключ
        if config['ai']['openrouter_api_key'] == 'YOUR_OPENROUTER_API_KEY_HERE':
            print("❌ Пожалуйста, укажите ваш OpenRouter API ключ в config.json")
            print("🔑 Получить ключ можно на: https://openrouter.ai")
            sys.exit(1)
        
        return config
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в формате JSON конфигурации: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        sys.exit(1)

def setup_logging(config: dict):
    """Настройка логирования"""
    
    log_config = config.get('logging', {})
    log_level = log_config.get('level', 'INFO')
    log_file = log_config.get('file', 'logs/companion.log')
    
    # Создаем директорию для логов
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_directories(config: dict):
    """Создание необходимых директорий"""
    
    directories = [
        'data',  # для базы данных
        'logs',  # для логов
        'config',  # для конфигурации
        os.path.dirname(config['database']['path'])  # директория БД
    ]
    
    for directory in directories:
        if directory:
            os.makedirs(directory, exist_ok=True)

async def main():
    """Основная функция запуска"""
    
    print("🚀 Запуск AI-компаньона...")
    print("=" * 50)
    
    # Загружаем конфигурацию
    config = load_config()
    
    # Создаем директории
    create_directories(config)
    
    # Настраиваем логирование
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Запуск AI-компаньона")
    
    try:
        # Определяем тип запуска
        telegram_enabled = config.get('integrations', {}).get('telegram', {}).get('enabled', False)
        web_enabled = config.get('integrations', {}).get('web', {}).get('enabled', False)
        
        if telegram_enabled:
            # Проверяем токен Telegram
            bot_token = config['integrations']['telegram'].get('bot_token')
            if not bot_token or bot_token == 'YOUR_TELEGRAM_BOT_TOKEN':
                print("❌ Пожалуйста, укажите токен Telegram бота в config.json")
                print("🤖 Создать бота можно у @BotFather в Telegram")
                return
            
            print("📱 Запуск с интеграцией Telegram...")
            companion = TelegramCompanion(config)
            await companion.start_telegram_bot()
            
        elif web_enabled:
            print("🌐 Запуск с веб-интерфейсом...")
            # TODO: Реализовать веб-интерфейс
            print("⚠️  Веб-интерфейс пока не реализован")
            print("💡 Используйте Telegram интеграцию")
            
        else:
            print("🔧 Запуск в консольном режиме...")
            companion = RealisticAICompanion(config)
            
            # Простой консольный интерфейс
            await run_console_mode(companion)
    
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
        logger.info("Получен сигнал остановки от пользователя")
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
        sys.exit(1)

async def run_console_mode(companion: RealisticAICompanion):
    """Консольный режим для тестирования"""
    
    print("\n💬 Консольный режим AI-компаньона")
    print("Введите 'exit' для выхода, 'status' для статуса")
    print("-" * 40)
    
    # Запускаем планировщик
    await companion.start()
    
    try:
        while True:
            user_input = input("\n👤 Вы: ").strip()
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'status':
                state = await companion.optimized_ai.get_simple_mood_calculation(
                    companion.psychological_core
                )
                print(f"🤖 Статус: {state['current_mood']}, энергия: {state['energy_level']}/100")
                continue
            elif not user_input:
                continue
            
            # Обрабатываем сообщение
            response = await companion.process_user_message(user_input)
            print(f"🤖 AI: {response}")
            
    except KeyboardInterrupt:
        pass
    finally:
        companion.stop()

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"📋 Текущая версия: {sys.version}")
        sys.exit(1)

def print_banner():
    """Печать баннера"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 AI-КОМПАНЬОН                          ║
║                                                              ║
║  Психологически достоверный виртуальный спутник              ║
║  с динамической личностью и эмоциональным интеллектом        ║
║                                                              ║
║  🧠 Живая психология  💭 Инициативное общение                ║
║  🎭 Смена настроений  📚 Долгосрочная память                 ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == "__main__":
    print_banner()
    check_python_version()
    
    # Запускаем основную функцию
    asyncio.run(main())
