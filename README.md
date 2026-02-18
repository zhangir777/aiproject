# EnbekAI — AI-аналитик рынка труда Казахстана

> Проект для конкурса **alem.ai battle** (категория: AI Driving Power — студенты)

## Описание

EnbekAI — веб-платформа для анализа рынка труда Казахстана с использованием искусственного интеллекта.

### Возможности
- **Интерактивная карта** — тепловая карта вакансий по регионам Казахстана
- **Аналитика** — статистика зарплат, топ профессий, тренды рынка
- **AI-чат** — задавайте вопросы о рынке труда на русском или казахском
- **Карьерный план** — персональные рекомендации на основе реальных данных
- **Каталог вакансий** — актуальные вакансии с enbek.kz

### Источники данных
- [enbek.kz](https://www.enbek.kz) — государственная биржа труда Казахстана
- [data.egov.kz](https://data.egov.kz) — открытые государственные данные

### AI-движок
- **Groq API** + Llama 3.3 70B — аналитика и чат
- **Llama 3.1 8B** — быстрая классификация вакансий

## Технологии

| Компонент | Технологии |
|-----------|-----------|
| Backend | Python 3.11, FastAPI, SQLite, APScheduler |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Графики | Recharts |
| Карта | React-Leaflet + OpenStreetMap |
| AI | Groq API (Llama 3.3 70B + 3.1 8B) |
| Деплой | Railway (backend) + Vercel (frontend) |

## Запуск локально

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # добавить GROQ_API_KEY
uvicorn main:app --reload
```
API будет доступен на http://localhost:8000
Swagger UI: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Приложение откроется на http://localhost:3000

### Первоначальное наполнение данными
```bash
cd backend
python scripts/seed_data.py       # тестовые данные
python scripts/parse_enbek.py     # парсинг реальных вакансий
python scripts/discover_datasets.py  # поиск датасетов egov.kz
```

## Структура проекта

```
EnbekAI/
├── backend/
│   ├── main.py           # FastAPI точка входа
│   ├── config.py         # Конфигурация
│   ├── database.py       # SQLite + миграции
│   ├── models.py         # Pydantic схемы
│   ├── routers/          # API эндпоинты
│   ├── services/         # Бизнес-логика
│   └── scripts/          # Утилиты
└── frontend/
    ├── app/              # Next.js App Router страницы
    ├── components/       # React компоненты
    └── lib/              # Утилиты и API клиент
```

## Команда

Студенческий проект для alem.ai battle 2026.

## Лицензия

MIT
