"""
Скрипт парсинга вакансий с enbek.kz
Запуск: python scripts/parse_enbek.py [max_pages] [max_vacancies]

Правильный URL: https://www.enbek.kz/ru/search/vacancy?page=N
Данные берутся из JSON-LD structured data на каждой странице вакансии.
"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db
from services.parser_service import EnbekParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def quick_test():
    """Тест: спарсить одну страницу и вернуть результат."""
    import httpx
    from bs4 import BeautifulSoup
    from services.parser_service import ENBEK_BASE, LIST_URL, HEADERS

    logger.info("Тест подключения к enbek.kz...")
    async with httpx.AsyncClient(headers=HEADERS, timeout=20.0, follow_redirects=True) as client:
        try:
            r = await client.get(LIST_URL, params={"page": 1})
            logger.info(f"HTTP {r.status_code} — {LIST_URL}")
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "lxml")
                import re
                links = soup.find_all("a", href=re.compile(r"/ru/vacancy/.+~\d+"))
                logger.info(f"Найдено ссылок на вакансии: {len(links)}")
                if links:
                    logger.info(f"Пример: {links[0]['href']}")
                return r.status_code == 200 and len(links) > 0
            return False
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False


async def main():
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    max_vacancies = int(sys.argv[2]) if len(sys.argv) > 2 else 2000

    logger.info("=" * 50)
    logger.info("EnbekAI — Парсер enbek.kz")
    logger.info(f"Страниц: {max_pages}, Вакансий макс: {max_vacancies}")
    logger.info(f"Задержка: 2.5с между запросами")
    logger.info("=" * 50)

    await init_db()

    # Сначала тест подключения
    ok = await quick_test()
    if not ok:
        logger.warning("enbek.kz недоступен или структура изменилась!")
        logger.info("Запустите seed_data.py для тестовых данных:")
        logger.info("  py scripts/seed_data.py 2000")
        return

    async with EnbekParser() as parser:
        saved = await parser.parse_all(max_pages=max_pages, max_vacancies=max_vacancies)
        logger.info(f"ИТОГО сохранено: {saved} реальных вакансий")

    if saved < 100:
        logger.warning(f"Мало данных ({saved}). Добавляем тестовые...")
        from scripts.seed_data import seed_vacancies
        await seed_vacancies(500)


if __name__ == "__main__":
    asyncio.run(main())
