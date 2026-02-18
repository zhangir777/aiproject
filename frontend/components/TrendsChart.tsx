'use client';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { formatMonth, formatSalaryShort } from '@/lib/utils';

interface TrendPoint {
  month: string;
  vacancy_count: number;
  avg_salary: number | null;
}

interface Props {
  data: TrendPoint[];
}

export default function TrendsChart({ data }: Props) {
  const chartData = data.map((d) => ({
    ...d,
    name: formatMonth(d.month),
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
        <YAxis
          yAxisId="right"
          orientation="right"
          tickFormatter={(v) => formatSalaryShort(v)}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value, name) => [
            name === 'vacancy_count'
              ? `${value} вакансий`
              : formatSalaryShort(value as number),
            name === 'vacancy_count' ? 'Вакансий' : 'Ср. зарплата',
          ]}
        />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="vacancy_count"
          stroke="#2563EB"
          strokeWidth={2}
          dot={{ r: 4 }}
          name="vacancy_count"
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="avg_salary"
          stroke="#10B981"
          strokeWidth={2}
          dot={{ r: 4 }}
          name="avg_salary"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
