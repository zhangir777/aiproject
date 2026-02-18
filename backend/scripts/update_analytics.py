"""
Обновление аналитической статистики:
 1. Распределяем даты seed-вакансий по последним 6 месяцам (для трендов)
 2. Заполняем таблицу market_stats агрегированными данными
 3. Печатаем итоговую статистику

Запуск: py -X utf8 scripts/update_analytics.py
"""
import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

import aiosqlite
from config import DATABASE_URL
from services.analytics_service import get_analytics_service


async def distribute_seed_dates():
    """
    Раздаём seed-вакансиям parsed_at по последним 6 месяцам,
    имитируя постепенный рост рынка (меньше в прошлом, больше сейчас).
    Реальные вакансии с enbek.kz не трогаем.
    """
    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")

        # Считаем seed-вакансии (у них нет реальных URL enbek.kz)
        cur = await db.execute(
            "SELECT id FROM vacancies WHERE source_url NOT LIKE '%enbek.kz/ru/vacancy/%~%' ORDER BY id"
        )
        seed_ids = [row[0] for row in await cur.fetchall()]

        if not seed_ids:
            print("  Seed-вакансий не найдено.")
            return 0

        # Распределение по месяцам (доля от старых к новым)
        # 6 месяцев назад → сейчас, с нарастанием
        weights = [0.08, 0.10, 0.14, 0.18, 0.22, 0.28]  # сумма = 1.0
        total = len(seed_ids)
        counts = [int(total * w) for w in weights]
        # Добавляем остаток в последний месяц
        counts[-1] += total - sum(counts)

        # Генерируем даты для каждого месяца
        from datetime import datetime, timedelta
        import random
        random.seed(42)

        assignments = []
        idx = 0
        for month_back in range(5, -1, -1):  # 5 месяцев назад → 0 (текущий)
            month_count = counts[5 - month_back]
            base_date = datetime.now() - timedelta(days=30 * month_back)
            for _ in range(month_count):
                if idx >= len(seed_ids):
                    break
                # Случайный день внутри месяца
                offset = random.randint(0, 28)
                dt = base_date - timedelta(days=offset)
                assignments.append((dt.strftime("%Y-%m-%d %H:%M:%S"), seed_ids[idx]))
                idx += 1

        await db.executemany(
            "UPDATE vacancies SET parsed_at = ? WHERE id = ?",
            assignments
        )
        await db.commit()
        print(f"  Обновлено дат: {len(assignments)} seed-вакансий")
        return len(assignments)


async def verify_trends(months: int = 6):
    """Показать распределение по месяцам."""
    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row

        from datetime import datetime, timedelta
        print("\n  Тренды по месяцам:")
        now = datetime.now()
        for i in range(months - 1, -1, -1):
            d = now - timedelta(days=30 * i)
            period = d.strftime("%Y-%m")
            cur = await db.execute(
                "SELECT COUNT(*) as cnt FROM vacancies WHERE strftime('%Y-%m', parsed_at) = ?",
                (period,)
            )
            row = await cur.fetchone()
            bar = "#" * (row["cnt"] // 50)
            print(f"    {period}: {row['cnt']:>5} вакансий  {bar}")


async def main():
    print("=" * 60)
    print("EnbekAI — Обновление аналитики")
    print("=" * 60)

    svc = get_analytics_service()

    # 1. Распределяем даты seed-данных
    print("\n[1/3] Распределение дат seed-вакансий по 6 месяцам...")
    updated = await distribute_seed_dates()
    await verify_trends()

    # 2. Обновляем market_stats
    print("\n[2/3] Заполнение таблицы market_stats...")
    await svc.update_market_stats()

    # Проверяем результат
    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT COUNT(*) as cnt FROM market_stats")
        ms_count = (await cur.fetchone())["cnt"]
        print(f"  market_stats: {ms_count} записей")

        cur = await db.execute(
            "SELECT region, profession, vacancy_count, avg_salary FROM market_stats "
            "ORDER BY vacancy_count DESC LIMIT 10"
        )
        rows = await cur.fetchall()
        print("\n  Топ 10 пар (регион + профессия):")
        for r in rows:
            sal = f"{r['avg_salary']:,}" if r['avg_salary'] else "нет данных"
            print(f"    {r['region']:<35} {r['profession']:<30} {r['vacancy_count']:>4} вак | {sal} T")

    # 3. Итоговый обзор
    print("\n[3/3] Общая статистика рынка:")
    overview = await svc.get_overview()
    print(f"  Всего вакансий:    {overview['total_vacancies']}")
    print(f"  Средняя зарплата:  {overview['avg_salary']:,} T" if overview['avg_salary'] else "  Средняя зарплата:  нет данных")
    print(f"  Топ регион:        {overview['top_region']}")
    print(f"  Топ профессия:     {overview['top_profession']}")
    print(f"  Регионов:          {overview['regions_count']}")

    print("\n  Топ профессий (все регионы):")
    top_profs = await svc.get_top_professions(limit=8)
    for p in top_profs:
        sal = f"{p['avg_salary']:,}" if p['avg_salary'] else "—"
        print(f"    {p['profession']:<35} {p['vacancy_count']:>4} вак | {sal} T")

    print("\n  Зарплаты по регионам (топ-8):")
    sal_by_reg = await svc.get_salary_by_region()
    for r in sal_by_reg[:8]:
        print(f"    {r['region']:<35} avg {r['avg_salary']:,} T" if r['avg_salary'] else f"    {r['region']}")

    print("\n" + "=" * 60)
    print("[OK] Аналитика обновлена")


if __name__ == "__main__":
    asyncio.run(main())
