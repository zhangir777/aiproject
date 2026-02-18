import logging
from fastapi import APIRouter, HTTPException
from models import CareerPlanRequest, CareerPlanResponse, AlternativeProfession
from services.career_service import get_career_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/career-plan", response_model=CareerPlanResponse)
async def create_career_plan(request: CareerPlanRequest):
    """Генерация персонального карьерного плана."""
    if not request.specialty.strip():
        raise HTTPException(status_code=400, detail="Укажите специальность")
    if not request.region.strip():
        raise HTTPException(status_code=400, detail="Укажите регион")

    try:
        svc = get_career_service()
        plan, stats, alternatives = await svc.generate_plan(
            specialty=request.specialty,
            region=request.region,
            skills=request.skills,
            experience_years=request.experience_years,
        )
        return CareerPlanResponse(
            plan=plan,
            stats=stats,
            alternatives=[
                AlternativeProfession(**alt) for alt in alternatives
            ],
        )
    except Exception as e:
        logger.error(f"Ошибка генерации карьерного плана: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
