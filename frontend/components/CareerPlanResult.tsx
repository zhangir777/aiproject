import ReactMarkdown from 'react-markdown';
import { formatSalaryShort, formatNumber } from '@/lib/utils';

interface CareerResult {
  plan: string;
  stats: {
    vacancy_count: number;
    avg_salary: number | null;
    min_salary: number | null;
    max_salary: number | null;
    top_skills: string[];
    region: string;
    specialty: string;
  };
  alternatives: Array<{
    title: string;
    avg_salary: number | null;
    vacancy_count: number;
    match_score: number;
  }>;
}

export default function CareerPlanResult({ result }: { result: CareerResult }) {
  const { plan, stats, alternatives } = result;

  return (
    <div className="space-y-6">
      {/* Stats sidebar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-blue-50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-blue-700">{formatNumber(stats.vacancy_count)}</p>
          <p className="text-xs text-gray-600 mt-1">Вакансий</p>
        </div>
        <div className="bg-emerald-50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-emerald-700">{formatSalaryShort(stats.avg_salary)}</p>
          <p className="text-xs text-gray-600 mt-1">Ср. зарплата</p>
        </div>
        <div className="bg-gray-50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-gray-700">{formatSalaryShort(stats.min_salary)}</p>
          <p className="text-xs text-gray-600 mt-1">Минимум</p>
        </div>
        <div className="bg-amber-50 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-amber-700">{formatSalaryShort(stats.max_salary)}</p>
          <p className="text-xs text-gray-600 mt-1">Максимум</p>
        </div>
      </div>

      {/* Plan */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Ваш карьерный план</h3>
        <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-li:text-gray-700">
          <ReactMarkdown>{plan}</ReactMarkdown>
        </div>
      </div>

      {/* Alternatives */}
      {alternatives.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Альтернативные профессии</h3>
          <div className="space-y-3">
            {alternatives.map((alt, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div>
                  <p className="font-medium text-gray-900">{alt.title}</p>
                  <p className="text-sm text-gray-500">{formatNumber(alt.vacancy_count)} вакансий</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-emerald-600">{formatSalaryShort(alt.avg_salary)}</p>
                  <p className="text-xs text-gray-400">ср. зарплата</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top skills */}
      {stats.top_skills && stats.top_skills.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Востребованные навыки</h3>
          <div className="flex flex-wrap gap-2">
            {stats.top_skills.map((skill: string) => (
              <span key={skill} className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium">
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
