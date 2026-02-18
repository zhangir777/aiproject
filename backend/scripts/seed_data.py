"""
Скрипт заполнения БД реалистичными тестовыми данными.
Используется как fallback если парсер enbek.kz не работает.
"""
import asyncio
import json
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiosqlite
from database import init_db
from config import DATABASE_URL

REGIONS = [
    "Алматы", "Астана", "Шымкент", "Карагандинская область",
    "Алматинская область", "Актюбинская область", "Атырауская область",
    "Восточно-Казахстанская область", "Мангистауская область",
    "Павлодарская область", "Туркестанская область",
]

VACANCIES_DATA = [
    # IT
    {"title": "Python разработчик", "industry": "IT", "salary_min": 400000, "salary_max": 800000,
     "skills": ["Python", "Django", "SQL", "Git", "Docker"]},
    {"title": "Frontend разработчик (React)", "industry": "IT", "salary_min": 350000, "salary_max": 700000,
     "skills": ["JavaScript", "React", "TypeScript", "CSS", "Git"]},
    {"title": "Full-stack разработчик", "industry": "IT", "salary_min": 450000, "salary_max": 900000,
     "skills": ["JavaScript", "Python", "React", "SQL", "Docker"]},
    {"title": "Data Scientist", "industry": "IT", "salary_min": 500000, "salary_max": 1000000,
     "skills": ["Python", "SQL", "Machine Learning", "Pandas", "TensorFlow"]},
    {"title": "DevOps инженер", "industry": "IT", "salary_min": 500000, "salary_max": 950000,
     "skills": ["Docker", "Kubernetes", "Linux", "CI/CD", "AWS"]},
    {"title": "Backend разработчик (Java)", "industry": "IT", "salary_min": 420000, "salary_max": 850000,
     "skills": ["Java", "Spring Boot", "SQL", "Git", "Microservices"]},
    {"title": "Мобильный разработчик (Android)", "industry": "IT", "salary_min": 380000, "salary_max": 750000,
     "skills": ["Kotlin", "Java", "Android SDK", "Git", "SQL"]},
    {"title": "QA инженер", "industry": "IT", "salary_min": 280000, "salary_max": 550000,
     "skills": ["Python", "Selenium", "Postman", "SQL", "Git"]},
    {"title": "Системный администратор", "industry": "IT", "salary_min": 250000, "salary_max": 500000,
     "skills": ["Linux", "Windows", "Network", "VMware", "Bash"]},
    {"title": "Data Analyst", "industry": "IT", "salary_min": 350000, "salary_max": 700000,
     "skills": ["SQL", "Python", "Power BI", "Excel", "Tableau"]},
    {"title": "UI/UX Дизайнер", "industry": "IT", "salary_min": 300000, "salary_max": 600000,
     "skills": ["Figma", "Adobe XD", "Photoshop", "Illustrator"]},
    {"title": "Продуктовый менеджер", "industry": "IT", "salary_min": 450000, "salary_max": 900000,
     "skills": ["Agile", "Scrum", "Jira", "Product Analytics", "SQL"]},

    # Финансы
    {"title": "Бухгалтер", "industry": "Финансы и бухгалтерия", "salary_min": 180000, "salary_max": 350000,
     "skills": ["1C", "Excel", "бухгалтерский учёт", "налогообложение"]},
    {"title": "Главный бухгалтер", "industry": "Финансы и бухгалтерия", "salary_min": 350000, "salary_max": 600000,
     "skills": ["1C", "Excel", "МСФО", "налогообложение", "финансовая отчётность"]},
    {"title": "Финансовый аналитик", "industry": "Финансы и бухгалтерия", "salary_min": 350000, "salary_max": 700000,
     "skills": ["Excel", "SQL", "Power BI", "финансовый анализ", "Python"]},
    {"title": "Экономист", "industry": "Финансы и бухгалтерия", "salary_min": 200000, "salary_max": 400000,
     "skills": ["Excel", "1C", "финансовый анализ", "бухгалтерский учёт"]},
    {"title": "Финансовый директор (CFO)", "industry": "Финансы и бухгалтерия", "salary_min": 700000, "salary_max": 1500000,
     "skills": ["МСФО", "управленческий учёт", "Excel", "стратегическое планирование"]},
    {"title": "Кредитный аналитик", "industry": "Финансы и бухгалтерия", "salary_min": 280000, "salary_max": 500000,
     "skills": ["Excel", "финансовый анализ", "SQL", "кредитный анализ"]},

    # Медицина
    {"title": "Врач общей практики", "industry": "Медицина", "salary_min": 200000, "salary_max": 450000,
     "skills": ["диагностика", "лечение", "Казахский язык", "Русский язык"]},
    {"title": "Хирург", "industry": "Медицина", "salary_min": 350000, "salary_max": 700000,
     "skills": ["хирургия", "анестезиология", "диагностика"]},
    {"title": "Стоматолог", "industry": "Медицина", "salary_min": 300000, "salary_max": 800000,
     "skills": ["стоматология", "ортодонтия", "имплантология"]},
    {"title": "Медицинская сестра", "industry": "Медицина", "salary_min": 130000, "salary_max": 250000,
     "skills": ["уход за пациентами", "инъекции", "первая помощь"]},
    {"title": "Фармацевт", "industry": "Медицина", "salary_min": 180000, "salary_max": 350000,
     "skills": ["фармакология", "консультирование", "1C"]},

    # Образование
    {"title": "Учитель математики", "industry": "Образование", "salary_min": 120000, "salary_max": 250000,
     "skills": ["математика", "педагогика", "Казахский язык"]},
    {"title": "Преподаватель английского языка", "industry": "Образование", "salary_min": 150000, "salary_max": 350000,
     "skills": ["Английский язык", "педагогика", "IELTS"]},
    {"title": "Школьный психолог", "industry": "Образование", "salary_min": 130000, "salary_max": 280000,
     "skills": ["психология", "консультирование", "диагностика"]},

    # Управление
    {"title": "Менеджер по продажам", "industry": "Управление", "salary_min": 200000, "salary_max": 600000,
     "skills": ["переговоры", "CRM", "Excel", "коммуникации"]},
    {"title": "Руководитель проекта", "industry": "Управление", "salary_min": 400000, "salary_max": 800000,
     "skills": ["Agile", "Scrum", "MS Project", "Jira", "управление командой"]},
    {"title": "HR менеджер", "industry": "Управление", "salary_min": 250000, "salary_max": 500000,
     "skills": ["рекрутинг", "1C", "Excel", "трудовое право"]},
    {"title": "Генеральный директор", "industry": "Управление", "salary_min": 800000, "salary_max": 2000000,
     "skills": ["стратегическое управление", "финансы", "переговоры"]},

    # Маркетинг
    {"title": "SMM менеджер", "industry": "Маркетинг", "salary_min": 180000, "salary_max": 400000,
     "skills": ["Instagram", "Facebook", "Canva", "таргетинг", "контент"]},
    {"title": "Маркетолог", "industry": "Маркетинг", "salary_min": 250000, "salary_max": 550000,
     "skills": ["Google Ads", "SEO", "Excel", "аналитика", "контент-маркетинг"]},
    {"title": "Контент-менеджер", "industry": "Маркетинг", "salary_min": 150000, "salary_max": 350000,
     "skills": ["копирайтинг", "SEO", "WordPress", "Canva"]},

    # Инженерия
    {"title": "Инженер-строитель", "industry": "Инженерия", "salary_min": 250000, "salary_max": 550000,
     "skills": ["AutoCAD", "строительные нормы", "Excel", "управление проектами"]},
    {"title": "Электрик", "industry": "Инженерия", "salary_min": 200000, "salary_max": 450000,
     "skills": ["электромонтаж", "ПТЭ", "безопасность"]},
    {"title": "Нефтяной инженер", "industry": "Инженерия", "salary_min": 500000, "salary_max": 1200000,
     "skills": ["нефтедобыча", "AutoCAD", "SAP", "геология"]},
    {"title": "Механик", "industry": "Инженерия", "salary_min": 180000, "salary_max": 400000,
     "skills": ["механика", "диагностика", "ремонт"]},

    # Юриспруденция
    {"title": "Юрист", "industry": "Юриспруденция", "salary_min": 250000, "salary_max": 600000,
     "skills": ["гражданское право", "договорное право", "трудовое право", "Excel"]},
    {"title": "Корпоративный юрист", "industry": "Юриспруденция", "salary_min": 400000, "salary_max": 900000,
     "skills": ["корпоративное право", "M&A", "Английский язык", "договорное право"]},

    # Логистика
    {"title": "Водитель категории B", "industry": "Логистика", "salary_min": 150000, "salary_max": 300000,
     "skills": ["вождение", "знание города", "GPS навигация"]},
    {"title": "Логист", "industry": "Логистика", "salary_min": 250000, "salary_max": 500000,
     "skills": ["1C", "Excel", "таможенное оформление", "ВЭД"]},
    {"title": "Менеджер по закупкам", "industry": "Логистика", "salary_min": 280000, "salary_max": 550000,
     "skills": ["переговоры", "1C", "Excel", "тендеры", "SAP"]},

    # Торговля
    {"title": "Продавец-консультант", "industry": "Торговля", "salary_min": 120000, "salary_max": 250000,
     "skills": ["продажи", "1C", "коммуникации"]},
    {"title": "Кассир", "industry": "Торговля", "salary_min": 100000, "salary_max": 200000,
     "skills": ["1C", "ККМ", "внимательность"]},

    # Строительство
    {"title": "Прораб", "industry": "Строительство", "salary_min": 300000, "salary_max": 650000,
     "skills": ["управление стройкой", "AutoCAD", "строительные нормы", "смета"]},
    {"title": "Архитектор", "industry": "Строительство", "salary_min": 350000, "salary_max": 750000,
     "skills": ["AutoCAD", "Revit", "ArchiCAD", "3ds Max", "дизайн"]},
]

COMPANIES = [
    "Kaspi Bank", "Halyk Bank", "Air Astana", "KazMunayGas", "Samruk-Kazyna",
    "Beeline Kazakhstan", "Kcell", "Forte Bank", "Bank CenterCredit", "Tengizchevroil",
    "BI Group", "MEGA Center", "Magnum Cash&Carry", "Alseco", "Kolesa Group",
    "Chocofamily", "Arbuz.kz", "OLX Kazakhstan", "Wildberries KZ", "Lamoda.kz",
    "Rakhat", "RG Brands", "Heineken Kazakhstan", "Philip Morris Kazakhstan",
    "McKinsey & Company", "PwC Kazakhstan", "Deloitte Kazakhstan", "KPMG",
    "Google Kazakhstan", "Microsoft Kazakhstan", "Epam Systems",
    "Erste Digital", "IT Solutions", "Dev Team", "Tech Hub Almaty",
    "Медицинский центр", "Университет", "Школа", "ТОО СтройГрупп",
]

EXPERIENCE_OPTIONS = [
    "Без опыта", "1-2 года", "2-3 года", "3-5 лет", "5+ лет",
]

DESCRIPTIONS = [
    "Требуется {title} в нашу команду. Отличные условия труда, дружный коллектив, официальное трудоустройство.",
    "Приглашаем на работу {title}. Стабильная зарплата, соцпакет, возможность карьерного роста.",
    "Вакансия {title}. Работа в крупной компании Казахстана. Конкурентная зарплата.",
    "Ищем опытного {title} для работы в динамично развивающейся компании.",
]


async def seed_vacancies(count: int = 1000):
    """Создать N реалистичных тестовых вакансий."""
    await init_db()

    async with aiosqlite.connect(DATABASE_URL) as db:
        # Проверяем есть ли уже данные
        cur = await db.execute("SELECT COUNT(*) FROM vacancies")
        existing = (await cur.fetchone())[0]
        if existing > 0:
            print(f"⚠️  В БД уже есть {existing} вакансий. Добавляем ещё {count}...")

        inserted = 0
        for i in range(count):
            template = random.choice(VACANCIES_DATA)
            region = random.choice(REGIONS)
            company = random.choice(COMPANIES)
            experience = random.choice(EXPERIENCE_OPTIONS)
            desc_template = random.choice(DESCRIPTIONS)
            description = desc_template.format(title=template["title"])

            # Небольшая вариация в зарплатах
            salary_variation = random.uniform(0.85, 1.2)
            salary_min = int(template["salary_min"] * salary_variation / 10000) * 10000
            salary_max = int(template["salary_max"] * salary_variation / 10000) * 10000

            # Уникальный URL
            source_url = f"https://www.enbek.kz/ru/vacancy/{random.randint(100000, 999999)}"

            # Случайные навыки (подмножество)
            skills = template["skills"].copy()
            if len(skills) > 3:
                skills = random.sample(skills, random.randint(3, len(skills)))

            try:
                await db.execute("""
                    INSERT OR IGNORE INTO vacancies
                    (title, company, region, salary_min, salary_max, industry,
                     experience, skills, description, source_url, normalized_title)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template["title"], company, region, salary_min, salary_max,
                    template["industry"], experience,
                    json.dumps(skills, ensure_ascii=False),
                    description, source_url,
                    template["title"],  # normalized_title = title для seed данных
                ))
                inserted += 1
            except Exception as e:
                pass  # Дубликат source_url

        await db.commit()
        print(f"✅ Добавлено {inserted} вакансий в БД")

        # Обновляем статистику
        cur = await db.execute("SELECT COUNT(*) FROM vacancies")
        total = (await cur.fetchone())[0]
        print(f"📊 Всего вакансий в БД: {total}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    print(f"🌱 Заполнение БД тестовыми данными ({count} вакансий)...")
    asyncio.run(seed_vacancies(count))
