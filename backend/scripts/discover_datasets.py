"""
Поиск и анализ датасетов на data.egov.kz
Запуск: python scripts/discover_datasets.py
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

EGOV_BASE = "https://data.egov.kz/api/v4"
HEADERS = {"User-Agent": "EnbekAI Research Bot/1.0"}

# Датасеты для проверки
DATASETS_TO_CHECK = [
    "medorg",           # Медицинские организации
    "universities",     # Университеты
    "colleges",         # Колледжи
    "graduates",        # Выпускники
    "employment",       # Занятость
    "labour",           # Рынок труда
    "vacancies",        # Вакансии
    "organizations",    # Организации
    "population",       # Население
    "regions",          # Регионы
    "education",        # Образование
    "schools",          # Школы
    "salary",           # Зарплаты
    "unemployment",     # Безработица
]


async def check_dataset(client: httpx.AsyncClient, name: str) -> dict | None:
    """Проверить наличие и размер датасета."""
    try:
        url = f"{EGOV_BASE}/{name}/v1"
        params = {"source": json.dumps({"size": 5})}
        response = await client.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", {})
            total = hits.get("total", {})
            if isinstance(total, dict):
                total_count = total.get("value", 0)
            else:
                total_count = total or 0

            sample = hits.get("hits", [])
            sample_data = [h.get("_source", {}) for h in sample[:2]]

            return {
                "name": name,
                "total": total_count,
                "fields": list(sample_data[0].keys()) if sample_data else [],
                "sample": sample_data[0] if sample_data else None,
            }
    except Exception as e:
        pass
    return None


async def main():
    print("🔍 Поиск датасетов на data.egov.kz...")
    print("=" * 60)

    async with httpx.AsyncClient(headers=HEADERS) as client:
        found = []
        for ds_name in DATASETS_TO_CHECK:
            result = await check_dataset(client, ds_name)
            if result and result["total"] > 0:
                found.append(result)
                print(f"✅ {ds_name}: {result['total']} записей")
                print(f"   Поля: {', '.join(result['fields'][:8])}")
                if result["sample"]:
                    print(f"   Пример: {str(result['sample'])[:150]}...")
                print()
            else:
                print(f"❌ {ds_name}: недоступен")

            await asyncio.sleep(0.5)

    print("=" * 60)
    print(f"\n📊 Найдено {len(found)} доступных датасетов")
    if found:
        print("\nРелевантные датасеты:")
        for ds in found:
            print(f"  - {ds['name']}: {ds['total']} записей | {', '.join(ds['fields'][:5])}")


if __name__ == "__main__":
    asyncio.run(main())
