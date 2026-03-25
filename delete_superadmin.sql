-- ============================================================
-- Скрипт удаления суперадмина из БД CVS Analyzer
-- Запуск:
--   psql -h localhost -p 5433 -U cvs_user -d cvs_analyzer -f delete_superadmin.sql
-- ============================================================

DO $$
DECLARE
    v_email  TEXT    := 'admin@cvsanalyzer.ru';  -- ← измените если нужно
    v_uid    INTEGER;
BEGIN
    SELECT id INTO v_uid FROM users WHERE email = v_email;

    IF v_uid IS NULL THEN
        RAISE NOTICE 'Пользователь % не найден — ничего не удалено.', v_email;
        RETURN;
    END IF;

    RAISE NOTICE 'Удаляем пользователя: % (id=%)', v_email, v_uid;

    -- 1. Снимаем ссылку на пользователя из prompts (created_by / changed_by)
    UPDATE prompts      SET created_by = NULL WHERE created_by = v_uid;
    UPDATE prompt_history SET changed_by = NULL WHERE changed_by = v_uid;
    RAISE NOTICE '  ✓ prompts.created_by / prompt_history.changed_by — обнулено';

    -- 2. Удаляем тарифы пользователя
    DELETE FROM user_tariffs WHERE user_id = v_uid;
    RAISE NOTICE '  ✓ user_tariffs удалено';

    -- 3. Удаляем аналитику
    DELETE FROM analyses WHERE user_id = v_uid;
    RAISE NOTICE '  ✓ analyses удалено';

    -- 4. Удаляем вакансии
    DELETE FROM vacancies WHERE user_id = v_uid;
    RAISE NOTICE '  ✓ vacancies удалено';

    -- 5. Удаляем пользователя
    DELETE FROM users WHERE id = v_uid;
    RAISE NOTICE '  ✓ пользователь удалён';

    -- 6. Удаляем тариф «Суперадмин» если он больше никому не назначен
    DELETE FROM tariffs
    WHERE name = 'Суперадмин'
      AND id NOT IN (SELECT DISTINCT tariff_id FROM user_tariffs WHERE tariff_id IS NOT NULL);
    RAISE NOTICE '  ✓ тариф Суперадмин удалён (если был свободен)';

    RAISE NOTICE 'Готово. Теперь запустите: python create_superadmin.py';
END;
$$;
