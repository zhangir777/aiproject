"""
Скрипт парсинга вакансий с enbek.kz
Запуск: python scripts/parse_enbek.py [max_pages] [max_vacancies]
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
from services.parser_service import EnbekParser


async def main():
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    max_vacancies = int(sys.argv[2]) if len(sys.argv) > 2 else 2000

    print(f"🔍 Запуск парсера enbek.kz")
    print(f"   Максимум страниц: {max_pages}")
    print(f"   Максимум вакансий: {max_vacancies}")
    print(f"   Задержка между запросами: 2.5 секунды")
    print()

    await init_db()

    async with EnbekParser() as parser:
        try:
            saved = await parser.parse_all(max_pages=max_pages, max_vacancies=max_vacancies)
            print(f"\n✅ Парсинг завершён! Сохранено {saved} вакансий")
        except Exception as e:
            print(f"\n❌ Ошибка парсинга: {e}")
            print("   Используйте seed_data.py для тестовых данных:")
            print("   python scripts/seed_data.py 1000")


if __name__ == "__main__":
    asyncio.run(main())
