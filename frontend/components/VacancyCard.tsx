import { formatSalaryShort } from '@/lib/utils';

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

export default function VacancyCard({ vacancy }: { vacancy: Vacancy }) {
  const salaryText =
    vacancy.salary_min && vacancy.salary_max
      ? `${formatSalaryShort(vacancy.salary_min)} — ${formatSalaryShort(vacancy.salary_max)}`
      : vacancy.salary_min
      ? `от ${formatSalaryShort(vacancy.salary_min)}`
      : vacancy.salary_max
      ? `до ${formatSalaryShort(vacancy.salary_max)}`
      : 'Зарплата не указана';

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-base truncate">{vacancy.title}</h3>
          {vacancy.company && (
            <p className="text-sm text-gray-600 mt-0.5">{vacancy.company}</p>
          )}
        </div>
        {(vacancy.salary_min || vacancy.salary_max) && (
          <div className="ml-3 text-right flex-shrink-0">
            <span className="text-sm font-semibold text-emerald-600">{salaryText}</span>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
          {vacancy.region}
        </span>
        {vacancy.industry && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
            {vacancy.industry}
          </span>
        )}
        {vacancy.experience && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700">
            {vacancy.experience}
          </span>
        )}
      </div>

      {vacancy.skills && vacancy.skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {vacancy.skills.slice(0, 5).map((skill) => (
            <span
              key={skill}
              className="px-2 py-0.5 bg-gray-50 border border-gray-200 text-gray-600 text-xs rounded"
            >
              {skill}
            </span>
          ))}
          {vacancy.skills.length > 5 && (
            <span className="px-2 py-0.5 text-gray-400 text-xs">
              +{vacancy.skills.length - 5}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
