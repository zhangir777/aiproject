import aiosqlite
import asyncio
import os
from config import DATABASE_URL

DB_PATH = DATABASE_URL


async def get_db():
    """Dependency для FastAPI — получить соединение с БД."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db():
    """Инициализация БД: создание таблиц и начальное заполнение."""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            -- Вакансии
            CREATE TABLE IF NOT EXISTS vacancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                region TEXT NOT NULL,
                city TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                industry TEXT,
                experience TEXT,
                skills TEXT,
                description TEXT,
                source_url TEXT UNIQUE,
                published_at TEXT,
                parsed_at TEXT DEFAULT (datetime('now')),
                normalized_title TEXT,
                skill_tags TEXT
            );

            -- Агрегированная статистика по рынку
            CREATE TABLE IF NOT EXISTS market_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                profession TEXT NOT NULL,
                avg_salary INTEGER,
                median_salary INTEGER,
                vacancy_count INTEGER,
                competition_ratio REAL,
                top_skills TEXT,
                period TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(region, profession, period)
            );

            -- Данные образования (из data.egov.kz)
            CREATE TABLE IF NOT EXISTS education_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT,
                institution TEXT,
                specialty TEXT,
                graduates_count INTEGER,
                year INTEGER,
                dataset_source TEXT,
                fetched_at TEXT DEFAULT (datetime('now'))
            );

            -- Регионы Казахстана (справочник)
            CREATE TABLE IF NOT EXISTS regions (
                id INTEGER PRIMARY KEY,
                name_ru TEXT NOT NULL,
                name_kz TEXT,
                latitude REAL,
                longitude REAL,
                population INTEGER
            );

            -- Кэш AI-ответов
            CREATE TABLE IF NOT EXISTS ai_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT UNIQUE,
                query_text TEXT,
                response_text TEXT,
                model_used TEXT,
                tokens_used INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );

            -- Индексы
            CREATE INDEX IF NOT EXISTS idx_vacancies_region ON vacancies(region);
            CREATE INDEX IF NOT EXISTS idx_vacancies_industry ON vacancies(industry);
            CREATE INDEX IF NOT EXISTS idx_vacancies_title ON vacancies(normalized_title);
            CREATE INDEX IF NOT EXISTS idx_market_stats_region ON market_stats(region, period);
            CREATE INDEX IF NOT EXISTS idx_ai_cache_hash ON ai_cache(query_hash);
        """)
        await db.commit()

        # Заполнить регионы если пустые
        cursor = await db.execute("SELECT COUNT(*) FROM regions")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await seed_regions(db)
            await db.commit()
            print("✅ Регионы Казахстана загружены в БД")


async def seed_regions(db):
    """Заполнить справочник регионов Казахстана."""
    regions = [
        (1, "Алматы", "Алматы", 43.238949, 76.945465, 2200000),
        (2, "Астана", "Астана", 51.128207, 71.430411, 1400000),
        (3, "Шымкент", "Шымкент", 42.315514, 69.597039, 1200000),
        (4, "Алматинская область", "Алматы облысы", 44.200000, 77.600000, 2100000),
        (5, "Акмолинская область", "Ақмола облысы", 51.700000, 70.400000, 740000),
        (6, "Актюбинская область", "Ақтөбе облысы", 50.283000, 57.167000, 910000),
        (7, "Атырауская область", "Атырау облысы", 47.117000, 51.883000, 680000),
        (8, "Восточно-Казахстанская область", "Шығыс Қазақстан облысы", 49.967000, 82.617000, 1350000),
        (9, "Жамбылская область", "Жамбыл облысы", 42.900000, 71.383000, 1200000),
        (10, "Западно-Казахстанская область", "Батыс Қазақстан облысы", 51.233000, 51.367000, 720000),
        (11, "Карагандинская область", "Қарағанды облысы", 49.800000, 73.100000, 1350000),
        (12, "Костанайская область", "Қостанай облысы", 53.217000, 63.617000, 840000),
        (13, "Кызылординская область", "Қызылорда облысы", 44.850000, 65.517000, 840000),
        (14, "Мангистауская область", "Маңғыстау облысы", 43.667000, 51.167000, 760000),
        (15, "Павлодарская область", "Павлодар облысы", 52.283000, 76.967000, 750000),
        (16, "Северо-Казахстанская область", "Солтүстік Қазақстан облысы", 54.017000, 69.267000, 530000),
        (17, "Туркестанская область", "Түркістан облысы", 41.300000, 69.600000, 2100000),
        (18, "Улытауская область", "Ұлытау облысы", 48.617000, 67.800000, 230000),
        (19, "Жетысуская область", "Жетісу облысы", 44.033000, 79.000000, 660000),
        (20, "Абайская область", "Абай облысы", 49.967000, 80.233000, 620000),
    ]
    await db.executemany(
        "INSERT OR IGNORE INTO regions (id, name_ru, name_kz, latitude, longitude, population) VALUES (?, ?, ?, ?, ?, ?)",
        regions
    )


if __name__ == "__main__":
    asyncio.run(init_db())
    print("✅ База данных инициализирована")
