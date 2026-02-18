'use client';
import { useEffect, useState } from 'react';
import { getVacancies, getIndustries } from '@/lib/api';
import { REGIONS } from '@/lib/utils';
import VacancyCard from '@/components/VacancyCard';

interface Vacancy {
  id: number;
  title: string;
  company: string | null;
  region: string;
  salary_min: number | null;
  salary_max: number | null;
  industry: string | null;
  experience: string | null;
  skills: string[] | null;
}

export default function VacanciesPage() {
  const [vacancies, setVacancies] = useState<Vacancy[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [industries, setIndustries] = useState<Array<{ industry: string; count: number }>>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [region, setRegion] = useState('');
  const [industry, setIndustry] = useState('');
  const [salaryMin, setSalaryMin] = useState('');
  const [salaryMax, setSalaryMax] = useState('');

  const perPage = 20;

  useEffect(() => {
    getIndustries().then(setIndustries);
  }, []);

  useEffect(() => {
    setLoading(true);
    getVacancies({
      region: region || undefined,
      industry: industry || undefined,
      salary_min: salaryMin ? Number(salaryMin) : undefined,
      salary_max: salaryMax ? Number(salaryMax) : undefined,
      page,
      per_page: perPage,
    }).then((data) => {
      setVacancies(data.items);
      setTotal(data.total);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [region, industry, salaryMin, salaryMax, page]);

  const totalPages = Math.ceil(total / perPage);

  const resetFilters = () => {
    setRegion('');
    setIndustry('');
    setSalaryMin('');
    setSalaryMax('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Вакансии</h1>
        <p className="text-gray-500 text-sm mt-1">Актуальные вакансии с enbek.kz</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Регион</label>
            <select
              value={region}
              onChange={(e) => { setRegion(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все регионы</option>
              {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Отрасль</label>
            <select
              value={industry}
              onChange={(e) => { setIndustry(e.target.value); setPage(1); }}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Все отрасли</option>
              {industries.map((i) => (
                <option key={i.industry} value={i.industry}>{i.industry} ({i.count})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Зарплата от (₸)</label>
            <input
              type="number"
              value={salaryMin}
              onChange={(e) => { setSalaryMin(e.target.value); setPage(1); }}
              placeholder="например 200000"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Зарплата до (₸)</label>
            <input
              type="number"
              value={salaryMax}
              onChange={(e) => { setSalaryMax(e.target.value); setPage(1); }}
              placeholder="например 1000000"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <p className="text-sm text-gray-500">
            Найдено: <span className="font-semibold text-gray-900">{total}</span> вакансий
          </p>
          <button
            onClick={resetFilters}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Сбросить фильтры
          </button>
        </div>
      </div>

      {/* Vacancies grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        </div>
      ) : vacancies.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          Вакансии не найдены. Попробуйте изменить фильтры.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {vacancies.map((v) => <VacancyCard key={v.id} vacancy={v} />)}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Назад
          </button>
          <span className="text-sm text-gray-600">
            Страница {page} из {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 text-sm border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Вперёд
          </button>
        </div>
      )}
    </div>
  );
}
