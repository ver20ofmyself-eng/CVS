"""
CVS Analyzer API — точка входа FastAPI
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, vacancies, analyze, profile, tariffs, prompts

# ── Логирование ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 CVS Analyzer API запущен (режим AI: %s)", settings.AI_MODE)
    yield
    logger.info("🛑 CVS Analyzer API остановлен")


# ── Приложение ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API для анализа резюме кандидатов с помощью AI",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Роутеры ────────────────────────────────────────────────────────────────────
API = "/api"
app.include_router(auth.router,      prefix=f"{API}/auth",      tags=["Аутентификация"])
app.include_router(vacancies.router, prefix=f"{API}/vacancies",  tags=["Вакансии"])
app.include_router(analyze.router,   prefix=f"{API}/analyze",    tags=["Анализ CV"])
app.include_router(profile.router,   prefix=f"{API}/profile",    tags=["Профиль"])
app.include_router(tariffs.router,   prefix=f"{API}/tariffs",    tags=["Тарифы"])
app.include_router(prompts.router,   prefix=f"{API}/prompts",    tags=["Промпты"])


# ── Служебные эндпоинты ────────────────────────────────────────────────────────
@app.get("/", tags=["Служебные"])
async def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}


@app.get("/health", tags=["Служебные"])
async def health_check():
    return {"status": "healthy", "ai_mode": settings.AI_MODE}
