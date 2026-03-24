-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);

-- Таблица тарифов
CREATE TABLE IF NOT EXISTS tariffs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    analyses_limit INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Вставляем тарифы
INSERT INTO tariffs (name, analyses_limit, price) 
VALUES 
    ('Бесплатный', 50, 0),
    ('Частичный', 100, 500),
    ('Полный', 300, 1200),
    ('Суперадмин', 10000, 0)
ON CONFLICT (name) DO UPDATE SET 
    analyses_limit = EXCLUDED.analyses_limit,
    price = EXCLUDED.price;

-- Таблица связи пользователей с тарифами
CREATE TABLE IF NOT EXISTS user_tariffs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tariff_id INTEGER REFERENCES tariffs(id),
    analyses_left INTEGER NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_user_tariffs_user_id ON user_tariffs(user_id);

-- Таблица вакансий
CREATE TABLE IF NOT EXISTS vacancies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    salary_range JSONB,
    description_html TEXT,
    description_text TEXT,
    key_skills JSONB DEFAULT '[]',
    comment_for_ai TEXT,
    templates JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vacancies_user_id ON vacancies(user_id);
CREATE INDEX IF NOT EXISTS idx_vacancies_is_active ON vacancies(is_active);

-- Таблица анализов (ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ)
CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    vacancy_id INTEGER REFERENCES vacancies(id) ON DELETE SET NULL,
    
    -- Исходные данные
    cv_text TEXT NOT NULL,
    cv_text_preview VARCHAR(500),
    
    -- Результаты анализа
    ai_response JSONB,
    score FLOAT,
    recommendation VARCHAR(50),
    
    -- Детали для фильтрации (ВСЕ JSONB ПОЛЯ)
    matched_skills JSONB DEFAULT '[]',
    missing_skills JSONB DEFAULT '[]',
    experience_years INTEGER,
    location_match VARCHAR(20),  -- Строка: 'yes', 'no', 'unknown'
    salary_match VARCHAR(20),     -- Строка: 'yes', 'no', 'unknown', 'above', 'below'
    
    -- Метаданные
    mode VARCHAR(50) DEFAULT 'MOCK',
    prompt_used VARCHAR(100),
    tokens_used INTEGER DEFAULT 0,
    processing_time FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для analyses
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_score ON analyses(score);
CREATE INDEX IF NOT EXISTS idx_analyses_recommendation ON analyses(recommendation);
CREATE INDEX IF NOT EXISTS idx_analyses_experience_years ON analyses(experience_years);
CREATE INDEX IF NOT EXISTS idx_analyses_mode ON analyses(mode);

-- Таблица платежей
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    tariff_id INTEGER REFERENCES tariffs(id),
    payment_system VARCHAR(50),
    payment_id VARCHAR(255),
    amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'RUB',
    status VARCHAR(50),
    payment_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);

-- Таблица настроек AI
CREATE TABLE IF NOT EXISTS ai_settings (
    id SERIAL PRIMARY KEY,
    api_key_encrypted TEXT,
    monthly_limit INTEGER DEFAULT 10000,
    used_this_month INTEGER DEFAULT 0,
    reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 month'
);

-- Таблица промптов
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(255),
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    response_format JSONB DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    version INTEGER DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(name);
CREATE INDEX IF NOT EXISTS idx_prompts_is_active ON prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_prompts_is_default ON prompts(is_default);

-- Таблица истории промптов
CREATE TABLE IF NOT EXISTS prompt_history (
    id SERIAL PRIMARY KEY,
    prompt_id INTEGER REFERENCES prompts(id) ON DELETE CASCADE,
    name VARCHAR(100),
    system_prompt TEXT,
    user_prompt_template TEXT,
    parameters JSONB,
    version INTEGER,
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_comment VARCHAR(255)
);

-- Вставляем дефолтный промпт
INSERT INTO prompts (name, description, system_prompt, user_prompt_template, response_format, is_default) VALUES 
(
    'default_cv_analyzer',
    'Стандартный промпт для анализа CV',
    'Ты опытный HR-специалист и технический рекрутер с 10-летним опытом найма IT-специалистов. Анализируй резюме кандидатов максимально объективно, учитывая требования вакансии. Обращай внимание на: релевантный опыт, ключевые навыки, образование, достижения, локацию, зарплатные ожидания. Дай четкую рекомендацию.',
    'Проведи анализ резюме кандидата на соответствие вакансии.

ИНФОРМАЦИЯ О ВАКАНСИИ:
Название: {title}
Локация: {location}
Зарплата: {salary_range}
Ключевые навыки: {key_skills}
Описание: {description_text}
Комментарий рекрутера: {comment_for_ai}

ТЕКСТ РЕЗЮМЕ:
{cv_text}

ПРОАНАЛИЗИРУЙ:
1. Соответствие ключевым навыкам (какие совпадают, какие отсутствуют, уровень владения)
2. Релевантность опыта (годы, проекты, технологии, достижения)
3. Локация и возможность переезда/удалёнки
4. Зарплатные ожидания (если указаны) - соответствуют ли рынку
5. Образование и дополнительное обучение
6. Сильные стороны кандидата
7. Слабые стороны или риски

ОТВЕТ ДОЛЖЕН БЫТЬ В ФОРМАТЕ JSON:
{
    "score": <число от 1 до 10>,
    "summary": "<краткое резюме анализа 2-3 предложения>",
    "matched_skills": ["список", "совпавших", "навыков"],
    "missing_skills": ["список", "отсутствующих", "навыков"],
    "experience_years": <число лет опыта>,
    "experience_assessment": "<оценка релевантности опыта>",
    "location_match": "yes/no/unknown",
    "salary_match": "yes/no/unknown/above/below",
    "strengths": ["сильная", "сторона1", "сторона2"],
    "weaknesses": ["слабая", "сторона1", "сторона2"],
    "recommendation": "<Пригласить на интервью/Рассмотреть/Не подходит>",
    "next_steps": "<что делать дальше>"
}',
    '{
        "temperature": 0.3,
        "max_tokens": 1500,
        "top_p": 0.9
    }',
    TRUE
);

-- Обновляем существующую таблицу analyses (если нужно)
DO $$
BEGIN
    -- Добавляем колонки если их нет
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS cv_text_preview VARCHAR(500);
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS score FLOAT;
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS recommendation VARCHAR(50);
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS matched_skills JSONB DEFAULT '[]';
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS missing_skills JSONB DEFAULT '[]';
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS experience_years INTEGER;
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS location_match VARCHAR(20);
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS salary_match VARCHAR(20);
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS mode VARCHAR(50) DEFAULT 'MOCK';
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS prompt_used VARCHAR(100);
    EXCEPTION WHEN duplicate_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ADD COLUMN IF NOT EXISTS processing_time FLOAT;
    EXCEPTION WHEN duplicate_column THEN END;
    
    -- Изменяем типы полей если они уже существуют
    BEGIN
        ALTER TABLE analyses ALTER COLUMN matched_skills TYPE JSONB USING matched_skills::JSONB;
    EXCEPTION WHEN undefined_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ALTER COLUMN missing_skills TYPE JSONB USING missing_skills::JSONB;
    EXCEPTION WHEN undefined_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ALTER COLUMN recommendation TYPE VARCHAR(50);
    EXCEPTION WHEN undefined_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ALTER COLUMN location_match TYPE VARCHAR(20);
    EXCEPTION WHEN undefined_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ALTER COLUMN salary_match TYPE VARCHAR(20);
    EXCEPTION WHEN undefined_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ALTER COLUMN mode TYPE VARCHAR(50);
    EXCEPTION WHEN undefined_column THEN END;
    
    BEGIN
        ALTER TABLE analyses ALTER COLUMN prompt_used TYPE VARCHAR(100);
    EXCEPTION WHEN undefined_column THEN END;
END $$;
