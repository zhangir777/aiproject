import logging
import re
from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse
from services.groq_service import get_groq_service, SYSTEM_PROMPT_CHAT
from services.analytics_service import get_analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)


def extract_intent(message: str) -> tuple[str | None, str | None]:
    """Простое извлечение региона и профессии из вопроса."""
    regions = [
        "Алматы", "Астана", "Шымкент", "Алматинская", "Акмолинская",
        "Актюбинская", "Атырауская", "Карагандинская", "Костанайская",
        "Павлодарская", "Туркестанская", "Мангистауская",
    ]
    professions = [
        "программист", "разработчик", "бухгалтер", "экономист", "врач",
        "учитель", "менеджер", "юрист", "инженер", "маркетолог",
        "data scientist", "аналитик", "дизайнер", "продавец", "водитель",
    ]
    msg_lower = message.lower()
    found_region = next((r for r in regions if r.lower() in msg_lower), None)
    found_prof = next((p for p in professions if p in msg_lower), None)
    return found_region, found_prof


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """AI-чат с аналитикой рынка труда."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    # Определяем контекст из вопроса
    region, profession = extract_intent(request.message)

    # Получаем данные из БД
    analytics = get_analytics_service()
    db_context = await analytics.get_context_for_ai(region=region, profession=profession)

    # Формируем контекст для AI
    context_text = ""
    if db_context.get("vacancy_count"):
        context_text += f"\n📊 Данные из базы EnbekAI:"
        if profession:
            context_text += f"\n- Профессия: {profession}"
        if region:
            context_text += f"\n- Регион: {region}"
        context_text += f"\n- Вакансий найдено: {db_context['vacancy_count']}"
        if db_context.get("avg_salary"):
            context_text += f"\n- Средняя зарплата: {db_context['avg_salary']:,} ₸"
        if db_context.get("top_skills"):
            context_text += f"\n- Популярные навыки: {', '.join(db_context['top_skills'][:5])}"
        context_text += "\n"

    # Формируем историю сообщений
    messages = []
    for msg in request.history[-10:]:  # последние 10 сообщений
        messages.append({"role": msg.role, "content": msg.content})

    # Добавляем контекст к вопросу
    user_message = request.message
    if context_text:
        user_message = f"{context_text}\nВопрос пользователя: {request.message}"

    messages.append({"role": "user", "content": user_message})

    try:
        groq = get_groq_service()
        response_text, model_used = await groq.chat(messages, system_prompt=SYSTEM_PROMPT_CHAT)
        return ChatResponse(
            response=response_text,
            data_used=db_context if db_context else None,
            model=model_used,
        )
    except Exception as e:
        logger.error(f"Ошибка AI чата: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка AI сервиса: {str(e)}")
