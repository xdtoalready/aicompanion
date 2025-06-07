-- Файл: app/database/schema.sql
-- Схема базы данных для AI-компаньона

-- Базовый профиль персонажа (статичная информация)
CREATE TABLE character_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    personality TEXT, -- JSON массив черт характера
    background TEXT, -- история персонажа
    interests TEXT, -- JSON массив интересов  
    speech_style TEXT,
    base_appearance TEXT, -- JSON с базовым внешним видом
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Текущее состояние персонажа (динамическая информация)
CREATE TABLE character_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER REFERENCES character_profile(id),
    location TEXT DEFAULT 'дома',
    mood TEXT DEFAULT 'спокойная',
    energy_level INTEGER DEFAULT 80, -- 0-100
    current_outfit TEXT, -- JSON с текущей одеждой
    current_activity TEXT,
    last_meal TEXT,
    sleep_quality TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- История диалогов
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER REFERENCES character_profile(id),
    user_message TEXT,
    ai_response TEXT,
    context_summary TEXT, -- краткое описание контекста
    mood_before TEXT, -- настроение до сообщения
    mood_after TEXT, -- настроение после сообщения
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    message_type TEXT DEFAULT 'response' -- 'response' или 'initiative'
);

-- Факты и воспоминания (что AI "помнит" о пользователе)
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER REFERENCES character_profile(id),
    memory_type TEXT, -- 'fact', 'preference', 'event', 'emotion'
    content TEXT, -- само воспоминание
    importance INTEGER DEFAULT 1, -- 1-10, важность для упоминания
    source_conversation_id INTEGER REFERENCES conversations(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- События и изменения состояния
CREATE TABLE state_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER REFERENCES character_profile(id),
    event_type TEXT, -- 'automatic', 'random', 'triggered'
    event_description TEXT,
    state_changes TEXT, -- JSON с изменениями состояния
    trigger_condition TEXT, -- что вызвало событие
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Настройки времени и поведения
CREATE TABLE behavior_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER REFERENCES character_profile(id),
    setting_name TEXT, -- 'wake_time', 'work_hours', 'initiative_frequency'
    setting_value TEXT, -- JSON со значениями
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Шаблоны для инициативных сообщений
CREATE TABLE message_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_type TEXT, -- 'morning', 'evening', 'random', 'activity_based'
    condition_context TEXT, -- в каких условиях использовать
    template_text TEXT,
    mood_requirement TEXT, -- какое настроение нужно
    energy_requirement TEXT, -- уровень энергии
    cooldown_hours INTEGER DEFAULT 24 -- как часто можно использовать
);