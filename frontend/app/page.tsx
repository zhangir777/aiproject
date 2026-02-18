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

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Рынок труда Казахстана</h1>
        <p className="text-gray-500 text-sm mt-1">Актуальная аналитика на основе данных enbek.kz</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Всего вакансий"
          value={formatNumber(overview?.total_vacancies ?? 0)}
          sub="в базе данных"
        />
        <StatCard
          label="Средняя зарплата"
          value={formatSalaryShort(overview?.avg_salary)}
          sub="по Казахстану"
        />
        <StatCard
          label="Топ регион"
          value={overview?.top_region ?? '—'}
          sub="наибольшее число вакансий"
        />
        <StatCard
          label="Регионов"
          value={String(overview?.regions_count ?? 0)}
          sub="охвачено данными"
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
          <h2 className="text-base font-semibold text-gray-900 mb-4">Карта вакансий</h2>
          <p className="text-xs text-gray-400 mb-3">Размер круга — число вакансий, цвет — уровень зарплаты</p>
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
