# 🤖 AI-Компаньон

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange.svg)](https://ai.google.dev)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-green.svg)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Психологически достоверный виртуальный спутник с динамической личностью и векторной памятью**

---

## ✨ Возможности

### 🧠 Искусственный интеллект
- **Google Gemini 2.5 Flash** - мощная и бесплатная AI модель
- **Адаптивный промпт-инжиниринг** - шаблоны Jinja2 для гибкой настройки
- **Три режима работы** - диалоги, планирование, аналитика с раздельной оптимизацией

### 👤 Система персонажей
- **Конфигурация через JSON** - полное описание личности в одном файле
- **Психологический профиль** - Big Five модель личности
- **Динамическое настроение** - реакция на события, время, контекст
- **Ценности и отношения** - глубина привязанности, история общения

### 💾 Векторная память
- **ChromaDB** - семантический поиск по эмоциональным воспоминаниям
- **3 коллекции** - разговоры, долгосрочная память, эмоциональные события
- **Умный контекст** - только релевантные воспоминания в промпте
- **Fallback к SQL** - гибридный подход при недоступности векторов

### 🌟 Виртуальная жизнь
- **Планирование дня** - динамическое формирование расписания
- **Активности** - работа, учёба, хобби, отдых с гуманизацией
- **Естественные инициативы** - 8-факторная вероятностная модель
- **Контекстные триггеры** - реакция на события, время, настроение

### 🚀 Инициативы
- **InitiativeEngine** - умная система инициативных сообщений
- **8 факторов вероятности** - время, настроение, энергия, активность, близость, время суток, день недели
- **Контекстные триггеры** - завершённая активность, долгое молчание, особое настроение
- **Тематический выбор** - темы на основе текущего контекста

### 📱 Интеграции
- **Telegram Bot** - мультисообщения, реалистичная печать, эмодзи
- **Web API** (опционально) - REST интерфейс для расширений
- **Расширяемость** - легко добавить Discord, VK, и другие

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      ИНТЕГРАЦИИ                              │
│    Telegram Bot    │    Web API    │    (future: Discord)    │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                   CORE: Companion.py                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Psychology  │  │ Relationship │  │  Virtual Life    │   │
│  │   System    │  │    Tracker   │  │    System        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                    AI LAYER                                  │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Gemini API     │  │  Initiative  │  │ Prompt         │  │
│  │ Manager        │  │  Engine      │  │ Manager        │  │
│  │ (3 use types)  │  │ (8 factors)  │  │ (Jinja2)       │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────────┐
│                   DATABASE LAYER                             │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ SQLite         │  │  ChromaDB    │  │ Memory Manager │  │
│  │ (metadata)     │  │  (vectors)   │  │ (hybrid)       │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 🛠️ Технологический стек

| Компонент | Технология | Назначение |
|-----------|-----------|------------|
| **AI Model** | Google Gemini 2.5 Flash | Генерация ответов, планирование, анализ |
| **Vector DB** | ChromaDB | Семантический поиск памяти |
| **SQL DB** | SQLite | Метаданные, история, отношения |
| **Templates** | Jinja2 | Промпт-инжиниринг |
| **Messaging** | python-telegram-bot | Telegram интеграция |
| **Scheduler** | APScheduler | Периодические задачи |
| **Framework** | asyncio | Асинхронная работа |

---

## 🚀 Быстрый старт

### 1. Установка

```bash
# Клонирование репозитория
git clone <your-repo-url> aicompanion
cd aicompanion

# Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Конфигурация

```bash
# Копируем пример
cp config/config.example.json config/config.json

# Редактируем
nano config/config.json
```

**Обязательные параметры:**

```json
{
  "ai": {
    "gemini_api_key": "YOUR_GEMINI_API_KEY"  // Получить: https://aistudio.google.com/app/apikey
  },
  "integrations": {
    "telegram": {
      "bot_token": "YOUR_BOT_TOKEN",         // От @BotFather
      "allowed_users": [123456789]           // Ваш Telegram ID
    }
  }
}
```

**Узнать Telegram ID:** напишите боту [@userinfobot](https://t.me/userinfobot)

### 3. Инициализация БД

```bash
# БД создаются автоматически при первом запуске
# SQLite: data/companion.db
# ChromaDB: data/chroma_memory/
```

### 4. Запуск

```bash
python main.py
```

При успешном запуске увидите:
```
🚀 AI Companion starting...
✅ Configuration loaded
✅ Database initialized
✅ ChromaDB vector memory ready
✅ Gemini API connected (model: gemini-2.0-flash-exp)
✅ Telegram bot started (@your_bot_name)
🎉 AI Companion is running!
```

---

## ⚙️ Конфигурация

### AI Settings

```json
{
  "ai": {
    "gemini_api_key": "YOUR_KEY",
    "model": "gemini-2.0-flash-exp",
    "max_tokens": 350,
    "temperature": 0.85,
    "top_p": 0.95,
    "top_k": 40,
    "limits": {
      "dialogue": {
        "max_requests_per_hour": 100,
        "max_tokens_per_day": 50000
      },
      "planning": {
        "max_requests_per_hour": 20,
        "max_tokens_per_day": 10000
      },
      "analytics": {
        "max_requests_per_hour": 10,
        "max_tokens_per_day": 5000
      }
    }
  }
}
```

### Behavior Settings

```json
{
  "behavior": {
    "max_daily_initiatives": 8,           // Макс инициатив в день
    "min_hours_between_initiatives": 2,    // Мин часов между инициативами
    "consciousness_cycle_minutes": 30,     // Цикл "сознания"
    "sleep_hours": {
      "start": 23,                         // Начало сна
      "end": 7                             // Конец сна
    }
  }
}
```

### Messaging Settings

```json
{
  "messaging": {
    "min_messages": 3,              // Минимум сообщений в ответе
    "max_messages": 7,              // Максимум сообщений
    "target_sentences": 3,          // Целевое кол-во предложений
    "use_emojis": true,            // Использовать эмодзи
    "max_emojis": 2                // Макс эмодзи на сообщение
  },
  "typing": {
    "mode": "fast",                // lightning | fast | normal | slow
    "show_typing_indicator": true, // Показывать "печатает..."
    "natural_pauses": true,        // Естественные паузы
    "customize_by_emotion": true   // Скорость зависит от эмоций
  }
}
```

### Memory Settings

```json
{
  "memory": {
    "max_working_memories": 50,      // Краткосрочная память
    "max_daily_memories": 200,       // Дневная память
    "importance_threshold": 7,       // Порог важности (0-10)
    "consolidation_hour": 3          // Час консолидации памяти
  }
}
```

---

## 📁 Структура проекта

```
aicompanion/
├── app/
│   ├── core/                           # Ядро системы
│   │   ├── companion.py                # 🔥 Главный класс компаньона
│   │   ├── gemini_api_manager.py       # 🔥 Gemini API менеджер
│   │   ├── initiative_engine.py        # 🔥 Умные инициативы
│   │   ├── prompt_manager.py           # 🔥 Менеджер промптов (Jinja2)
│   │   ├── ai_client.py                # AI клиент с кэшированием
│   │   ├── psychology.py               # Психологическая модель
│   │   ├── relationship_tracker.py     # Отслеживание отношений
│   │   ├── daily_planning_system.py    # Планирование дня
│   │   ├── virtual_life.py             # Виртуальная жизнь
│   │   └── ai_activity_humanizer.py    # Гуманизация активностей
│   ├── database/
│   │   ├── memory_manager_optimized.py # Гибридная память (SQL+Vector)
│   │   ├── vector_memory_manager.py    # 🔥 ChromaDB менеджер
│   │   └── schema.sql                  # SQL схема
│   └── integrations/
│       └── telegram_bot.py             # Telegram бот
├── config/
│   ├── config.json                     # Рабочая конфигурация (не в git)
│   └── config.example.json             # Шаблон конфигурации
├── characters/                          # JSON персонажи
│   └── marin_kitagawa.json
├── prompts/                             # 🔥 Jinja2 шаблоны промптов
│   ├── dialogue.jinja2                 # Основной диалог
│   ├── initiative.jinja2               # Инициативы
│   ├── planning.jinja2                 # Планирование
│   ├── humanize_activity.jinja2        # Гуманизация
│   └── planning_commands.jinja2        # Команды самопланирования
├── data/                               # Данные (создается автоматически)
│   ├── companion.db                    # SQLite БД
│   └── chroma_memory/                  # ChromaDB векторы
├── logs/                               # Логи
│   └── companion.log
├── main.py                             # 🚀 Точка входа
├── requirements.txt                    # Python зависимости
├── README.md                           # Этот файл
└── ROADMAP.md                          # План развития

🔥 - Новые/обновленные файлы (миграция Gemini + ChromaDB)
```

---

## 📚 Ключевые модули

### `app/core/companion.py`

Главный класс AI-компаньона. Координирует все подсистемы.

**Ключевые методы:**
- `process_message(user_id, text)` - обработка сообщений
- `_should_initiate_realistically()` - проверка инициатив через InitiativeEngine
- `_consciousness_cycle()` - периодический цикл "сознания"
- `get_current_state()` - получение состояния (настроение, энергия, активность)

**Зависимости:**
- GeminiAPIManager - для AI запросов
- InitiativeEngine - для умных инициатив
- VirtualLife - для активностей
- MemoryManager - для памяти
- Psychology - для моделирования личности

---

### `app/core/gemini_api_manager.py`

Менеджер Google Gemini API с тремя режимами работы.

**Типы использования:**
```python
class APIUsageType(Enum):
    DIALOGUE = "dialogue"       # Диалоги + инициативы
    PLANNING = "planning"       # Планирование дня
    ANALYTICS = "analytics"     # Консолидация памяти
```

**Ключевые методы:**
```python
async def make_request(
    usage_type: APIUsageType,
    messages: List[Dict[str, str]],
    **kwargs
) -> Response
```

**Автоматическая конфигурация:**
- DIALOGUE: temperature=0.85, max_tokens=400
- PLANNING: temperature=0.7, max_tokens=500
- ANALYTICS: temperature=0.6, max_tokens=300

**Статистика:**
```python
stats = manager.get_usage_stats()
# {'total_requests': 150, 'total_tokens': 45000, 'by_type': {...}}
```

---

### `app/core/initiative_engine.py`

Интеллектуальная система инициативных сообщений.

**8 факторов вероятности:**

| Фактор | Влияние | Множитель |
|--------|---------|-----------|
| Время с последнего сообщения | 0-24+ часов | 0.3x - 2.0x |
| Настроение | radiant/excited → sad/anxious | 0.4x - 1.5x |
| Энергия | 0-100 | 0.4x - 1.3x |
| Активность | working → free | 0.3x - 1.5x |
| Близость | 0-100 | 0.6x - 1.8x |
| Время суток | ночь → день → вечер | 0.2x - 1.3x |
| День недели | будни → выходные | 1.0x - 1.2x |
| Базовая вероятность | - | 0.3 (30%) |

**Контекстные триггеры (+бонус):**
- Завершена активность: +0.3
- Скоро важная активность: +0.2
- Долгое молчание (>6ч): +0.2
- Особое настроение (excited/anxious): +0.15

**Пример:**
```python
should_send, probability, reason = engine.should_send_initiative(
    character_state={'mood': 'happy', 'energy_level': 80, 'intimacy': 70},
    virtual_life_context={'activity': 'free', 'time': '18:00'},
    last_message_time=datetime.now() - timedelta(hours=4),
    relationship={'intimacy_level': 75}
)
# should_send=True, probability=0.68, reason="Хорошее настроение, свободна, вечер"
```

---

### `app/database/vector_memory_manager.py`

Семантический поиск памяти через ChromaDB.

**Коллекции:**
- `conversations` - история диалогов
- `memories` - долгосрочные воспоминания
- `emotional_memories` - эмоционально значимые события

**Ключевые методы:**

```python
# Добавление воспоминания
manager.add_memory(
    memory_id="mem_123",
    text="Обсуждали любимые фильмы",
    importance=8,
    emotion="happy",
    tags=["interests", "hobbies"]
)

# Семантический поиск
results = manager.search_similar_memories(
    query="что я люблю смотреть?",
    limit=5,
    min_importance=7
)
# [
#   {'text': 'Обсуждали любимые фильмы', 'similarity': 0.87, ...},
#   {'text': 'Говорили про Netflix сериалы', 'similarity': 0.82, ...}
# ]
```

**Преимущества:**
- Семантический поиск (не по ключевым словам!)
- Фильтрация по важности, эмоции, тегам
- Скоринг по релевантности (L2 distance → similarity)

---

### `app/core/prompt_manager.py`

Централизованное управление промптами через Jinja2.

**Шаблоны:**

| Файл | Назначение | Переменные |
|------|-----------|-----------|
| `dialogue.jinja2` | Основной диалог | name, personality, mood, memory_context, relationship |
| `initiative.jinja2` | Инициативы | situation_analysis, topic, time_of_day |
| `planning.jinja2` | Планирование дня | current_hour, yesterday_summary, goals |
| `humanize_activity.jinja2` | Гуманизация | activity, mood, energy |
| `planning_commands.jinja2` | Команды {{plan: ...}} | - |

**Использование:**

```python
from app.core.prompt_manager import get_prompt_manager

prompt_manager = get_prompt_manager()

prompt = prompt_manager.render('dialogue.jinja2', {
    'name': 'Алиса',
    'age': 25,
    'mood': 'happy',
    'energy': 80,
    'memory_context': 'Обсуждали планы на выходные',
    'relationship': {'intimacy_level': 75}
})
```

**Преимущества:**
- Легко изменять промпты без правки кода
- Переиспользование через `{% include %}`
- Условная логика в шаблонах
- Кэширование скомпилированных шаблонов

---

## 👥 Создание персонажа

### Полный JSON шаблон

Создайте файл `characters/my_character.json`:

```json
{
  "id": "alice_01",
  "name": "Алиса",
  "age": 25,
  "gender": "female",
  "occupation": "дизайнер",
  "background": "Креативная и жизнерадостная девушка из Москвы",

  "personality_traits": {
    "extraversion": 7.5,
    "agreeableness": 8.0,
    "conscientiousness": 6.5,
    "neuroticism": 4.0,
    "openness": 8.5
  },

  "core_values": {
    "family_importance": 8,
    "career_ambition": 7,
    "creativity_drive": 9,
    "social_connection": 8,
    "personal_growth": 9
  },

  "interests": [
    "графический дизайн",
    "современное искусство",
    "йога",
    "путешествия",
    "фотография"
  ],

  "speech_style": {
    "formality": "casual",
    "emoji_usage": "moderate",
    "sentence_length": "medium",
    "characteristic_phrases": [
      "Слушай,",
      "Кстати,",
      "Вау!",
      "Знаешь что?"
    ]
  },

  "daily_routine": {
    "wake_up_time": "08:00",
    "work_start": "10:00",
    "work_end": "18:00",
    "sleep_time": "23:30",
    "preferred_activities": {
      "morning": ["yoga", "coffee", "planning"],
      "afternoon": ["work", "lunch_with_friends"],
      "evening": ["creative_projects", "social_media", "reading"],
      "night": ["meditation", "journaling"]
    }
  },

  "emotional_patterns": {
    "default_mood": "happy",
    "mood_volatility": 0.6,
    "stress_triggers": ["deadline", "conflict", "uncertainty"],
    "joy_triggers": ["creative_success", "social_connection", "new_experiences"]
  }
}
```

### Использование в конфиге

```json
{
  "character_profile_path": "characters/my_character.json"
}
```

Система автоматически загрузит все параметры.

---

## 🔧 Разработка

### Структура кода

```python
# Пример добавления новой интеграции
from app.core.companion import AICompanion

class DiscordBot:
    def __init__(self, config):
        self.companion = AICompanion(config)

    async def on_message(self, message):
        response = await self.companion.process_message(
            user_id=message.author.id,
            text=message.content
        )
        await message.channel.send(response)
```

### Расширение промптов

Создайте новый шаблон `prompts/custom_mode.jinja2`:

```jinja2
Ты {{name}}, {{age}} лет.

Сейчас особый режим: {{mode}}.

{% if mode == "creative" %}
Будь максимально креативной и необычной!
{% endif %}

Контекст: {{context}}
```

Используйте:

```python
prompt = prompt_manager.render('custom_mode.jinja2', {
    'name': 'Алиса',
    'age': 25,
    'mode': 'creative',
    'context': 'Обсуждаем идеи для стартапа'
})
```

### Тестирование

```bash
# Установка dev-зависимостей
pip install pytest pytest-asyncio black flake8

# Запуск тестов
pytest

# Форматирование кода
black app/

# Линтер
flake8 app/
```

---

## 🐳 Docker развертывание

### Docker Compose (рекомендуется)

```yaml
# docker-compose.yml
version: '3.8'

services:
  ai-companion:
    build: .
    container_name: ai-companion
    restart: unless-stopped
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
      - ./logs:/app/logs
      - ./characters:/app/characters:ro
    environment:
      - TZ=Europe/Moscow
    mem_limit: 512m
    cpus: 1
```

```bash
# Запуск
docker-compose up -d

# Логи
docker-compose logs -f

# Остановка
docker-compose down
```

---

## 📊 Мониторинг

### Статистика API

```python
stats = companion.api_manager.get_usage_stats()
print(f"Requests: {stats['total_requests']}")
print(f"Tokens: {stats['total_tokens']}")
print(f"By type: {stats['by_type']}")
```

### Статус системы

```python
state = companion.get_current_state()
print(f"Mood: {state['mood']}")
print(f"Energy: {state['energy_level']}")
print(f"Activity: {state['current_activity']}")
print(f"Intimacy: {state['intimacy']}")
```

### Логи

```bash
# Реальное время
tail -f logs/companion.log

# Только ошибки
grep ERROR logs/companion.log

# Последние 100 строк
tail -n 100 logs/companion.log
```

---

## 🛡️ Безопасность

### Рекомендации

1. **Защита API ключей:**
   ```bash
   chmod 600 config/config.json
   echo "config/config.json" >> .gitignore
   ```

2. **Ограничение пользователей Telegram:**
   ```json
   {"allowed_users": [123456789]}  // Только ваш ID
   ```

3. **Регулярное резервное копирование:**
   ```bash
   # Автоматический бэкап (cron)
   0 3 * * * tar -czf ~/backups/companion-$(date +\%Y\%m\%d).tar.gz ~/aicompanion/data
   ```

4. **Обновление зависимостей:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## 🐛 Решение проблем

### AI не отвечает

```bash
# Проверка API ключа
python -c "import json; print(json.load(open('config/config.json'))['ai']['gemini_api_key'])"

# Тест подключения
curl https://generativelanguage.googleapis.com/v1/models?key=YOUR_KEY

# Логи ошибок
grep "Gemini API error" logs/companion.log
```

### ChromaDB не работает

```bash
# Проверка директории
ls -la data/chroma_memory/

# Пересоздание векторной БД
rm -rf data/chroma_memory/
# Перезапустить приложение
```

### Telegram бот офлайн

```bash
# Проверка токена
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"

# Проверка сети
ping api.telegram.org

# Логи бота
grep "Telegram" logs/companion.log
```

---

## 📈 Производительность

### Системные требования

| Конфигурация | RAM | CPU | Диск |
|--------------|-----|-----|------|
| Минимальная | 256 MB | 1 core | 1 GB |
| Рекомендуемая | 512 MB | 2 cores | 2 GB SSD |
| Оптимальная | 1 GB | 2+ cores | 5 GB SSD |

### Оптимизация токенов

- ✅ **Векторный поиск** - только релевантные воспоминания
- ✅ **Компактные промпты** - 300 строк вместо 800
- ✅ **Кэширование** - повторные запросы используют кэш
- ✅ **Умные лимиты** - max_tokens зависит от типа (dialogue/planning/analytics)

**Экономия:** ~60% токенов при сохранении качества!

---

## 🎯 Roadmap

См. [ROADMAP.md](ROADMAP.md) для подробного плана развития.

**Ближайшие цели:**
- [ ] Динамическое планирование активностей
- [ ] Динамика настроения от событий
- [ ] Web UI для настройки персонажей
- [ ] Мультиязычность (English support)
- [ ] Discord интеграция
- [ ] Voice messages support

---

## 📞 Поддержка

**Возникли проблемы?**

1. Проверьте логи: `tail -f logs/companion.log`
2. Убедитесь в правильности конфигурации
3. Проверьте доступность API (Gemini, Telegram)
4. Освободите место на диске
5. Перезапустите: `python main.py`

**Для разработчиков:**
- Создавайте issue в GitHub
- Пишите подробное описание проблемы
- Прикладывайте логи (без API ключей!)

---

## 📜 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

---

## 🙏 Благодарности

- **Google Gemini** - за мощный и бесплатный AI
- **ChromaDB** - за векторную базу данных
- **python-telegram-bot** - за отличную библиотеку
- **Jinja2** - за гибкие шаблоны

---

<div align="center">

**🎉 Ваш AI-компаньон готов к работе!**

*Создавайте уникальную личность, наслаждайтесь живым общением и развивайте долгосрочные отношения с вашим виртуальным спутником.*

</div>
