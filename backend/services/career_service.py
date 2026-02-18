"""
Сервис генерации карьерных планов.
"""
import json
import logging
from typing import Optional

import aiosqlite

from config import DATABASE_URL
from services.groq_service import get_groq_service, SYSTEM_PROMPT_CAREER, GROQ_MODEL_MAIN

logger = logging.getLogger(__name__)


class CareerService:

    async def get_profession_stats(self, specialty: str, region: str) -> dict:
        """Получить статистику по профессии и региону."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row

            cur = await db.execute("""
                SELECT
                    COUNT(*) as vacancy_count,
                    AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_salary,
                    MIN(salary_min) as min_salary,
                    MAX(salary_max) as max_salary
                FROM vacancies
                WHERE (LOWER(title) LIKE ? OR LOWER(normalized_title) LIKE ?)
                  AND region = ?
            """, (f"%{specialty.lower()}%", f"%{specialty.lower()}%", region))
            row = await cur.fetchone()

            # Если нет данных по региону — общее
            if row and row["vacancy_count"] == 0:
                cur = await db.execute("""
                    SELECT
                        COUNT(*) as vacancy_count,
                        AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_salary,
                        MIN(salary_min) as min_salary,
                        MAX(salary_max) as max_salary
                    FROM vacancies
                    WHERE LOWER(title) LIKE ? OR LOWER(normalized_title) LIKE ?
                """, (f"%{specialty.lower()}%", f"%{specialty.lower()}%"))
                row = await cur.fetchone()

            # Топ навыки для этой профессии
            cur2 = await db.execute("""
                SELECT skills FROM vacancies
                WHERE (LOWER(title) LIKE ? OR LOWER(normalized_title) LIKE ?)
                  AND skills IS NOT NULL LIMIT 100
            """, (f"%{specialty.lower()}%", f"%{specialty.lower()}%"))
            skill_rows = await cur2.fetchall()
            all_skills: dict[str, int] = {}
            for sr in skill_rows:
                try:
                    skills = json.loads(sr["skills"])
                    for s in skills:
                        all_skills[s] = all_skills.get(s, 0) + 1
                except Exception:
                    pass
            top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:8]

            return {
                "vacancy_count": row["vacancy_count"] if row else 0,
                "avg_salary": int(row["avg_salary"]) if row and row["avg_salary"] else None,
                "min_salary": row["min_salary"] if row else None,
                "max_salary": row["max_salary"] if row else None,
                "top_skills": [s for s, _ in top_skills],
                "region": region,
                "specialty": specialty,
            }

    async def get_alternatives(self, specialty: str, region: str) -> list[dict]:
        """Найти альтернативные профессии."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row

            # Профессии с похожими навыками или из той же отрасли
            cur = await db.execute("""
                SELECT
                    COALESCE(normalized_title, title) as profession,
                    COUNT(*) as vacancy_count,
                    AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_salary,
                    industry
                FROM vacancies
                WHERE industry = (
                    SELECT industry FROM vacancies
                    WHERE LOWER(title) LIKE ?
                    GROUP BY industry ORDER BY COUNT(*) DESC LIMIT 1
                )
                AND LOWER(title) NOT LIKE ?
                GROUP BY profession
                ORDER BY avg_salary DESC
                LIMIT 5
            """, (f"%{specialty.lower()}%", f"%{specialty.lower()}%"))
            rows = await cur.fetchall()

            return [
                {
                    "title": row["profession"],
                    "avg_salary": int(row["avg_salary"]) if row["avg_salary"] else None,
                    "vacancy_count": row["vacancy_count"],
                    "match_score": 0.7,  # TODO: реальный скоринг
                }
                for row in rows
            ]

    async def generate_plan(self, specialty: str, region: str, skills: list[str], experience_years: int) -> tuple[str, dict, list]:
        """Сгенерировать карьерный план через Groq."""
        stats = await self.get_profession_stats(specialty, region)
        alternatives = await self.get_alternatives(specialty, region)

        groq = get_groq_service()

        avg_salary_str = f"{stats['avg_salary']:,} T" if stats['avg_salary'] else 'нет данных'
        alt_list = "\n".join([
            f"- {a['title']}: {a['avg_salary']:,} T, {a['vacancy_count']} вакансий"
            for a in alternatives[:3] if a['avg_salary']
        ]) if alternatives else 'нет данных'

        context = f"""
Данные из базы EnbekAI:
- Специальность: {specialty}
- Регион: {region}
- Вакансий найдено: {stats['vacancy_count']}
- Средняя зарплата: {avg_salary_str}
- Диапазон зарплат: {stats['min_salary']} — {stats['max_salary']} T
- Топ навыки для этой профессии: {', '.join(stats['top_skills']) if stats['top_skills'] else 'нет данных'}

Данные пользователя:
- Текущие навыки: {', '.join(skills) if skills else 'не указаны'}
- Опыт работы: {experience_years} лет

Альтернативные профессии (из той же отрасли):
{alt_list}

Составь персональный карьерный план согласно инструкции.
"""

        messages = [{"role": "user", "content": context}]
        plan, model = await groq.chat(messages, system_prompt=SYSTEM_PROMPT_CAREER, max_tokens=2048)

        return plan, stats, alternatives


_career_service: Optional[CareerService] = None


def get_career_service() -> CareerService:
    global _career_service
    if _career_service is None:
        _career_service = CareerService()
    return _career_service
