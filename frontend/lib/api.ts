const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Dashboard
export const getDashboardOverview = () =>
  fetchApi<{
    total_vacancies: number;
    avg_salary: number | null;
    top_region: string | null;
    top_profession: string | null;
    regions_count: number;
  }>('/api/dashboard/overview');

export const getMapData = () =>
  fetchApi<Array<{
    region: string;
    latitude: number;
    longitude: number;
    vacancy_count: number;
    avg_salary: number | null;
    top_profession: string | null;
  }>>('/api/dashboard/map');

export const getTopProfessions = (region?: string, limit = 10) =>
  fetchApi<Array<{
    profession: string;
    vacancy_count: number;
    avg_salary: number | null;
    growth_percent: number | null;
  }>>(`/api/dashboard/top-professions?limit=${limit}${region ? `&region=${encodeURIComponent(region)}` : ''}`);

export const getSalaryByRegion = () =>
  fetchApi<Array<{
    region: string;
    avg_salary: number | null;
    median_salary: number | null;
    vacancy_count: number;
  }>>('/api/dashboard/salary-by-region');

export const getTrends = (months = 6) =>
  fetchApi<Array<{
    month: string;
    vacancy_count: number;
    avg_salary: number | null;
  }>>(`/api/dashboard/trends?months=${months}`);

// Vacancies
export const getVacancies = (params: {
  region?: string;
  industry?: string;
  salary_min?: number;
  salary_max?: number;
  page?: number;
  per_page?: number;
}) => {
  const sp = new URLSearchParams();
  if (params.region) sp.set('region', params.region);
  if (params.industry) sp.set('industry', params.industry);
  if (params.salary_min) sp.set('salary_min', String(params.salary_min));
  if (params.salary_max) sp.set('salary_max', String(params.salary_max));
  if (params.page) sp.set('page', String(params.page));
  if (params.per_page) sp.set('per_page', String(params.per_page));
  return fetchApi<{
    items: Array<{
      id: number;
      title: string;
      company: string | null;
      region: string;
      salary_min: number | null;
      salary_max: number | null;
      industry: string | null;
      experience: string | null;
      skills: string[] | null;
    }>;
    total: number;
    page: number;
    per_page: number;
  }>(`/api/vacancies?${sp.toString()}`);
};

export const getIndustries = () =>
  fetchApi<Array<{ industry: string; count: number }>>('/api/vacancies/industries');

export const getRegions = () =>
  fetchApi<Array<{
    id: number;
    name_ru: string;
    name_kz: string | null;
    latitude: number;
    longitude: number;
  }>>('/api/vacancies/regions');

// AI Chat
export const sendChatMessage = (message: string, history: Array<{ role: string; content: string }>) =>
  fetchApi<{ response: string; data_used: Record<string, unknown> | null; model: string }>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history }),
  });

// Career Plan
export const generateCareerPlan = (data: {
  specialty: string;
  region: string;
  skills: string[];
  experience_years: number;
}) =>
  fetchApi<{
    plan: string;
    stats: Record<string, unknown>;
    alternatives: Array<{
      title: string;
      avg_salary: number | null;
      vacancy_count: number;
      match_score: number;
    }>;
  }>('/api/career-plan', {
    method: 'POST',
    body: JSON.stringify(data),
  });
