"""
Сервис для работы с AI (DeepSeek).

Режимы (AI_MODE в .env):
  MOCK — детерминированная эмуляция без API-запросов. Только для разработки/тестирования.
  REAL — реальный DeepSeek API. При ошибках НЕ переключается на MOCK:
         вместо этого выбрасывает структурированное исключение AIServiceError,
         которое обрабатывается в analyze.py и возвращается клиенту как HTTP 503.

Логика выбора промпта (REAL):
  1. Ищем активный пользовательский промпт с is_default=True для данного user_id.
  2. Если нет — берём системный (default_cv_analyzer, owner_id IS NULL).
  3. Если и системный не найден — выбрасываем AIServiceError (не MOCK!).
"""
import json
import logging
import re
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_NAME = "default_cv_analyzer"


class AIServiceError(Exception):
    """
    Ошибка AI-сервиса — пробрасывается наверх, никогда не глушится MOCK-ом.
    Атрибут `user_message` — строка для показа пользователю.
    """
    def __init__(self, user_message: str, technical: str = ""):
        self.user_message = user_message
        self.technical    = technical
        super().__init__(user_message)


class AIService:
    def __init__(self) -> None:
        self.mode    = settings.AI_MODE.upper()
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.model   = settings.DEEPSEEK_MODEL
        self.timeout = settings.DEEPSEEK_TIMEOUT
        self.retries = getattr(settings, "DEEPSEEK_RETRIES", 2)

        if self.mode == "REAL" and not self.api_key:
            raise RuntimeError(
                "AI_MODE=REAL задан в .env, но DEEPSEEK_API_KEY пустой. "
                "Заполните ключ или переключитесь на AI_MODE=MOCK."
            )

        logger.info(f"🤖 AIService запущен в режиме: {self.mode}")

    # ── Публичный метод ────────────────────────────────────────────────────────
    async def analyze_cv(
        self,
        vacancy: Dict[str, Any],
        cv_text: str,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Анализ резюме на соответствие вакансии.
        Выбрасывает AIServiceError при проблемах в REAL-режиме.
        """
        if self.mode == "MOCK":
            return self._mock_analysis(vacancy, cv_text)
        return await self._real_analysis(vacancy, cv_text, db, user_id)

    # ── MOCK ───────────────────────────────────────────────────────────────────
    def _mock_analysis(self, vacancy: Dict[str, Any], cv_text: str) -> Dict[str, Any]:
        """Детерминированная эмуляция — только для разработки."""
        logger.info("🔧 MOCK-анализ (только для тестирования)")

        required_skills = vacancy.get("key_skills", [])
        cv_lower        = cv_text.lower()

        years_m          = re.search(r"(\d+)\s*(?:лет|год|года)", cv_lower)
        experience_years = int(years_m.group(1)) if years_m else 0

        salary_m        = re.search(r"(\d+)\s*(?:000|тыс|руб)", cv_lower)
        expected_salary = int(salary_m.group(1)) * 1000 if salary_m else None

        matched, missing, partial = [], [], []
        total_w = matched_w = 0
        _weights = dict(python=1.5, fastapi=1.2, postgresql=1.2, docker=1.0,
                        kubernetes=1.3, aws=1.2, git=0.8, redis=1.0)

        for skill in required_skills:
            sl = skill.lower()
            w  = _weights.get(sl, 1.0)
            total_w += w
            if sl in cv_lower:
                matched.append(skill); matched_w += w
            else:
                parts = [p for p in sl.split() if len(p) > 3]
                if any(p in cv_lower for p in parts):
                    partial.append(f"{skill} (частично)"); matched_w += w * 0.5
                else:
                    missing.append(skill)

        score = round((matched_w / total_w * 10), 1) if total_w else 5.0
        if   experience_years >= 5: score = min(10.0, score + 1.0); exp_txt = "Senior"
        elif experience_years >= 3: score = min(10.0, score + 0.5); exp_txt = "Middle"
        elif experience_years >= 1: exp_txt = "Junior"
        else:                       exp_txt = "Опыт не указан"

        sal_status = "unknown"
        if expected_salary:
            sr = vacancy.get("salary_range", {})
            if sr:
                s_min, s_max = sr.get("min"), sr.get("max")
                if s_min and s_max:
                    if s_min <= expected_salary <= s_max: sal_status = "yes"
                    elif expected_salary < s_min:         sal_status = "below"
                    else:                                 sal_status = "above"

        if   score >= 8: rec = "Пригласить на интервью"; ns = "Провести техническое интервью"
        elif score >= 6: rec = "Рассмотреть";             ns = "Сравнить с другими кандидатами"
        else:            rec = "Не подходит";             ns = "Отправить вежливый отказ"

        return dict(
            score=score,
            summary=f"{exp_txt}. Навыки: {len(matched)}/{len(required_skills)}. [MOCK]",
            matched_skills=matched, partial_skills=partial, missing_skills=missing,
            experience_years=experience_years, experience_assessment=exp_txt,
            expected_salary=expected_salary, salary_match=sal_status,
            location_match="unknown",
            strengths=[f"Навыки: {', '.join(matched[:3])}"] if matched else [],
            weaknesses=[f"Отсутствуют: {', '.join(missing[:3])}"] if missing else [],
            recommendation=rec, next_steps=ns,
            analysis_date=datetime.now().isoformat(),
            mode="MOCK", prompt_used="mock", tokens_used=0,
        )

    # ── REAL ───────────────────────────────────────────────────────────────────
    async def _real_analysis(
        self,
        vacancy: Dict[str, Any],
        cv_text: str,
        db: Optional[Session],
        user_id: Optional[int],
    ) -> Dict[str, Any]:
        """
        Реальный запрос к DeepSeek.
        Выбрасывает AIServiceError — никакого тихого fallback на MOCK.
        """
        system_prompt, user_template, parameters, prompt_name = self._load_prompt(db, user_id)

        try:
            user_prompt = user_template.format(
                title            = vacancy.get("title", ""),
                location         = vacancy.get("location", ""),
                salary_range     = vacancy.get("salary_range", {}),
                key_skills       = ", ".join(vacancy.get("key_skills", [])),
                description_text = vacancy.get("description_text", ""),
                comment_for_ai   = vacancy.get("comment_for_ai", ""),
                cv_text          = cv_text[:4000],
            )
        except (KeyError, ValueError) as e:
            raise AIServiceError(
                user_message = "Ошибка в шаблоне промпта: некорректные переменные.",
                technical    = str(e),
            )

        payload = {
            "model"      : self.model,
            "messages"   : [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": parameters.get("temperature", 0.3),
            "max_tokens" : parameters.get("max_tokens",  1500),
            "top_p"      : parameters.get("top_p",       0.9),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type" : "application/json",
        }

        last_error: Optional[Exception] = None

        for attempt in range(1, self.retries + 2):
            try:
                logger.info(f"DeepSeek запрос (попытка {attempt}/{self.retries + 1}), промпт: {prompt_name}")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self.api_url, headers=headers, json=payload)

                if resp.status_code == 200:
                    data        = resp.json()
                    raw_text    = data["choices"][0]["message"]["content"]
                    tokens_used = data.get("usage", {}).get("total_tokens", 0)
                    result      = self._parse_response(raw_text, prompt_name)
                    result["tokens_used"] = tokens_used
                    result["mode"]        = "REAL"
                    logger.info(f"✅ DeepSeek OK, score={result.get('score')}, tokens={tokens_used}")
                    return result

                # ── Обработка HTTP-ошибок ──────────────────────────────────
                if resp.status_code == 401:
                    raise AIServiceError(
                        "Ключ DeepSeek API недействителен. Проверьте DEEPSEEK_API_KEY в .env.",
                        f"HTTP 401: {resp.text[:200]}"
                    )
                if resp.status_code == 403:
                    raise AIServiceError(
                        "Доступ к DeepSeek API запрещён (HTTP 403). Проверьте ключ и права.",
                        resp.text[:200]
                    )
                if resp.status_code == 402:
                    raise AIServiceError(
                        "Недостаточно средств на балансе DeepSeek. Пополните счёт на platform.deepseek.com.",
                        "HTTP 402 Payment Required"
                    )
                if resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate-limit (429), жду {wait}с...")
                    await asyncio.sleep(wait)
                    last_error = RuntimeError(f"HTTP 429 Rate limit на попытке {attempt}")
                    continue
                if resp.status_code >= 500:
                    last_error = RuntimeError(f"HTTP {resp.status_code}: сервер DeepSeek недоступен")
                    logger.warning(str(last_error))
                    if attempt <= self.retries:
                        await asyncio.sleep(2 ** attempt)
                    continue

                # Прочие 4xx
                raise AIServiceError(
                    f"DeepSeek вернул неожиданный статус {resp.status_code}.",
                    resp.text[:300]
                )

            except AIServiceError:
                raise  # Пробрасываем как есть — не глушим

            except httpx.TimeoutException:
                last_error = TimeoutError(f"Таймаут {self.timeout}с на попытке {attempt}")
                logger.warning(str(last_error))
                if attempt <= self.retries:
                    await asyncio.sleep(1)

            except httpx.ConnectError as e:
                last_error = e
                logger.warning(f"Ошибка соединения с DeepSeek: {e}")
                if attempt <= self.retries:
                    await asyncio.sleep(2)

            except Exception as e:
                logger.exception(f"Неожиданная ошибка при вызове DeepSeek: {e}")
                raise AIServiceError(
                    "Внутренняя ошибка при обращении к AI. Попробуйте позже.",
                    str(e)
                )

        # Все попытки исчерпаны
        raise AIServiceError(
            f"DeepSeek API недоступен после {self.retries + 1} попыток. "
            "Проверьте подключение к интернету или повторите позже.",
            str(last_error),
        )

    # ── Загрузка промпта ───────────────────────────────────────────────────────
    def _load_prompt(
        self,
        db: Optional[Session],
        user_id: Optional[int],
    ):
        """
        Возвращает (system_prompt, user_template, parameters, prompt_name).

        Приоритет:
          1. Пользовательский is_default=True для user_id
          2. Системный (owner_id IS NULL, is_active=True)
          3. AIServiceError — не MOCK
        """
        if db and user_id:
            # Пользовательский основной
            prompt = (
                db.query(Prompt)
                .filter(
                    Prompt.owner_id  == user_id,
                    Prompt.is_default == True,
                    Prompt.is_active  == True,
                )
                .first()
            )
            if prompt:
                return self._extract_prompt(prompt)

        if db:
            # Системный
            prompt = (
                db.query(Prompt)
                .filter(
                    Prompt.name      == SYSTEM_PROMPT_NAME,
                    Prompt.owner_id  == None,
                    Prompt.is_active == True,
                )
                .first()
            )
            if prompt:
                return self._extract_prompt(prompt)

        raise AIServiceError(
            "Промпт для анализа не найден. Убедитесь, что системный промпт "
            f"«{SYSTEM_PROMPT_NAME}» существует и активен в базе данных.",
            "No active prompt found in DB"
        )

    @staticmethod
    def _extract_prompt(prompt: Prompt):
        params = prompt.parameters or {}
        if isinstance(params, str):
            try: params = json.loads(params)
            except Exception: params = {}
        return prompt.system_prompt, prompt.user_prompt_template, params, prompt.name

    # ── Парсинг ответа ─────────────────────────────────────────────────────────
    def _parse_response(self, text: str, prompt_name: str) -> Dict[str, Any]:
        """Извлекает JSON из ответа LLM. Терпимо к markdown-обёртке."""
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
        start = cleaned.find("{")
        end   = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(cleaned[start:end])
                result.setdefault("prompt_used", prompt_name)
                if "score" in result:
                    result["score"] = float(result["score"])
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error: {e}")

        # Если JSON не распарсился — это тоже ошибка, не MOCK
        raise AIServiceError(
            "AI вернул ответ в неожиданном формате. "
            "Проверьте user_prompt_template — в нём должна быть инструкция вернуть JSON.",
            f"Raw response: {text[:300]}"
        )


# ── Singleton ──────────────────────────────────────────────────────────────────
ai_service = AIService()
