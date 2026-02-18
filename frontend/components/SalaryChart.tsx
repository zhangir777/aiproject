'use client';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { formatSalaryShort } from '@/lib/utils';

interface RegionSalary {
  region: string;
  avg_salary: number | null;
  vacancy_count: number;
}

interface Props {
  data: RegionSalary[];
}

export default function SalaryChart({ data }: Props) {
  const chartData = data
    .filter((d) => d.avg_salary)
    .slice(0, 10)
    .map((d) => ({
      ...d,
      name: d.region.replace(' область', '').replace('Северо-Казахстанская', 'С.-Каз.').replace('Западно-Казахстанская', 'З.-Каз.').replace('Восточно-Казахстанская', 'В.-Каз.'),
    }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ left: 10, right: 20, top: 10, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11 }}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis tickFormatter={(v) => formatSalaryShort(v)} tick={{ fontSize: 11 }} />
        <Tooltip
          formatter={(value) => [formatSalaryShort(value as number), 'Ср. зарплата']}
          labelStyle={{ fontWeight: 600 }}
        />
        <Bar dataKey="avg_salary" fill="#10B981" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
