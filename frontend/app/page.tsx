'use client';
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import {
  getDashboardOverview,
  getMapData,
  getTopProfessions,
  getSalaryByRegion,
  getTrends,
} from '@/lib/api';
import { formatSalaryShort, formatNumber, REGIONS } from '@/lib/utils';
import TopProfessions from '@/components/TopProfessions';
import SalaryChart from '@/components/SalaryChart';
import TrendsChart from '@/components/TrendsChart';

const KazakhstanMap = dynamic(() => import('@/components/KazakhstanMap'), { ssr: false });

function StatCard({
  label,
  value,
  sub,
  color,
  icon,
}: {
  label: string;
  value: string;
  sub?: string;
  color: 'blue' | 'green' | 'orange' | 'purple';
  icon: React.ReactNode;
}) {
  const colorMap = {
    blue:   { bg: 'bg-blue-50',   text: 'text-blue-600',   border: 'border-blue-100' },
    green:  { bg: 'bg-emerald-50', text: 'text-emerald-600', border: 'border-emerald-100' },
    orange: { bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-100' },
    purple: { bg: 'bg-violet-50', text: 'text-violet-600', border: 'border-violet-100' },
  };
  const c = colorMap[color];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className={`w-10 h-10 ${c.bg} ${c.border} border rounded-lg flex items-center justify-center mb-3`}>
        <span className={c.text}>{icon}</span>
      </div>
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<{
    total_vacancies: number;
    avg_salary: number | null;
    top_region: string | null;
    top_profession: string | null;
    regions_count: number;
  } | null>(null);

  const [mapData, setMapData] = useState<Array<{
    region: string; latitude: number; longitude: number;
    vacancy_count: number; avg_salary: number | null; top_profession: string | null;
  }>>([]);

  const [professions, setProfessions] = useState<Array<{
    profession: string; vacancy_count: number; avg_salary: number | null; growth_percent: number | null;
  }>>([]);

  const [salaryData, setSalaryData] = useState<Array<{
    region: string; avg_salary: number | null; vacancy_count: number;
  }>>([]);

  const [trends, setTrends] = useState<Array<{
    month: string; vacancy_count: number; avg_salary: number | null;
  }>>([]);

  const [selectedRegion, setSelectedRegion] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getDashboardOverview(),
      getMapData(),
      getTopProfessions(undefined, 10),
      getSalaryByRegion(),
      getTrends(6),
    ]).then(([ov, map, prof, salary, tr]) => {
      setOverview(ov);
      setMapData(map);
      setProfessions(prof);
      setSalaryData(salary);
      setTrends(tr);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedRegion) {
      getTopProfessions(selectedRegion, 10).then(setProfessions);
    } else {
      getTopProfessions(undefined, 10).then(setProfessions);
    }
  }, [selectedRegion]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500">Загрузка данных...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 rounded-2xl p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Рынок труда Казахстана
            </h1>
            <p className="text-blue-100 text-sm mt-2 max-w-lg">
              Актуальная аналитика вакансий, зарплат и карьерных трендов на основе данных enbek.kz
            </p>
          </div>
          <div className="hidden sm:flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl px-4 py-3">
            <svg className="w-5 h-5 text-blue-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <div>
              <p className="text-xs text-blue-200">Powered by</p>
              <p className="text-sm font-semibold text-white">Groq AI</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Всего вакансий"
          value={formatNumber(overview?.total_vacancies ?? 0)}
          sub="в базе данных"
          color="blue"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          }
        />
        <StatCard
          label="Средняя зарплата"
          value={formatSalaryShort(overview?.avg_salary)}
          sub="по Казахстану"
          color="green"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          label="Топ регион"
          value={overview?.top_region ?? '—'}
          sub="наибольшее число вакансий"
          color="orange"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
        />
        <StatCard
          label="Регионов"
          value={String(overview?.regions_count ?? 0)}
          sub="охвачено данными"
          color="purple"
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          }
        />
      </div>

      {/* Region filter */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-700">Фильтр по региону:</label>
        <select
          value={selectedRegion}
          onChange={(e) => setSelectedRegion(e.target.value)}
          className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Весь Казахстан</option>
          {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Map */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-1">Карта вакансий</h2>
          <p className="text-xs text-gray-400 mb-4">Размер круга — число вакансий, цвет — уровень зарплаты</p>
          <KazakhstanMap data={mapData} />
        </div>

        {/* Top professions */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-4">
            Топ профессий {selectedRegion ? `— ${selectedRegion}` : ''}
          </h2>
          <TopProfessions data={professions} />
        </div>

        {/* Salary by region */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Зарплаты по регионам</h2>
          <SalaryChart data={salaryData} />
        </div>

        {/* Trends */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Тренды рынка (6 мес.)</h2>
          <TrendsChart data={trends} />
        </div>
      </div>
    </div>
  );
}
