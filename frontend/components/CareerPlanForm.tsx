'use client';
import { useState } from 'react';
import { REGIONS } from '@/lib/utils';
import { generateCareerPlan } from '@/lib/api';

interface CareerResult {
  plan: string;
  stats: Record<string, unknown>;
  alternatives: Array<{
    title: string;
    avg_salary: number | null;
    vacancy_count: number;
    match_score: number;
  }>;
}

interface Props {
  onResult: (result: CareerResult) => void;
}

const COMMON_SKILLS = [
  'Python', 'JavaScript', 'SQL', 'Excel', '1C', 'AutoCAD',
  'React', 'Java', 'C++', 'Figma', 'Power BI', 'SAP',
  'Английский язык', 'Казахский язык', 'Agile', 'Docker',
];

export default function CareerPlanForm({ onResult }: Props) {
  const [specialty, setSpecialty] = useState('');
  const [region, setRegion] = useState('Алматы');
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [experience, setExperience] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) =>
      prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!specialty.trim()) {
      setError('Введите специальность');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const result = await generateCareerPlan({
        specialty,
        region,
        skills: selectedSkills,
        experience_years: experience,
      });
      onResult(result);
    } catch (err) {
      setError('Ошибка генерации плана. Проверьте соединение с сервером.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Специальность / профессия
        </label>
        <input
          type="text"
          value={specialty}
          onChange={(e) => setSpecialty(e.target.value)}
          placeholder="Например: Python разработчик, бухгалтер, маркетолог..."
          className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Регион
        </label>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm bg-white"
        >
          {REGIONS.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Текущие навыки (выберите или добавьте)
        </label>
        <div className="flex flex-wrap gap-2">
          {COMMON_SKILLS.map((skill) => (
            <button
              type="button"
              key={skill}
              onClick={() => toggleSkill(skill)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                selectedSkills.includes(skill)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {skill}
            </button>
          ))}
        </div>
        {selectedSkills.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            Выбрано: {selectedSkills.join(', ')}
          </p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Опыт работы: <span className="text-blue-600 font-semibold">{experience} лет</span>
        </label>
        <input
          type="range"
          min={0}
          max={15}
          value={experience}
          onChange={(e) => setExperience(Number(e.target.value))}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Без опыта</span>
          <span>5 лет</span>
          <span>10+</span>
          <span>15+ лет</span>
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Генерация плана...
          </span>
        ) : (
          'Построить карьерный план'
        )}
      </button>
    </form>
  );
}
