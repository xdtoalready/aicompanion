#!/usr/bin/env python3
"""
Основной скрипт запуска AI-компаньона
"""

import sys
import os
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Выводит баннер приложения"""
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
    print("🚀 Запуск AI-компаньона...")
    print("==================================================")

def load_config(config_path="config.json"):
    """Загружает конфигурацию из файла"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Конфигурация загружена из {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Файл конфигурации не найден: {config_path}")
        logger.info("Создаем конфигурацию по умолчанию")
        
        # Конфигурация по умолчанию
        default_config = {
            "ai": {
                "model": "deepseek/deepseek-chat-v3-0324:free",
                "max_tokens": 350,
                "temperature": 0.85
            },
            "character": {
                "name": "Алиса",
                "personality": {
                    "extraversion": 7.0,
                    "agreeableness": 8.0,
                    "conscientiousness": 6.0,
                    "neuroticism": 4.0,
                    "openness": 9.0
                }
            },
            "typing_simulator": {
                "default_speed_mode": "normal",
                "variability": 0.2
            },
            "integrations": {
                "telegram": {
                    "bot_token": "YOUR_BOT_TOKEN_HERE",
                    "allowed_users": []
                }
            },
            "database": {
                "path": "data/companion.db"
            },
            "debug": {
                "commands_enabled": True
            }
        }
        
        # Сохраняем конфигурацию по умолчанию
        os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Создана конфигурация по умолчанию: {config_path}")
        return default_config
    except json.JSONDecodeError:
        logger.error(f"Ошибка формата JSON в файле конфигурации: {config_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        sys.exit(1)

def setup_database(config):
    """Настраивает базу данных"""
    try:
        from app.database import init_database
        
        db_path = config.get('database', {}).get('path', "data/companion.db")
        logger.info(f"Инициализация базы данных: {db_path}")
        
        # Создаем директорию для базы данных
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Инициализируем базу данных, если она не существует
        if not os.path.exists(db_path):
            init_database(db_path)
            logger.info(f"База данных создана: {db_path}")
        else:
            logger.info(f"Используется существующая база данных: {db_path}")
        
        return db_path
    except Exception as e:
        logger.error(f"Ошибка настройки базы данных: {e}")
        return None

async def main():
    """Основная функция запуска"""
    print_banner()
    logger.info("Запуск AI-компаньона")
    
    try:
        # Загружаем конфигурацию
        config = load_config()
        
        # Настраиваем базу данных
        db_path = setup_database(config)
        
        # Проверяем наличие токена Telegram
        if config['integrations']['telegram']['bot_token'] == "YOUR_BOT_TOKEN_HERE":
            logger.warning("Токен Telegram бота не настроен в конфигурации")
            print("\n⚠️  Внимание: Токен Telegram бота не настроен!")
            print("   Отредактируйте файл config.json и укажите правильный токен.")
            print("   Запуск в демо-режиме без Telegram...\n")
            
            # Запускаем демо-режим
            from run_demo import run_demo
            await run_demo(config)
            return
        
        # Запускаем с интеграцией Telegram
        print("📱 Запуск с интеграцией Telegram...")
        
        # Импортируем необходимые модули
        from app.integrations.telegram_bot import TelegramCompanion
        
        # Создаем экземпляр компаньона
        companion = TelegramCompanion(config)
        
        # Запускаем бота
        companion.run()
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершение работы AI-компаньона...")
        sys.exit(0)

