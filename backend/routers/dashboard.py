from typing import Optional
from fastapi import APIRouter, Query
from services.analytics_service import get_analytics_service

router = APIRouter()


@router.get("/overview")
async def get_overview():
    """Общая статистика по рынку труда."""
    svc = get_analytics_service()
    return await svc.get_overview()


@router.get("/map")
async def get_map_data():
    """Данные для карты Казахстана."""
    svc = get_analytics_service()
    return await svc.get_map_data()


@router.get("/top-professions")
async def get_top_professions(
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    limit: int = Query(10, ge=1, le=50),
):
    """Топ профессий по количеству вакансий."""
    svc = get_analytics_service()
    return await svc.get_top_professions(region=region, limit=limit)


@router.get("/salary-by-region")
async def get_salary_by_region():
    """Средние зарплаты по регионам."""
    svc = get_analytics_service()
    return await svc.get_salary_by_region()


@router.get("/trends")
async def get_trends(months: int = Query(6, ge=1, le=24)):
    """Тренды рынка труда за N месяцев."""
    svc = get_analytics_service()
    return await svc.get_trends(months=months)
