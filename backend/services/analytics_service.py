"""
Сервис аналитики — агрегация данных, тренды, gap-анализ.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import aiosqlite

from config import DATABASE_URL

logger = logging.getLogger(__name__)


class AnalyticsService:

    async def get_overview(self) -> dict:
        """Общая статистика по рынку труда."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row

            # Всего вакансий
            cur = await db.execute("SELECT COUNT(*) as cnt FROM vacancies")
            total = (await cur.fetchone())["cnt"]

            # Средняя зарплата
            cur = await db.execute(
                "SELECT AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_sal "
                "FROM vacancies WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL"
            )
            avg_sal = (await cur.fetchone())["avg_sal"]

            # Топ регион
            cur = await db.execute(
                "SELECT region, COUNT(*) as cnt FROM vacancies GROUP BY region ORDER BY cnt DESC LIMIT 1"
            )
            top_region_row = await cur.fetchone()
            top_region = top_region_row["region"] if top_region_row else None

            # Топ профессия
            cur = await db.execute(
                "SELECT COALESCE(normalized_title, title) as prof, COUNT(*) as cnt "
                "FROM vacancies GROUP BY prof ORDER BY cnt DESC LIMIT 1"
            )
            top_prof_row = await cur.fetchone()
            top_prof = top_prof_row["prof"] if top_prof_row else None

            # Количество регионов
            cur = await db.execute("SELECT COUNT(DISTINCT region) as cnt FROM vacancies")
            regions_count = (await cur.fetchone())["cnt"]

            return {
                "total_vacancies": total,
                "avg_salary": int(avg_sal) if avg_sal else None,
                "top_region": top_region,
                "top_profession": top_prof,
                "regions_count": regions_count,
            }

    async def get_map_data(self) -> list[dict]:
        """Данные для карты — статистика по регионам."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row

            cur = await db.execute("""
                SELECT
                    v.region,
                    r.latitude,
                    r.longitude,
                    COUNT(*) as vacancy_count,
                    AVG((COALESCE(v.salary_min,0) + COALESCE(v.salary_max,0)) / 2.0) as avg_salary
                FROM vacancies v
                LEFT JOIN regions r ON r.name_ru = v.region
                WHERE r.latitude IS NOT NULL
                GROUP BY v.region
                ORDER BY vacancy_count DESC
            """)
            rows = await cur.fetchall()
            result = []
            for row in rows:
                # Топ профессия в регионе
                cur2 = await db.execute(
                    "SELECT COALESCE(normalized_title, title) as prof, COUNT(*) as cnt "
                    "FROM vacancies WHERE region = ? GROUP BY prof ORDER BY cnt DESC LIMIT 1",
                    (row["region"],)
                )
                top_prof_row = await cur2.fetchone()
                top_prof = top_prof_row["prof"] if top_prof_row else None

                result.append({
                    "region": row["region"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "vacancy_count": row["vacancy_count"],
                    "avg_salary": int(row["avg_salary"]) if row["avg_salary"] else None,
                    "top_profession": top_prof,
                })
            return result

    async def get_top_professions(self, region: Optional[str] = None, limit: int = 10) -> list[dict]:
        """Топ профессий по количеству вакансий."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row

            where = "WHERE region = ?" if region else ""
            params = (region,) if region else ()

            cur = await db.execute(f"""
                SELECT
                    COALESCE(normalized_title, title) as profession,
                    COUNT(*) as vacancy_count,
                    AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_salary
                FROM vacancies
                {where}
                GROUP BY profession
                ORDER BY vacancy_count DESC
                LIMIT ?
            """, (*params, limit))

            rows = await cur.fetchall()
            return [
                {
                    "profession": row["profession"],
                    "vacancy_count": row["vacancy_count"],
                    "avg_salary": int(row["avg_salary"]) if row["avg_salary"] else None,
                    "growth_percent": None,  # TODO: трекинг во времени
                }
                for row in rows
            ]

    async def get_salary_by_region(self) -> list[dict]:
        """Зарплаты по регионам."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row

            cur = await db.execute("""
                SELECT
                    region,
                    AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_salary,
                    COUNT(*) as vacancy_count
                FROM vacancies
                WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL
                GROUP BY region
                ORDER BY avg_salary DESC
            """)
            rows = await cur.fetchall()
            return [
                {
                    "region": row["region"],
                    "avg_salary": int(row["avg_salary"]) if row["avg_salary"] else None,
                    "median_salary": None,  # сложнее посчитать в SQLite без расширений
                    "vacancy_count": row["vacancy_count"],
                }
                for row in rows
            ]

    async def get_trends(self, months: int = 6) -> list[dict]:
        """Тренды вакансий за последние N месяцев."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row

            # Генерируем список месяцев
            result = []
            now = datetime.now()
            for i in range(months - 1, -1, -1):
                d = now - timedelta(days=30 * i)
                period = d.strftime("%Y-%m")
                cur = await db.execute(
                    """SELECT COUNT(*) as cnt,
                       AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_sal
                       FROM vacancies
                       WHERE strftime('%Y-%m', parsed_at) = ?""",
                    (period,)
                )
                row = await cur.fetchone()
                result.append({
                    "month": period,
                    "vacancy_count": row["cnt"] if row else 0,
                    "avg_salary": int(row["avg_sal"]) if row and row["avg_sal"] else None,
                })
            return result

    async def get_context_for_ai(self, region: Optional[str] = None, profession: Optional[str] = None) -> dict:
        """Получить данные из БД для контекста AI-чата."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            db.row_factory = aiosqlite.Row
            context = {}

            # Статистика по профессии/региону
            where_clauses = []
            params = []
            if profession:
                where_clauses.append("(LOWER(title) LIKE ? OR LOWER(normalized_title) LIKE ?)")
                params.extend([f"%{profession.lower()}%", f"%{profession.lower()}%"])
            if region:
                where_clauses.append("region = ?")
                params.append(region)

            where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            cur = await db.execute(f"""
                SELECT
                    COUNT(*) as vacancy_count,
                    AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_salary,
                    MIN(salary_min) as min_salary,
                    MAX(salary_max) as max_salary
                FROM vacancies {where}
            """, params)
            row = await cur.fetchone()
            if row:
                context["vacancy_count"] = row["vacancy_count"]
                context["avg_salary"] = int(row["avg_salary"]) if row["avg_salary"] else None
                context["min_salary"] = row["min_salary"]
                context["max_salary"] = row["max_salary"]

            # Топ навыки
            if profession or region:
                skills_where = where + " AND skills IS NOT NULL" if where else "WHERE skills IS NOT NULL"
                cur2 = await db.execute(f"""
                    SELECT skills FROM vacancies {skills_where} LIMIT 50
                """, params)
                rows = await cur2.fetchall()
                all_skills: dict[str, int] = {}
                for r in rows:
                    try:
                        skills = json.loads(r["skills"])
                        for s in skills:
                            all_skills[s] = all_skills.get(s, 0) + 1
                    except Exception:
                        pass
                top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10]
                context["top_skills"] = [s for s, _ in top_skills]

            return context

    async def update_market_stats(self):
        """Обновить агрегированную статистику в market_stats."""
        async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            period = datetime.now().strftime("%Y-%m")

            # По регионам и профессиям
            cur = await db.execute("""
                SELECT
                    region,
                    COALESCE(normalized_title, title) as profession,
                    COUNT(*) as vacancy_count,
                    AVG((COALESCE(salary_min,0) + COALESCE(salary_max,0)) / 2.0) as avg_salary
                FROM vacancies
                GROUP BY region, profession
                HAVING vacancy_count >= 2
                ORDER BY vacancy_count DESC
                LIMIT 1000
            """)
            rows = await cur.fetchall()

            for row in rows:
                await db.execute("""
                    INSERT OR REPLACE INTO market_stats
                    (region, profession, avg_salary, vacancy_count, period)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row[0], row[1],
                    int(row[3]) if row[3] else None,
                    row[2], period
                ))

            await db.commit()
            logger.info(f"market_stats обновлена: {len(rows)} записей")


_analytics: AnalyticsService = None


def get_analytics_service() -> AnalyticsService:
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsService()
    return _analytics
