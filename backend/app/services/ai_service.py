"""
Сервис для работы с AI (DeepSeek)
Поддерживает два режима:
1. REAL - реальный API DeepSeek (требует ключ и баланс)
2. MOCK - эмуляция для разработки и тестирования
"""
import os
import json
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from app.models.prompt import Prompt

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, mode: str = "MOCK", api_key: Optional[str] = None):
        """
        Инициализация AI сервиса
        mode: "REAL" или "MOCK"
        """
        self.mode = mode.upper()
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        if self.mode == "REAL" and not self.api_key:
            logger.warning("API ключ не указан, переключаюсь в MOCK режим")
            self.mode = "MOCK"
        
        logger.info(f"AI Сервис инициализирован в режиме: {self.mode}")
    
    async def analyze_cv(
        self, 
        vacancy: Dict[str, Any], 
        cv_text: str,
        db: Optional[Session] = None,
        prompt_name: str = "default_cv_analyzer"
    ) -> Dict[str, Any]:
        """
        Анализ CV на соответствие вакансии
        """
        if self.mode == "MOCK":
            return self._mock_analysis_enhanced(vacancy, cv_text)
        else:
            return await self._real_analysis_with_prompt(vacancy, cv_text, db, prompt_name)
    
    def _mock_analysis_enhanced(self, vacancy: Dict[str, Any], cv_text: str) -> Dict[str, Any]:
        """
        Улучшенная эмуляция анализа с более реалистичной логикой
        """
        logger.info("🔧 Используется MOCK режим анализа (улучшенный)")
        
        # Извлекаем навыки из вакансии
        required_skills = vacancy.get('key_skills', [])
        cv_lower = cv_text.lower()
        
        # Анализ опыта (ищем годы)
        years_match = re.search(r'(\d+)\s*(?:лет|год|года)', cv_lower)
        experience_years = int(years_match.group(1)) if years_match else 0
        
        # Анализ зарплаты (ищем цифры)
        salary_match = re.search(r'(\d+)\s*(?:000|тыс|руб)', cv_lower)
        expected_salary = int(salary_match.group(1)) * 1000 if salary_match else None
        
        # Анализ локации
        location_match = True
        vacancy_location = vacancy.get('location', '').lower()
        if 'москва' in vacancy_location and ('спб' in cv_lower or 'питер' in cv_lower):
            location_match = False
        elif 'удален' in vacancy_location:
            location_match = True
        
        # Считаем совпадения навыков с весами
        skill_weights = {
            'python': 1.5,
            'fastapi': 1.2,
            'postgresql': 1.2,
            'docker': 1.0,
            'redis': 1.0,
            'kubernetes': 1.3,
            'aws': 1.2,
            'git': 0.8,
            'sqlalchemy': 1.1,
            'pydantic': 1.1,
            'aiogram': 1.0,
            'celery': 1.0
        }
        
        matched_skills = []
        missing_skills = []
        partial_skills = []
        total_weight = 0
        matched_weight = 0
        
        for skill in required_skills:
            skill_lower = skill.lower()
            weight = skill_weights.get(skill_lower, 1.0)
            total_weight += weight
            
            if skill_lower in cv_lower:
                matched_skills.append(skill)
                matched_weight += weight
            else:
                # Проверяем частичные совпадения
                skill_parts = skill_lower.split()
                if skill_parts:
                    found_part = False
                    for part in skill_parts:
                        if part in cv_lower and len(part) > 3:
                            partial_skills.append(f"{skill} (частично)")
                            matched_weight += weight * 0.5
                            found_part = True
                            break
                    if not found_part:
                        missing_skills.append(skill)
                else:
                    missing_skills.append(skill)
        
        # Вычисляем оценку
        if total_weight > 0:
            score = round((matched_weight / total_weight) * 10, 1)
        else:
            score = 5.0
        
        # Корректируем на основе опыта
        if experience_years >= 5:
            score = min(10, score + 1)
            experience_assessment = "Отличный опыт, соответствует senior уровню"
        elif experience_years >= 3:
            score = min(10, score + 0.5)
            experience_assessment = "Хороший опыт, соответствует middle уровню"
        elif experience_years >= 1:
            experience_assessment = "Начальный опыт, подходит для junior позиции"
        else:
            experience_assessment = "Опыт не указан или недостаточен"
        
        # Оценка зарплаты
        salary_match_status = "unknown"
        if expected_salary:
            vacancy_salary = vacancy.get('salary_range', {})
            if vacancy_salary:
                salary_min = vacancy_salary.get('min', 0)
                salary_max = vacancy_salary.get('max', 0)
                
                if salary_min and salary_max:
                    if salary_min <= expected_salary <= salary_max:
                        salary_match_status = "match"
                    elif expected_salary < salary_min:
                        salary_match_status = "below"
                    else:
                        salary_match_status = "above"
        
        # Генерируем рекомендацию
        if score >= 8:
            recommendation = "Пригласить на интервью"
            next_steps = "Провести техническое интервью для проверки практических навыков"
        elif score >= 6:
            recommendation = "Рассмотреть при наличии других кандидатов"
            next_steps = "Сравнить с другими кандидатами, при необходимости провести короткое интервью"
        else:
            recommendation = "Не подходит"
            next_steps = "Отправить вежливый отказ или сохранить в базу на будущее"
        
        # Формируем strengths и weaknesses
        strengths = []
        weaknesses = []
        
        if matched_skills:
            strengths.append(f"Владеет ключевыми технологиями: {', '.join(matched_skills[:3])}")
        if experience_years >= 3:
            strengths.append(f"Релевантный опыт: {experience_years} лет")
        if location_match:
            strengths.append("Локация соответствует требованиям")
        
        if missing_skills:
            weaknesses.append(f"Отсутствуют навыки: {', '.join(missing_skills[:3])}")
        if salary_match_status == "above":
            weaknesses.append(f"Зарплатные ожидания выше рынка ({expected_salary:,} ₽)")
        if not location_match:
            weaknesses.append("Локация не соответствует требованиям")
        
        return {
            "score": score,
            "summary": f"Кандидат с опытом {experience_years} лет. Соответствие навыкам: {len(matched_skills)}/{len(required_skills)}. {experience_assessment}",
            "matched_skills": matched_skills,
            "partial_skills": partial_skills,
            "missing_skills": missing_skills,
            "experience_years": experience_years,
            "experience_assessment": experience_assessment,
            "expected_salary": expected_salary,
            "salary_match": salary_match_status,
            "location_match": location_match,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendation": recommendation,
            "next_steps": next_steps,
            "analysis_date": datetime.now().isoformat(),
            "mode": "MOCK (enhanced)",
            "prompt_used": "default_cv_analyzer (mock)"
        }
    
    async def _real_analysis_with_prompt(
        self, 
        vacancy: Dict[str, Any], 
        cv_text: str,
        db: Optional[Session] = None,
        prompt_name: str = "default_cv_analyzer"
    ) -> Dict[str, Any]:
        """
        Реальный анализ через DeepSeek API с использованием промпта из БД
        """
        logger.info(f"🤖 Используется REAL режим анализа с промптом: {prompt_name}")
        
        # Получаем промпт из БД
        prompt = None
        if db:
            prompt = db.query(Prompt).filter(
                Prompt.name == prompt_name,
                Prompt.is_active == True
            ).first()
        
        if not prompt:
            logger.warning(f"Промпт {prompt_name} не найден, использую дефолтный")
            # Запасной вариант - жёстко закодированный промпт
            system_prompt = "Ты опытный HR-специалист и технический рекрутер."
            user_template = "Проанализируй резюме: {cv_text}"
        else:
            system_prompt = prompt.system_prompt
            user_template = prompt.user_prompt_template
            parameters = prompt.parameters or {}
        
        # Формируем промпт с подстановкой переменных
        try:
            user_prompt = user_template.format(
                title=vacancy.get('title', 'Не указано'),
                location=vacancy.get('location', 'Не указано'),
                salary_range=vacancy.get('salary_range', {}),
                key_skills=', '.join(vacancy.get('key_skills', [])),
                description_text=vacancy.get('description_text', 'Нет описания'),
                comment_for_ai=vacancy.get('comment_for_ai', 'Нет комментария'),
                cv_text=cv_text[:3000]  # Ограничиваем длину
            )
        except Exception as e:
            logger.error(f"Ошибка форматирования промпта: {e}")
            user_prompt = f"Проанализируй резюме: {cv_text[:1000]}"
        
        # Подготавливаем запрос к DeepSeek
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": parameters.get('temperature', 0.3),
            "max_tokens": parameters.get('max_tokens', 1500),
            "top_p": parameters.get('top_p', 0.9)
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis_text = result['choices'][0]['message']['content']
                    
                    # Парсим ответ AI в структурированный формат
                    return self._parse_ai_response(analysis_text, prompt_name)
                else:
                    logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                    # При ошибке переключаемся на mock режим
                    return self._mock_analysis_enhanced(vacancy, cv_text)
                    
        except Exception as e:
            logger.error(f"Исключение при вызове API: {e}")
            return self._mock_analysis_enhanced(vacancy, cv_text)
    
    def _parse_ai_response(self, text: str, prompt_name: str) -> Dict[str, Any]:
        """
        Парсинг ответа AI в структурированный формат
        """
        try:
            # Пытаемся найти JSON в ответе
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                result = json.loads(json_str)
                result['prompt_used'] = prompt_name
                result['mode'] = "REAL"
                return result
        except:
            pass
        
        # Если не удалось распарсить JSON, возвращаем структурированный текст
        return {
            "score": 0,
            "summary": text[:200],
            "raw_response": text,
            "prompt_used": prompt_name,
            "mode": "REAL (parse error)"
        }

# Создаём глобальный экземпляр сервиса
ai_service = AIService(mode=os.getenv("AI_MODE", "MOCK"))
