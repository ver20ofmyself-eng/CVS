-- ============================================================
-- Миграция: добавляем owner_id в таблицу prompts
-- Системный промпт (default_cv_analyzer) остаётся глобальным
-- (owner_id = NULL), пользовательские привязываются к владельцу.
--
-- Запуск:
--   psql -h localhost -p 5433 -U cvs_user -d cvs_analyzer \
--        -f migrate_prompts_owner.sql
-- ============================================================

BEGIN;

-- 1. Добавляем колонку owner_id (nullable — системный промпт её не имеет)
ALTER TABLE prompts
    ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE;

-- 2. Для промптов, созданных конкретным пользователем (не системный),
--    переносим created_by → owner_id
UPDATE prompts
SET owner_id = created_by
WHERE name <> 'default_cv_analyzer'
  AND created_by IS NOT NULL
  AND owner_id IS NULL;

-- 3. Системный промпт — owner_id остаётся NULL (это намеренно)
UPDATE prompts SET owner_id = NULL WHERE name = 'default_cv_analyzer';

-- 4. Снимаем глобальный UNIQUE с name (теперь уникален name+owner_id)
--    Сначала находим и удаляем старый constraint
DO $$
DECLARE
    cname TEXT;
BEGIN
    SELECT conname INTO cname
    FROM pg_constraint
    WHERE conrelid = 'prompts'::regclass AND contype = 'u'
      AND conname LIKE '%name%';
    IF cname IS NOT NULL THEN
        EXECUTE 'ALTER TABLE prompts DROP CONSTRAINT ' || quote_ident(cname);
        RAISE NOTICE 'Удалён constraint: %', cname;
    END IF;
END;
$$;

-- 5. Новый составной уникальный индекс: (owner_id, name)
--    NULL owner_id (системный) — разрешаем только один экземпляр по name
CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_owner_name
    ON prompts (COALESCE(owner_id::TEXT, 'system'), name);

-- 6. Индекс для быстрой выборки промптов пользователя
CREATE INDEX IF NOT EXISTS idx_prompts_owner_id ON prompts(owner_id);

COMMIT;

DO $$
BEGIN
    RAISE NOTICE '✅ Миграция prompts.owner_id завершена.';
END;
$$;
