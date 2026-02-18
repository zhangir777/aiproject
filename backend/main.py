import os
import json
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import aiosqlite
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, DEBUG, DATABASE_URL
from database import init_db
from routers import dashboard, chat, career, vacancies

# ─────────────────────────────────────────────────────────
# Данные для генерации вакансий
# ─────────────────────────────────────────────────────────

_PROFESSIONS = [
    ("Программист",           "IT",             ["Python", "JavaScript", "SQL", "Git", "Docker", "React"],          350000, 1200000),
    ("Аналитик данных",       "IT",             ["Python", "SQL", "Power BI", "Excel", "Tableau", "Machine Learning"], 400000, 1100000),
    ("Системный администратор","IT",             ["Linux", "Windows Server", "Сети", "VMware", "Cisco"],             280000,  750000),
    ("Дизайнер",              "IT",             ["Figma", "Photoshop", "Illustrator", "UI/UX", "Adobe XD"],         250000,  700000),
    ("Бухгалтер",             "Финансы",        ["1C", "Excel", "МСФО", "Налоговый учет", "Бухгалтерская отчетность"], 200000, 600000),
    ("Экономист",             "Финансы",        ["Финансовый анализ", "Excel", "1C", "Бюджетирование", "МСФО"],     250000,  650000),
    ("Юрист",                 "Финансы",        ["Гражданское право", "Договоры", "Суд", "Корпоративное право"],    280000,  750000),
    ("HR-менеджер",           "Финансы",        ["Подбор персонала", "1C ЗУП", "Трудовое право", "KPI"],            200000,  500000),
    ("Менеджер по продажам",  "Торговля",       ["CRM", "Переговоры", "Excel", "1C", "B2B"],                        200000,  800000),
    ("Маркетолог",            "Торговля",       ["SMM", "Google Analytics", "SEO", "Таргетинг", "Контент"],         220000,  650000),
    ("Продавец-консультант",  "Торговля",       ["Обслуживание клиентов", "1C", "Кассовый аппарат", "Продажи"],     150000,  380000),
    ("Логист",                "Транспорт",      ["Логистика", "Excel", "1C", "ВЭД", "Таможня"],                     200000,  550000),
    ("Инженер",               "Промышленность", ["AutoCAD", "Проектирование", "Технические чертежи", "ПДД"],        280000,  850000),
    ("Строитель",             "Строительство",  ["Строительство", "Чтение чертежей", "Сварка", "Бетонирование"],    200000,  600000),
    ("Учитель",               "Образование",    ["Педагогика", "Казахский язык", "Русский язык", "Методика"],       150000,  350000),
    ("Врач",                  "Медицина",       ["Диагностика", "МКБ-10", "УЗИ", "Медицинская документация"],       300000,  900000),
    ("Фармацевт",             "Медицина",       ["Фармакология", "1C", "Работа с клиентами", "GMP"],                220000,  500000),
    ("Повар",                 "Общепит",        ["Кулинария", "ХААСП", "Технологические карты", "Су-вид"],          160000,  420000),
]

_REGIONS = [
    ("Алматы", 22),
    ("Астана", 18),
    ("Шымкент", 9),
    ("Карагандинская область", 7),
    ("Алматинская область", 5),
    ("Атырауская область", 5),
    ("Мангистауская область", 5),
    ("Актюбинская область", 4),
    ("Восточно-Казахстанская область", 4),
    ("Павлодарская область", 4),
    ("Жамбылская область", 3),
    ("Туркестанская область", 3),
    ("Костанайская область", 3),
    ("Северо-Казахстанская область", 2),
    ("Западно-Казахстанская область", 2),
    ("Акмолинская область", 2),
    ("Кызылординская область", 2),
]

_COMPANIES = [
    "Kaspi Bank", "Halyk Bank", "ForteBank", "Jusan Bank", "Freedom Finance",
    "Beeline Kazakhstan", "Kcell", "Kazakhtelecom", "Tele2 Kazakhstan", "Activ",
    "KazMunaiGaz", "Air Astana", "Kolesa Group", "Choco Family", "2GIS Kazakhstan",
    "KPMG Kazakhstan", "Deloitte Kazakhstan", "PwC Kazakhstan", "Ernst & Young KZ",
    "Magnum Cash&Carry", "Technodom", "Sulpak", "Fix Price Kazakhstan", "Dodos",
    "BI Group", "Базис-А", "Алматы Строй", "КазСтрой", "Нурлы Жол Строй",
    "СемейМед", "Клиника Он Клиник", "КазМедЦентр", "Медикер", "Инвитро КЗ",
    "Samsung Kazakhstan", "LG Electronics KZ", "Huawei Kazakhstan", "Apple Premium KZ",
    "Яндекс Казахстан", "Wolt Kazakhstan", "Glovo Kazakhstan", "inDriver",
    "Центр Обслуживания", "АЛЕЛЬ АВТО", "Агентство Алматы", "КазАгро", "Эффект",
]

_EXPERIENCE = ["Без опыта", "1-3 года", "3-5 лет", "Более 5 лет"]


async def _seed_vacancies_if_empty():
    """Генерирует 500 реалистичных вакансий если таблица пуста."""
    async with aiosqlite.connect(DATABASE_URL, timeout=30) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        cur = await db.execute("SELECT COUNT(*) FROM vacancies")
        count = (await cur.fetchone())[0]
        if count > 0:
            print(f"[OK] Vacancies already exist: {count}")
            return

        rng = random.Random(42)
        region_names = [r[0] for r in _REGIONS]
        region_weights = [r[1] for r in _REGIONS]

        rows = []
        now = datetime.now()

        for i in range(500):
            prof_name, industry, skills, sal_min_base, sal_max_base = rng.choice(_PROFESSIONS)
            region = rng.choices(region_names, weights=region_weights, k=1)[0]
            company = rng.choice(_COMPANIES)
            experience = rng.choice(_EXPERIENCE)

            # Реалистичные зарплаты с разбросом ±30%
            factor = rng.uniform(0.7, 1.3)
            sal_min = int(sal_min_base * factor / 10000) * 10000
            sal_max = int(sal_max_base * factor / 10000) * 10000

            # Навыки — случайная выборка из списка профессии
            chosen_skills = rng.sample(skills, k=min(rng.randint(2, 4), len(skills)))

            # Дата публикации — последние 90 дней
            days_ago = rng.randint(0, 90)
            published = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")

            rows.append((
                prof_name,                         # title
                company,                           # company
                region,                            # region
                region,                            # city
                sal_min,                           # salary_min
                sal_max,                           # salary_max
                industry,                          # industry
                experience,                        # experience
                json.dumps(chosen_skills, ensure_ascii=False),  # skills
                f"Требуется {prof_name} в компанию {company}. Опыт: {experience}.",  # description
                f"https://enbek.kz/vacancy/{i+1}", # source_url
                published,                         # published_at
                prof_name,                         # normalized_title
            ))

        await db.executemany("""
            INSERT OR IGNORE INTO vacancies
            (title, company, region, city, salary_min, salary_max,
             industry, experience, skills, description, source_url,
             published_at, normalized_title)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)
        await db.commit()
        print(f"[OK] Seeded 500 vacancies")


async def _calculate_stats():
    """Агрегирует данные из vacancies в market_stats."""
    from services.analytics_service import AnalyticsService
    try:
        svc = AnalyticsService()
        await svc.update_market_stats()
        print("[OK] Market stats calculated")
    except Exception as e:
        print(f"[WARN] Stats calculation skipped: {e}")


# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[START] EnbekAI starting...")
    await init_db()
    print("[OK] Database ready")
    await _seed_vacancies_if_empty()
    await _calculate_stats()
    yield
    print("[STOP] EnbekAI shutting down")


app = FastAPI(
    title="EnbekAI API",
    description="AI-аналитик рынка труда Казахстана",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(chat.router, prefix="/api", tags=["AI Chat"])
app.include_router(career.router, prefix="/api", tags=["Career Plan"])
app.include_router(vacancies.router, prefix="/api/vacancies", tags=["Vacancies"])


@app.get("/")
async def root():
    return {
        "service": "EnbekAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=DEBUG)
