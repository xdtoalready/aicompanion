-- Миграция: добавление новых колонок для улучшенного планирования
-- Дата: 2025-11-13

-- Добавление колонок в virtual_activities
ALTER TABLE virtual_activities ADD COLUMN planning_date TEXT;
ALTER TABLE virtual_activities ADD COLUMN generated_by_ai BOOLEAN DEFAULT 0;
ALTER TABLE virtual_activities ADD COLUMN flexibility INTEGER DEFAULT 5;
ALTER TABLE virtual_activities ADD COLUMN importance INTEGER DEFAULT 5;
ALTER TABLE virtual_activities ADD COLUMN planned_by TEXT DEFAULT 'system';
ALTER TABLE virtual_activities ADD COLUMN emotional_reason TEXT;
ALTER TABLE virtual_activities ADD COLUMN can_reschedule BOOLEAN DEFAULT 1;
