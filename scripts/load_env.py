# Загрузчик переменных окружения
import os
from pathlib import Path
from typing import Dict, Any

def load_env_config() -> Dict[str, Any]:
    """Загружает конфигурацию из переменных окружения"""
    
    config = {
        "ai": {
            "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
            "model": os.getenv("AI_MODEL", "deepseek/deepseek-chat"),
            "temperature": float(os.getenv("AI_TEMPERATURE", "0.8")),
            "max_tokens": int(os.getenv("AI_MAX_TOKENS", "300"))
        },
        "database": {
            "path": os.getenv("DATABASE_PATH", "data/companion.db"),
            "backup_interval_hours": int(os.getenv("DATABASE_BACKUP_INTERVAL", "24"))
        },
        "character": {
            "name": os.getenv("CHARACTER_NAME", "Алиса"),
            "age": int(os.getenv("CHARACTER_AGE", "25")),
            "gender": os.getenv("CHARACTER_GENDER", "female"),
            "personality_traits": {
                "extraversion": float(os.getenv("PERSONALITY_EXTRAVERSION", "6.5")),
                "agreeableness": float(os.getenv("PERSONALITY_AGREEABLENESS", "7.8")),
                "conscientiousness": float(os.getenv("PERSONALITY_CONSCIENTIOUSNESS", "6.2")),
                "neuroticism": float(os.getenv("PERSONALITY_NEUROTICISM", "4.1")),
                "openness": float(os.getenv("PERSONALITY_OPENNESS", "8.3"))
            }
        },
        "behavior": {
            "max_daily_initiatives": int(os.getenv("MAX_DAILY_INITIATIVES", "8")),
            "min_hours_between_initiatives": int(os.getenv("MIN_HOURS_BETWEEN_INITIATIVES", "2")),
            "consciousness_cycle_minutes": int(os.getenv("CONSCIOUSNESS_CYCLE_MINUTES", "30")),
            "sleep_hours": {
                "start": int(os.getenv("SLEEP_START_HOUR", "23")),
                "end": int(os.getenv("SLEEP_END_HOUR", "7"))
            }
        },
        "integrations": {
            "telegram": {
                "enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
                "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
                "allowed_users": [
                    int(uid.strip()) for uid in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",") 
                    if uid.strip().isdigit()
                ]
            },
            "web": {
                "enabled": os.getenv("WEB_ENABLED", "false").lower() == "true",
                "host": os.getenv("WEB_HOST", "localhost"),
                "port": int(os.getenv("WEB_PORT", "5000")),
                "debug": os.getenv("WEB_DEBUG", "false").lower() == "true"
            }
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": os.getenv("LOG_FILE", "logs/companion.log"),
            "max_file_size_mb": int(os.getenv("LOG_MAX_SIZE_MB", "10")),
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
        }
    }
    
    return config

def validate_env_config(config: Dict[str, Any]) -> bool:
    """Проверяет корректность конфигурации"""
    
    errors = []
    
    # Проверяем API ключ
    if not config["ai"]["openrouter_api_key"]:
        errors.append("OPENROUTER_API_KEY не установлен")
    
    # Проверяем Telegram токен если включен
    if config["integrations"]["telegram"]["enabled"] and not config["integrations"]["telegram"]["bot_token"]:
        errors.append("TELEGRAM_BOT_TOKEN не установлен при включенной Telegram интеграции")
    
    # Проверяем пользователей Telegram
    if config["integrations"]["telegram"]["enabled"] and not config["integrations"]["telegram"]["allowed_users"]:
        errors.append("TELEGRAM_ALLOWED_USERS не установлены")
    
    if errors:
        print("❌ Ошибки конфигурации:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    return True

# Пример использования
if __name__ == "__main__":
    config = load_env_config()
    
    if validate_env_config(config):
        print("✅ Конфигурация из переменных окружения корректна")
        print(f"   Character: {config['character']['name']}")
        print(f"   Telegram: {'✅' if config['integrations']['telegram']['enabled'] else '❌'}")
    else:
        print("❌ Некорректная конфигурация")