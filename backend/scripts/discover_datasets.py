"""
Поиск и анализ датасетов на data.egov.kz + загрузка статичных данных
Запуск: py -X utf8 scripts/discover_datasets.py
"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

from database import init_db
from services.egov_service import EgovService, KNOWN_DATASETS, STATIC_EDUCATION_DATA, STATIC_LABOUR_STATS


async def main():
    print("=" * 60)
    print("EnbekAI — data.egov.kz Dataset Discovery")
    print("=" * 60)

    await init_db()
    svc = EgovService()

    try:
        # Статус API ключа
        if svc.has_api_key:
            print("\n[OK] EGOV_API_KEY найден — проверяем датасеты...")
            results = await svc.probe_all_datasets()
            accessible = [r for r in results if r["accessible"]]
            inaccessible = [r for r in results if not r["accessible"]]

            print(f"\nДоступны: {len(accessible)} датасетов")
            for r in accessible:
                print(f"  + {r['name']}: {r['description']}")
                print(f"    Поля: {', '.join(r['fields'][:6])}")

            if inaccessible:
                print(f"\nНедоступны: {len(inaccessible)}")
                for r in inaccessible:
                    print(f"  - {r['name']}: {r['description']}")
        else:
            print("\n[WARN] EGOV_API_KEY не задан в .env")
            print("  Для доступа к API: зарегистрируйтесь на data.egov.kz")
            print("  и добавьте EGOV_API_KEY=ваш_ключ в backend/.env")
            print()
            print(f"  Известные датасеты ({len(KNOWN_DATASETS)}):")
            for name, info in KNOWN_DATASETS.items():
                print(f"    - {name}: {info['description']}")

        # Всегда загружаем статичные данные
        print("\n[DATA] Загрузка официальной статистики МОН РК и stat.gov.kz...")
        count = await svc.seed_static_data()
        print(f"  Образовательная статистика: {count} записей в БД")
        print(f"  Данные по безработице: {len(STATIC_LABOUR_STATS)} регионов")
        print()
        print("  Покрытые регионы:")
        regions = set(r for r, *_ in STATIC_EDUCATION_DATA)
        for rg in sorted(regions):
            print(f"    - {rg}")

        print()
        print("[STAT] Статистика безработицы 2024 (официальные данные):")
        for region, rate, year in sorted(STATIC_LABOUR_STATS, key=lambda x: x[1]):
            bar = "#" * int(rate)
            print(f"  {region:<35} {rate:.1f}% {bar}")

    finally:
        await svc.close()

    print("\n" + "=" * 60)
    print("[OK] data.egov.kz клиент готов к работе")


if __name__ == "__main__":
    asyncio.run(main())
