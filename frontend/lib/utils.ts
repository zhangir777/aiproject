import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatSalary(amount: number | null | undefined): string {
  if (!amount) return 'не указана';
  return new Intl.NumberFormat('ru-KZ', {
    style: 'currency',
    currency: 'KZT',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatSalaryShort(amount: number | null | undefined): string {
  if (!amount) return '—';
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1)}M ₸`;
  if (amount >= 1_000) return `${Math.round(amount / 1_000)}K ₸`;
  return `${amount} ₸`;
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('ru-RU').format(n);
}

export function formatMonth(period: string): string {
  const [year, month] = period.split('-');
  const months = [
    'Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
    'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек',
  ];
  return `${months[parseInt(month) - 1]} ${year}`;
}

export const REGIONS = [
  'Алматы',
  'Астана',
  'Шымкент',
  'Алматинская область',
  'Акмолинская область',
  'Актюбинская область',
  'Атырауская область',
  'Восточно-Казахстанская область',
  'Жамбылская область',
  'Западно-Казахстанская область',
  'Карагандинская область',
  'Костанайская область',
  'Кызылординская область',
  'Мангистауская область',
  'Павлодарская область',
  'Северо-Казахстанская область',
  'Туркестанская область',
  'Улытауская область',
  'Жетысуская область',
  'Абайская область',
];

export const PRIMARY_COLOR = '#2563EB';
export const SECONDARY_COLOR = '#10B981';
export const ACCENT_COLOR = '#F59E0B';
