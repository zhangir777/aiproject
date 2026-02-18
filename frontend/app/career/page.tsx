'use client';
import { useState } from 'react';
import CareerPlanForm from '@/components/CareerPlanForm';
import CareerPlanResult from '@/components/CareerPlanResult';

export default function CareerPage() {
  const [result, setResult] = useState<{
    plan: string;
    stats: Record<string, unknown>;
    alternatives: Array<{
      title: string;
      avg_salary: number | null;
      vacancy_count: number;
      match_score: number;
    }>;
  } | null>(null);

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-9 h-9 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-sm">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Карьерный план</h1>
        </div>
        <p className="text-gray-500 text-sm">
          Получите персональный AI-план карьеры на основе реальных данных рынка труда
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h2 className="text-base font-semibold text-gray-900 mb-5">Ваши данные</h2>
          <CareerPlanForm onResult={setResult} />
        </div>

        <div>
          {result ? (
            <CareerPlanResult result={result as Parameters<typeof CareerPlanResult>[0]['result']} />
          ) : (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 p-8 text-center h-full flex flex-col items-center justify-center min-h-[320px]">
              <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Ваш карьерный план</h3>
              <p className="text-gray-500 text-sm max-w-xs">
                Заполните форму слева, чтобы получить персональный карьерный план с анализом рынка труда
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
