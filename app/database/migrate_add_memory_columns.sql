-- Миграция: добавление колонок для эмоциональной памяти
-- Дата: 2025-11-13

-- Добавление колонок в memories
ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0;
ALTER TABLE memories ADD COLUMN emotional_intensity REAL DEFAULT 0.0;
