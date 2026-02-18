from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ──────────────────────────────────────────────
# Vacancies
# ──────────────────────────────────────────────

class VacancyBase(BaseModel):
    title: str
    company: Optional[str] = None
    region: str
    city: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    industry: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[List[str]] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    published_at: Optional[str] = None


class VacancyOut(VacancyBase):
    id: int
    normalized_title: Optional[str] = None
    skill_tags: Optional[List[str]] = None
    parsed_at: Optional[str] = None

    class Config:
        from_attributes = True


class VacancyFilter(BaseModel):
    region: Optional[str] = None
    industry: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class VacancyListResponse(BaseModel):
    items: List[VacancyOut]
    total: int
    page: int
    per_page: int


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

class DashboardOverview(BaseModel):
    total_vacancies: int
    avg_salary: Optional[int]
    top_region: Optional[str]
    top_profession: Optional[str]
    regions_count: int


class RegionMapPoint(BaseModel):
    region: str
    latitude: float
    longitude: float
    vacancy_count: int
    avg_salary: Optional[int]
    top_profession: Optional[str]


class ProfessionStat(BaseModel):
    profession: str
    vacancy_count: int
    avg_salary: Optional[int]
    growth_percent: Optional[float] = None


class RegionSalaryStat(BaseModel):
    region: str
    avg_salary: Optional[int]
    median_salary: Optional[int]
    vacancy_count: int


class TrendPoint(BaseModel):
    month: str
    vacancy_count: int
    avg_salary: Optional[int]


# ──────────────────────────────────────────────
# AI Chat
# ──────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    data_used: Optional[dict] = None
    model: str


# ──────────────────────────────────────────────
# Career Plan
# ──────────────────────────────────────────────

class CareerPlanRequest(BaseModel):
    specialty: str
    region: str
    skills: List[str] = []
    experience_years: int = Field(default=0, ge=0, le=50)


class AlternativeProfession(BaseModel):
    title: str
    avg_salary: Optional[int]
    vacancy_count: int
    match_score: float


class CareerPlanResponse(BaseModel):
    plan: str  # markdown
    stats: dict
    alternatives: List[AlternativeProfession]


# ──────────────────────────────────────────────
# Regions & Skills
# ──────────────────────────────────────────────

class RegionOut(BaseModel):
    id: int
    name_ru: str
    name_kz: Optional[str]
    latitude: float
    longitude: float
    population: Optional[int]


class IndustryStat(BaseModel):
    industry: str
    count: int


class SkillStat(BaseModel):
    skill: str
    count: int
    avg_salary_boost: Optional[int] = None
