'use client';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { formatSalaryShort } from '@/lib/utils';

interface Profession {
  profession: string;
  vacancy_count: number;
  avg_salary: number | null;
}

interface Props {
  data: Profession[];
}

const COLORS = ['#2563EB', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE', '#EFF6FF', '#F0F9FF', '#E0F2FE', '#BAE6FD'];

export default function TopProfessions({ data }: Props) {
  const chartData = data.slice(0, 10).map((d) => ({
    ...d,
    name: d.profession.length > 20 ? d.profession.slice(0, 20) + '…' : d.profession,
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 30, top: 10, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value, name) => [
            name === 'vacancy_count' ? `${value} вакансий` : formatSalaryShort(value as number),
            name === 'vacancy_count' ? 'Вакансий' : 'Ср. зарплата',
          ]}
        />
        <Bar dataKey="vacancy_count" radius={[0, 4, 4, 0]}>
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
