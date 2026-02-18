"""
Парсер вакансий с enbek.kz
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Optional

import aiosqlite
import httpx
from bs4 import BeautifulSoup

from config import PARSER_DELAY_SECONDS, PARSER_USER_AGENT, ENBEK_BASE_URL, DATABASE_URL

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": PARSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,kk-KZ;q=0.8",
    "Connection": "keep-alive",
}

REGION_MAP = {
    "Алматы": "Алматы",
    "Астана": "Астана",
    "Шымкент": "Шымкент",
    "Алматинская область": "Алматинская область",
    "Акмолинская область": "Акмолинская область",
    "Актюбинская область": "Актюбинская область",
    "Атырауская область": "Атырауская область",
    "Восточно-Казахстанская область": "Восточно-Казахстанская область",
    "Жамбылская область": "Жамбылская область",
    "Западно-Казахстанская область": "Западно-Казахстанская область",
    "Карагандинская область": "Карагандинская область",
    "Костанайская область": "Костанайская область",
    "Кызылординская область": "Кызылординская область",
    "Мангистауская область": "Мангистауская область",
    "Павлодарская область": "Павлодарская область",
    "Северо-Казахстанская область": "Северо-Казахстанская область",
    "Туркестанская область": "Туркестанская область",
}


def parse_salary(salary_text: str) -> tuple[Optional[int], Optional[int]]:
    """Извлечь диапазон зарплаты из текста."""
    if not salary_text:
        return None, None
    salary_text = salary_text.replace("\xa0", "").replace(" ", "").replace(",", "")
    numbers = re.findall(r"\d+", salary_text)
    numbers = [int(n) for n in numbers if int(n) > 1000]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return numbers[0], numbers[-1]


def normalize_region(region_text: str) -> str:
    """Нормализовать название региона."""
    if not region_text:
        return "Неизвестно"
    region_text = region_text.strip()
    for key, value in REGION_MAP.items():
        if key.lower() in region_text.lower():
            return value
    return region_text


class EnbekParser:
    def __init__(self):
        self.client = None
        self.parsed_count = 0
        self.saved_count = 0

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            headers=HEADERS,
            timeout=30.0,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Загрузить страницу и вернуть BeautifulSoup."""
        try:
            await asyncio.sleep(PARSER_DELAY_SECONDS)
            response = await self.client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except Exception as e:
            logger.error(f"Ошибка загрузки {url}: {e}")
            return None

    def extract_vacancy_list(self, soup: BeautifulSoup) -> list[str]:
        """Извлечь список URL вакансий со страницы списка."""
        urls = []
        # enbek.kz — ищем ссылки на вакансии
        links = soup.find_all("a", href=re.compile(r"/ru/vacancy/\d+"))
        for link in links:
            href = link.get("href", "")
            if href and "/vacancy/" in href:
                full_url = ENBEK_BASE_URL + href if href.startswith("/") else href
                if full_url not in urls:
                    urls.append(full_url)
        return urls

    def parse_vacancy_page(self, soup: BeautifulSoup, url: str) -> Optional[dict]:
        """Парсить страницу отдельной вакансии."""
        try:
            vacancy = {"source_url": url, "published_at": datetime.now().isoformat()}

            # Заголовок
            title_el = soup.find("h1") or soup.find("h2", class_=re.compile(r"title|vacancy"))
            vacancy["title"] = title_el.get_text(strip=True) if title_el else "Без названия"

            # Компания
            company_el = soup.find(class_=re.compile(r"company|employer|organization"))
            vacancy["company"] = company_el.get_text(strip=True) if company_el else None

            # Зарплата
            salary_el = soup.find(class_=re.compile(r"salary|wage|pay"))
            salary_text = salary_el.get_text(strip=True) if salary_el else ""
            salary_min, salary_max = parse_salary(salary_text)
            vacancy["salary_min"] = salary_min
            vacancy["salary_max"] = salary_max

            # Регион
            location_el = soup.find(class_=re.compile(r"location|region|city|address"))
            region_text = location_el.get_text(strip=True) if location_el else ""
            vacancy["region"] = normalize_region(region_text)
            vacancy["city"] = region_text.strip() if region_text else None

            # Описание
            desc_el = soup.find(class_=re.compile(r"description|content|body|detail"))
            vacancy["description"] = desc_el.get_text(strip=True)[:3000] if desc_el else None

            # Навыки из описания (простое извлечение)
            skills = extract_skills_from_text(vacancy.get("description", "") or "")
            vacancy["skills"] = json.dumps(skills, ensure_ascii=False)

            # Опыт
            exp_match = re.search(r"(\d+)\s*(лет|года|год|г\.)", vacancy.get("description", "") or "")
            vacancy["experience"] = f"{exp_match.group(1)} лет" if exp_match else None

            # Отрасль (из URL или категории)
            vacancy["industry"] = extract_industry(vacancy["title"])

            return vacancy
        except Exception as e:
            logger.error(f"Ошибка парсинга вакансии {url}: {e}")
            return None

    async def save_vacancy(self, db: aiosqlite.Connection, vacancy: dict) -> bool:
        """Сохранить вакансию в БД (upsert)."""
        try:
            await db.execute(
                """INSERT OR IGNORE INTO vacancies
                   (title, company, region, city, salary_min, salary_max,
                    industry, experience, skills, description, source_url, published_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    vacancy.get("title"),
                    vacancy.get("company"),
                    vacancy.get("region", "Неизвестно"),
                    vacancy.get("city"),
                    vacancy.get("salary_min"),
                    vacancy.get("salary_max"),
                    vacancy.get("industry"),
                    vacancy.get("experience"),
                    vacancy.get("skills"),
                    vacancy.get("description"),
                    vacancy.get("source_url"),
                    vacancy.get("published_at"),
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения вакансии: {e}")
            return False

    async def parse_all(self, max_pages: int = 50, max_vacancies: int = 3000) -> int:
        """Парсить все вакансии постранично."""
        base_url = f"{ENBEK_BASE_URL}/ru/vacancy"
        saved = 0

        async with aiosqlite.connect(DATABASE_URL) as db:
            for page in range(1, max_pages + 1):
                if saved >= max_vacancies:
                    break

                url = f"{base_url}?page={page}"
                logger.info(f"Парсинг страницы {page}: {url}")
                soup = await self.fetch_page(url)
                if not soup:
                    break

                vacancy_urls = self.extract_vacancy_list(soup)
                if not vacancy_urls:
                    logger.info(f"Страница {page}: вакансий не найдено, завершаем")
                    break

                logger.info(f"Страница {page}: найдено {len(vacancy_urls)} вакансий")

                for v_url in vacancy_urls:
                    if saved >= max_vacancies:
                        break
                    v_soup = await self.fetch_page(v_url)
                    if not v_soup:
                        continue
                    vacancy = self.parse_vacancy_page(v_soup, v_url)
                    if vacancy:
                        ok = await self.save_vacancy(db, vacancy)
                        if ok:
                            saved += 1
                            self.saved_count = saved
                            if saved % 50 == 0:
                                await db.commit()
                                logger.info(f"Сохранено {saved} вакансий")

            await db.commit()

        logger.info(f"Парсинг завершён. Сохранено: {saved} вакансий")
        return saved


def extract_skills_from_text(text: str) -> list[str]:
    """Простое извлечение навыков из текста описания."""
    if not text:
        return []
    known_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "SQL", "Excel",
        "1C", "AutoCAD", "SAP", "C++", "C#", "React", "Vue", "Angular",
        "Node.js", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker",
        "Kubernetes", "Git", "Linux", "Windows", "Microsoft Office",
        "Power BI", "Tableau", "Photoshop", "Illustrator", "Figma",
        "Английский язык", "Казахский язык", "Русский язык",
        "бухгалтерский учёт", "налогообложение", "маркетинг",
        "управление проектами", "Project Management", "Agile", "Scrum",
    ]
    found = []
    text_lower = text.lower()
    for skill in known_skills:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:10]


def extract_industry(title: str) -> str:
    """Определить отрасль по названию вакансии."""
    title_lower = title.lower()
    if any(w in title_lower for w in ["программист", "разработчик", "developer", "it", "data", "devops"]):
        return "IT"
    elif any(w in title_lower for w in ["бухгалтер", "финансист", "экономист", "аудитор"]):
        return "Финансы и бухгалтерия"
    elif any(w in title_lower for w in ["врач", "медсестра", "фармацевт", "медицин"]):
        return "Медицина"
    elif any(w in title_lower for w in ["учитель", "педагог", "преподаватель"]):
        return "Образование"
    elif any(w in title_lower for w in ["юрист", "адвокат", "правовой"]):
        return "Юриспруденция"
    elif any(w in title_lower for w in ["менеджер", "директор", "руководитель"]):
        return "Управление"
    elif any(w in title_lower for w in ["маркетолог", "seo", "smm", "реклам"]):
        return "Маркетинг"
    elif any(w in title_lower for w in ["инженер", "технолог", "механик"]):
        return "Инженерия"
    elif any(w in title_lower for w in ["продавец", "торговый", "кассир"]):
        return "Торговля"
    elif any(w in title_lower for w in ["водитель", "логист", "транспорт"]):
        return "Логистика"
    elif any(w in title_lower for w in ["строитель", "прораб", "архитектор"]):
        return "Строительство"
    else:
        return "Другое"
