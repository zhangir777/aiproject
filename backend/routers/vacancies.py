import json
from typing import Optional
from fastapi import APIRouter, Query
import aiosqlite
from models import VacancyOut, VacancyListResponse
from config import DATABASE_URL

router = APIRouter()


@router.get("", response_model=VacancyListResponse)
async def list_vacancies(
    region: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Список вакансий с фильтрами и пагинацией."""
    where_clauses = []
    params = []

    if region:
        where_clauses.append("region = ?")
        params.append(region)
    if industry:
        where_clauses.append("industry = ?")
        params.append(industry)
    if salary_min:
        where_clauses.append("(salary_min >= ? OR salary_max >= ?)")
        params.extend([salary_min, salary_min])
    if salary_max:
        where_clauses.append("(salary_max <= ? OR salary_min <= ?)")
        params.extend([salary_max, salary_max])

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    offset = (page - 1) * per_page

    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row

        # Общее количество
        cur = await db.execute(f"SELECT COUNT(*) as cnt FROM vacancies {where}", params)
        total = (await cur.fetchone())["cnt"]

        # Данные с пагинацией
        cur = await db.execute(
            f"SELECT * FROM vacancies {where} ORDER BY parsed_at DESC LIMIT ? OFFSET ?",
            [*params, per_page, offset],
        )
        rows = await cur.fetchall()

        items = []
        for row in rows:
            row_dict = dict(row)
            # Парсим JSON поля
            for field in ["skills", "skill_tags"]:
                if row_dict.get(field):
                    try:
                        row_dict[field] = json.loads(row_dict[field])
                    except Exception:
                        row_dict[field] = []
            items.append(VacancyOut(**row_dict))

    return VacancyListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/industries")
async def get_industries():
    """Список отраслей с количеством вакансий."""
    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT industry, COUNT(*) as count FROM vacancies "
            "WHERE industry IS NOT NULL GROUP BY industry ORDER BY count DESC"
        )
        rows = await cur.fetchall()
        return [{"industry": row["industry"], "count": row["count"]} for row in rows]


@router.get("/skills")
async def get_skills(profession: Optional[str] = Query(None)):
    """Топ навыков с зарплатным буст."""
    where = ""
    params = []
    if profession:
        where = "WHERE LOWER(title) LIKE ? OR LOWER(normalized_title) LIKE ?"
        params = [f"%{profession.lower()}%", f"%{profession.lower()}%"]

    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        skills_where = where + " AND skills IS NOT NULL" if where else "WHERE skills IS NOT NULL"
        cur = await db.execute(f"SELECT skills FROM vacancies {skills_where} LIMIT 500", params)
        rows = await cur.fetchall()

        skill_counts: dict[str, int] = {}
        for row in rows:
            try:
                skills = json.loads(row["skills"])
                for s in skills:
                    skill_counts[s] = skill_counts.get(s, 0) + 1
            except Exception:
                pass

        result = sorted(
            [{"skill": k, "count": v, "avg_salary_boost": None} for k, v in skill_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
        return result[:30]


@router.get("/regions")
async def get_regions():
    """Список регионов."""
    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM regions ORDER BY name_ru")
        rows = await cur.fetchall()
        return [dict(row) for row in rows]
