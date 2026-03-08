from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импортируем роутеры
from app.api import auth, vacancies, analyze, profile, tariffs, prompts

app = FastAPI(title="CVS Analyzer API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/api/auth", tags=["Аутентификация"])
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["Вакансии"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["Анализ CV"])
app.include_router(profile.router, prefix="/api/profile", tags=["Профиль"])
app.include_router(tariffs.router, prefix="/api/tariffs", tags=["Тарифы"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["Промпты"])

@app.get("/")
async def root():
    return {"message": "CVS Analyzer API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
