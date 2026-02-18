"""Быстрая проверка качества данных в БД."""
import asyncio
import sys
import os
# Фикс для Windows: использовать UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiosqlite
from config import DATABASE_URL


async def main():
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row

        # Реальные вакансии с enbek.kz
        cur = await db.execute("""
            SELECT title, company, region, salary_min, salary_max, industry
            FROM vacancies
            WHERE source_url LIKE '%enbek.kz/ru/vacancy/%~%'
            LIMIT 8
        """)
        rows = await cur.fetchall()
        print("=== РЕАЛЬНЫЕ ВАКАНСИИ С ENBEK.KZ ===")
        for r in rows:
            sal = f"{r['salary_min']} - {r['salary_max']}" if r['salary_min'] else "не указана"
            print(f"  {r['title']}")
            print(f"    Компания: {r['company']} | Регион: {r['region']} | ЗП: {sal} | Отрасль: {r['industry']}")
        print()

        # Статистика
        cur2 = await db.execute(
            "SELECT COUNT(*) as cnt FROM vacancies WHERE source_url LIKE '%enbek.kz/ru/vacancy/%~%'"
        )
        real_count = (await cur2.fetchone())["cnt"]

        cur3 = await db.execute("SELECT COUNT(*) as cnt FROM vacancies")
        total = (await cur3.fetchone())["cnt"]

        cur4 = await db.execute(
            "SELECT COUNT(*) as cnt FROM vacancies WHERE salary_min IS NOT NULL"
        )
        with_salary = (await cur4.fetchone())["cnt"]

        cur5 = await db.execute(
            "SELECT region, COUNT(*) as cnt FROM vacancies WHERE source_url LIKE '%enbek.kz/ru/vacancy/%~%' GROUP BY region ORDER BY cnt DESC LIMIT 5"
        )
        regions = await cur5.fetchall()

        print(f"Реальных вакансий (enbek.kz): {real_count}")
        print(f"Тестовых (seed):               {total - real_count}")
        print(f"Всего в БД:                    {total}")
        print(f"С указанной зарплатой:         {with_salary}")
        print()
        print("Топ регионов (реальные):")
        for r in regions:
            print(f"  {r['region']}: {r['cnt']} вакансий")


if __name__ == "__main__":
    asyncio.run(main())
