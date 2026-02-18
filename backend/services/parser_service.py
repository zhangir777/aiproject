"""
Парсер вакансий с enbek.kz
Правильный URL: /ru/search/vacancy?page=N
Вакансии используют JSON-LD structured data на страницах деталей.
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

from config import PARSER_DELAY_SECONDS, PARSER_USER_AGENT, DATABASE_URL

logger = logging.getLogger(__name__)

ENBEK_BASE = "https://www.enbek.kz"
LIST_URL = f"{ENBEK_BASE}/ru/search/vacancy"

HEADERS = {
    "User-Agent": PARSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,kk-KZ;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://www.enbek.kz/",
}

REGION_MAP = {
    "Алматы": "Алматы",
    "Астана": "Астана",
    "Шымкент": "Шымкент",
    "Алматинская": "Алматинская область",
    "Акмолинская": "Акмолинская область",
    "Актюбинская": "Актюбинская область",
    "Атырауская": "Атырауская область",
    "Восточно-Казахстанская": "Восточно-Казахстанская область",
    "Жамбылская": "Жамбылская область",
    "Западно-Казахстанская": "Западно-Казахстанская область",
    "Карагандинская": "Карагандинская область",
    "Костанайская": "Костанайская область",
    "Кызылординская": "Кызылординская область",
    "Мангистауская": "Мангистауская область",
    "Павлодарская": "Павлодарская область",
    "Северо-Казахстанская": "Северо-Казахстанская область",
    "Туркестанская": "Туркестанская область",
    "Улытауская": "Улытауская область",
    "Жетысуская": "Жетысуская область",
    "Абайская": "Абайская область",
    "Актобе": "Актюбинская область",
    "Актау": "Мангистауская область",
    "Атырау": "Атырауская область",
    "Усть-Каменогорск": "Восточно-Казахстанская область",
    "Семей": "Абайская область",
    "Тараз": "Жамбылская область",
    "Костанай": "Костанайская область",
    "Кызылорда": "Кызылординская область",
    "Павлодар": "Павлодарская область",
    "Петропавловск": "Северо-Казахстанская область",
    "Уральск": "Западно-Казахстанская область",
    "Туркестан": "Туркестанская область",
    "Кокшетау": "Акмолинская область",
}


def normalize_region(location_text: str) -> str:
    if not location_text:
        return "Неизвестно"
    for key, value in REGION_MAP.items():
        if key.lower() in location_text.lower():
            return value
    # Если не нашли — берём первую часть до запятой
    return location_text.split(",")[0].strip() or "Неизвестно"


def parse_salary_value(salary_data: dict) -> tuple[Optional[int], Optional[int]]:
    """Парсит зарплату из JSON-LD baseSalary."""
    try:
        value = salary_data.get("value", {})
        if isinstance(value, dict):
            min_v = value.get("minValue")
            max_v = value.get("maxValue")
            val = value.get("value")
            if min_v:
                return int(float(min_v)), int(float(max_v)) if max_v else int(float(min_v))
            if val:
                return int(float(val)), int(float(val))
        elif isinstance(value, (int, float)):
            return int(value), int(value)
    except Exception:
        pass
    return None, None


def extract_skills_from_text(text: str) -> list[str]:
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
        "управление проектами", "Agile", "Scrum", "1С",
    ]
    found = []
    text_lower = text.lower()
    for skill in known_skills:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:10]


def extract_industry(title: str, category: str = "") -> str:
    combined = (title + " " + category).lower()
    if any(w in combined for w in ["программист", "разработчик", "developer", "it", "data", "devops", "software", "веб", "web"]):
        return "IT"
    elif any(w in combined for w in ["бухгалтер", "финансист", "экономист", "аудитор", "финанс"]):
        return "Финансы и бухгалтерия"
    elif any(w in combined for w in ["врач", "медсестра", "фармацевт", "медицин", "хирург", "стоматолог", "логопед"]):
        return "Медицина"
    elif any(w in combined for w in ["учитель", "педагог", "преподаватель", "воспитатель", "образование"]):
        return "Образование"
    elif any(w in combined for w in ["юрист", "адвокат", "правовой", "право"]):
        return "Юриспруденция"
    elif any(w in combined for w in ["менеджер", "директор", "руководитель", "управл"]):
        return "Управление"
    elif any(w in combined for w in ["маркетолог", "seo", "smm", "реклам", "маркетинг"]):
        return "Маркетинг"
    elif any(w in combined for w in ["инженер", "технолог", "механик", "энергетик"]):
        return "Инженерия"
    elif any(w in combined for w in ["продавец", "торговый", "кассир", "торговл"]):
        return "Торговля"
    elif any(w in combined for w in ["водитель", "логист", "транспорт", "курьер"]):
        return "Логистика"
    elif any(w in combined for w in ["строитель", "прораб", "архитектор", "монтажник"]):
        return "Строительство"
    elif any(w in combined for w in ["повар", "официант", "бармен", "кухня", "ресторан"]):
        return "Общепит"
    elif any(w in combined for w in ["охранник", "безопасность", "security"]):
        return "Безопасность"
    else:
        return "Другое"


class EnbekParser:
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
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

    async def fetch(self, url: str, params: dict = None) -> Optional[BeautifulSoup]:
        """Загрузить страницу с задержкой."""
        try:
            await asyncio.sleep(PARSER_DELAY_SECONDS)
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP {e.response.status_code}: {url}")
        except Exception as e:
            logger.error(f"Ошибка загрузки {url}: {e}")
        return None

    def extract_vacancy_links(self, soup: BeautifulSoup) -> list[str]:
        """Извлечь ссылки на вакансии со страницы списка."""
        links = set()
        # Ищем все ссылки с форматом /ru/vacancy/slug~id
        for a in soup.find_all("a", href=re.compile(r"/ru/vacancy/.+~\d+")):
            href = a.get("href", "")
            if href.startswith("/"):
                href = ENBEK_BASE + href
            links.add(href)
        return list(links)

    def parse_jsonld(self, soup: BeautifulSoup) -> Optional[dict]:
        """Извлечь данные из JSON-LD structured data (самый надёжный способ)."""
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "")
                if data.get("@type") == "JobPosting":
                    return data
            except Exception:
                continue
        return None

    def parse_vacancy_page(self, soup: BeautifulSoup, url: str) -> Optional[dict]:
        """Парсит страницу вакансии. Приоритет: JSON-LD → HTML."""
        try:
            vacancy = {"source_url": url}

            # — JSON-LD (структурированные данные) —
            jsonld = self.parse_jsonld(soup)
            if jsonld:
                vacancy["title"] = jsonld.get("title", "").strip()
                vacancy["company"] = jsonld.get("hiringOrganization", {}).get("name", "").strip() or None

                # Зарплата
                base_salary = jsonld.get("baseSalary", {})
                salary_min, salary_max = parse_salary_value(base_salary)
                vacancy["salary_min"] = salary_min
                vacancy["salary_max"] = salary_max

                # Локация
                location = jsonld.get("jobLocation", {})
                address = location.get("address", {})
                locality = address.get("addressLocality", "") or address.get("addressRegion", "")
                vacancy["city"] = locality.strip() or None
                vacancy["region"] = normalize_region(locality)

                # Дата
                date_posted = jsonld.get("datePosted", "")
                vacancy["published_at"] = date_posted or datetime.now().isoformat()

                # Описание
                desc = jsonld.get("description", "") or ""
                vacancy["description"] = desc[:3000] if desc else None

                # Опыт
                exp_req = jsonld.get("experienceRequirements", "") or ""
                vacancy["experience"] = str(exp_req)[:100] if exp_req else None

            else:
                # — Fallback: парсим HTML напрямую —
                title_el = (
                    soup.find("h1") or
                    soup.find("h2", class_=re.compile(r"title|vacancy|job")) or
                    soup.find("h3")
                )
                vacancy["title"] = title_el.get_text(strip=True) if title_el else "Без названия"

                # Зарплата из текста
                salary_el = soup.find(string=re.compile(r"\d[\d\s]+тг|тенге", re.I))
                if salary_el:
                    nums = re.findall(r"\d[\d\s]+", str(salary_el))
                    nums = [int(n.replace(" ", "")) for n in nums if int(n.replace(" ", "")) > 1000]
                    vacancy["salary_min"] = nums[0] if nums else None
                    vacancy["salary_max"] = nums[-1] if len(nums) > 1 else vacancy.get("salary_min")
                else:
                    vacancy["salary_min"] = None
                    vacancy["salary_max"] = None

                vacancy["company"] = None
                vacancy["region"] = "Неизвестно"
                vacancy["city"] = None
                vacancy["published_at"] = datetime.now().isoformat()
                vacancy["description"] = None
                vacancy["experience"] = None

            # Обязательные поля
            if not vacancy.get("title"):
                return None

            # Навыки из описания
            desc_text = vacancy.get("description") or ""
            skills = extract_skills_from_text(desc_text)
            vacancy["skills"] = json.dumps(skills, ensure_ascii=False)

            # Категория (отрасль) — из страницы если есть
            category_el = soup.find(class_=re.compile(r"category|industry|field|sphere"))
            category_text = category_el.get_text(strip=True) if category_el else ""
            vacancy["industry"] = extract_industry(vacancy.get("title", ""), category_text)
            vacancy["normalized_title"] = vacancy.get("title", "")

            return vacancy

        except Exception as e:
            logger.error(f"Ошибка парсинга {url}: {e}")
            return None

    async def save_vacancy(self, db: aiosqlite.Connection, vacancy: dict) -> bool:
        try:
            await db.execute(
                """INSERT OR IGNORE INTO vacancies
                   (title, company, region, city, salary_min, salary_max,
                    industry, experience, skills, description, source_url,
                    published_at, normalized_title)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    vacancy.get("normalized_title"),
                ),
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            return False

    async def parse_all(self, max_pages: int = 50, max_vacancies: int = 3000) -> int:
        """Парсить все вакансии постранично."""
        saved = 0
        failed_pages = 0

        async with aiosqlite.connect(DATABASE_URL) as db:
            for page_num in range(1, max_pages + 1):
                if saved >= max_vacancies:
                    break

                logger.info(f"[Страница {page_num}/{max_pages}] Загружаем...")
                soup = await self.fetch(LIST_URL, params={"page": page_num})

                if not soup:
                    failed_pages += 1
                    if failed_pages >= 3:
                        logger.error("3 страницы подряд не загрузились, останавливаем")
                        break
                    continue

                failed_pages = 0
                vacancy_urls = self.extract_vacancy_links(soup)
                logger.info(f"  Найдено ссылок: {len(vacancy_urls)}")

                if not vacancy_urls:
                    logger.warning(f"  Нет вакансий на странице {page_num}, проверяем структуру...")
                    # Возможно страница пустая или последняя
                    if page_num > 1:
                        break
                    continue

                for v_url in vacancy_urls:
                    if saved >= max_vacancies:
                        break

                    v_soup = await self.fetch(v_url)
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
                                logger.info(f"  Сохранено: {saved} вакансий")

            await db.commit()

        logger.info(f"Парсинг завершён. Сохранено: {saved}")
        return saved
