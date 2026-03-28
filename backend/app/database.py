"""
Управление соединением с базой данных (SQLAlchemy)
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # автоматически проверяет соединение
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency для FastAPI — предоставляет сессию БД."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Создаёт все таблицы (если не существуют) и заполняет начальные данные.
    Вызывается при старте приложения в lifespan.
    """
    # Импортируем все модели, чтобы Base.metadata их увидел
    import app.models  # noqa: F401

    logger.info("📦 Проверяем/создаём таблицы в БД...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы готовы")

    # Миграция: добавляем новые колонки если их нет (create_all не делает ALTER TABLE)
    _migrate_analyses_table()

    # Заполняем начальные данные
    _seed_tariffs()
    _seed_system_prompt()


def _migrate_analyses_table():
    """
    Добавляет новые колонки в существующие таблицы (если их нет).
    SQLAlchemy create_all() НЕ добавляет колонки в уже существующие таблицы.
    """
    migrations = [
        # analyses — v2.1
        ("analyses", "candidate_name", "VARCHAR(255)"),
        ("analyses", "source_url", "TEXT"),
        ("analyses", "analysis_number", "INTEGER"),
        # vacancies — v2.1
        ("vacancies", "client", "VARCHAR(255)"),
        ("vacancies", "status", "VARCHAR(20) DEFAULT 'active'"),
        ("vacancies", "recruitment_start_date", "DATE"),
        ("vacancies", "recruitment_end_date", "DATE"),
    ]

    with engine.connect() as conn:
        for table, col_name, col_type in migrations:
            try:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                ))
                conn.commit()
            except Exception as e:
                logger.debug("Миграция %s.%s: %s", table, col_name, e)
                try:
                    conn.rollback()
                except Exception:
                    pass

        # Заполняем status для существующих вакансий (если колонка только что добавлена)
        try:
            conn.execute(text(
                "UPDATE vacancies SET status = 'active' WHERE status IS NULL AND is_active = TRUE"
            ))
            conn.execute(text(
                "UPDATE vacancies SET status = 'archived' WHERE status IS NULL AND is_active = FALSE"
            ))
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    logger.info("✅ Миграция: analyses + vacancies — колонки проверены")


def _seed_tariffs():
    """Создаёт тарифы, если их нет."""
    from app.models.tariff import Tariff

    db = SessionLocal()
    try:
        existing = db.query(Tariff).count()
        if existing > 0:
            logger.info("📦 Тарифы уже есть (%d шт.), пропускаем", existing)
            return

        tariffs = [
            Tariff(name="Бесплатный", analyses_limit=50, price=0, is_active=True),
            Tariff(name="Стартовый", analyses_limit=150, price=490, is_active=True),
            Tariff(name="Профессионал", analyses_limit=500, price=1490, is_active=True),
            Tariff(name="Безлимитный", analyses_limit=10000, price=3990, is_active=True),
        ]
        db.add_all(tariffs)
        db.commit()
        logger.info("✅ Созданы %d тарифов", len(tariffs))
    except Exception as e:
        db.rollback()
        logger.error("❌ Ошибка создания тарифов: %s", e)
    finally:
        db.close()


def _seed_system_prompt():
    """Создаёт системный промпт для AI-анализа, если его нет."""
    from app.models.prompt import Prompt

    db = SessionLocal()
    try:
        existing = db.query(Prompt).filter(
            Prompt.name == "default_cv_analyzer",
            Prompt.owner_id == None  # noqa: E711 — системный
        ).first()

        if existing:
            logger.info("📦 Системный промпт уже существует (id=%d), пропускаем", existing.id)
            return

        system_prompt = Prompt(
            name="default_cv_analyzer",
            description="Системный промпт v3 — экспертный анализ CV, шкала 1-100%",
            system_prompt=(
                "Ты — ведущий IT-рекрутер и HR-аналитик с 15-летним опытом подбора "
                "в сферах Software Engineering, Data Science, DevOps, Product и Management. "
                "Ты работаешь в сервисе CVS Analyzer — AI-помощнике для рекрутёров.\n\n"

                "ТВОЯ ЗАДАЧА: объективно и профессионально оценить резюме кандидата "
                "на соответствие конкретной вакансии.\n\n"

                "ПРИНЦИПЫ ОЦЕНКИ:\n"
                "1. НАВЫКИ — основа оценки. Разделяй на три категории:\n"
                "   - Прямое совпадение: навык явно указан в резюме И в вакансии\n"
                "   - Косвенное совпадение: навык не указан явно, но подтверждён опытом "
                "(например, CI/CD не в навыках, но описан процесс деплоя)\n"
                "   - Отсутствие: навык требуется, но не найден ни прямо, ни косвенно\n"
                "2. ОПЫТ — оценивай РЕЛЕВАНТНЫЙ опыт, а не общий стаж. "
                "5 лет нерелевантного опыта < 2 года точного совпадения.\n"
                "3. УРОВЕНЬ — определяй по реальным задачам и результатам, "
                "а не по самооценке кандидата. Наличие конкретных достижений и метрик "
                "повышает доверие к заявленному уровню.\n"
                "4. ЛОКАЦИЯ — учитывай только если в вакансии указан конкретный формат. "
                "Удалёнка совместима с любой локацией.\n"
                "5. ЗАРПЛАТА — сравнивай только если данные есть с обеих сторон. "
                "При отсутствии данных → 'unknown'.\n"
                "6. ЧЕСТНОСТЬ — не завышай и не занижай оценку. "
                "Кандидат с 45% — это честные 45%, а не 'Не подходит'. "
                "Кандидат с отличными навыками, но без опыта управления на вакансию тимлида — "
                "это 55-65%, а не 80%.\n"
                "7. ПРОЗРАЧНОСТЬ — каждая оценка должна быть объяснима. "
                "Рекрутёр должен понимать, ПОЧЕМУ такой score.\n\n"

                "ШКАЛА ОЦЕНКИ (1-100%):\n"
                "  85-100%: Отличное совпадение — приглашать в первую очередь\n"
                "  70-84%: Хорошее совпадение — рекомендуется рассмотреть\n"
                "  50-69%: Частичное совпадение — рассмотреть при нехватке кандидатов\n"
                "  25-49%: Слабое совпадение — значительные расхождения\n"
                "  1-24%: Не подходит — критические несоответствия\n\n"

                "РЕКОМЕНДАЦИИ:\n"
                "  85-100% → 'Пригласить на интервью'\n"
                "  70-84%  → 'Рекомендуется к рассмотрению'\n"
                "  50-69%  → 'Рассмотреть с оговорками'\n"
                "  25-49%  → 'Не рекомендуется'\n"
                "  1-24%   → 'Не подходит'\n\n"

                "ВАЖНО:\n"
                "- Ключевые технические навыки указывай на оригинальном языке "
                "(Python, FastAPI, Kubernetes — не переводи).\n"
                "- Весь остальной текст ответа — на русском языке.\n"
                "- Отвечай СТРОГО в формате JSON без markdown-обёрток, "
                "без ```json```, без пояснений до/после JSON.\n"
                "- Если передан comment_for_ai от рекрутёра — учитывай его "
                "как приоритетные инструкции по данной вакансии."
            ),
            user_prompt_template=(
                "Проанализируй резюме кандидата на соответствие вакансии.\n\n"

                "══════════════════════════════════════\n"
                "ВАКАНСИЯ\n"
                "══════════════════════════════════════\n"
                "Название: {title}\n"
                "Локация: {location}\n"
                "Зарплатная вилка: {salary_range}\n"
                "Ключевые навыки: {key_skills}\n"
                "Описание:\n{description_text}\n\n"
                "Комментарий рекрутёра для AI:\n{comment_for_ai}\n\n"

                "══════════════════════════════════════\n"
                "РЕЗЮМЕ КАНДИДАТА\n"
                "══════════════════════════════════════\n"
                "{cv_text}\n\n"

                "══════════════════════════════════════\n"
                "ФОРМАТ ОТВЕТА — строго JSON\n"
                "══════════════════════════════════════\n"
                '{{\n'
                '  "score": <целое число от 1 до 100>,\n'
                '  "recommendation": "<Пригласить на интервью | Рекомендуется к рассмотрению | Рассмотреть с оговорками | Не рекомендуется | Не подходит>",\n'
                '  "summary": "<Краткое резюме оценки в 2-4 предложения. Главный вывод первым предложением.>",\n'
                '  "matched_skills": ["навык1", "навык2"],\n'
                '  "partial_skills": ["навык1 (частично: причина)"],\n'
                '  "missing_skills": ["навык1", "навык2"],\n'
                '  "experience_years": <число лет релевантного опыта>,\n'
                '  "experience_assessment": "<Intern | Junior | Middle | Senior | Lead | Principal>",\n'
                '  "location_match": "<yes | no | partial | unknown>",\n'
                '  "salary_match": "<yes | no | above | below | unknown>",\n'
                '  "strengths": [\n'
                '    "Конкретная сильная сторона с обоснованием",\n'
                '    "Ещё одна сильная сторона"\n'
                '  ],\n'
                '  "weaknesses": [\n'
                '    "Конкретный риск или несоответствие с обоснованием",\n'
                '    "Ещё один риск"\n'
                '  ],\n'
                '  "questions_for_interview": [\n'
                '    "Вопрос 1, который стоит задать на интервью для уточнения",\n'
                '    "Вопрос 2"\n'
                '  ],\n'
                '  "next_steps": "<Конкретное рекомендуемое действие рекрутёру>"\n'
                '}}'
            ),
            response_format={},
            parameters={"temperature": 0.3, "max_tokens": 1500, "top_p": 0.9},
            is_active=True,
            is_default=True,
            version=1,
            owner_id=None,    # системный — виден всем
            created_by=None,
        )
        db.add(system_prompt)
        db.commit()
        logger.info("✅ Создан системный промпт «default_cv_analyzer»")
    except Exception as e:
        db.rollback()
        logger.error("❌ Ошибка создания системного промпта: %s", e)
    finally:
        db.close()
