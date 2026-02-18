'use client';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { formatSalaryShort, formatNumber } from '@/lib/utils';

interface MapPoint {
  region: string;
  latitude: number;
  longitude: number;
  vacancy_count: number;
  avg_salary: number | null;
  top_profession: string | null;
}

interface Props {
  data: MapPoint[];
}

function getSalaryColor(salary: number | null, max: number, min: number): string {
  if (!salary) return '#94A3B8';
  const ratio = (salary - min) / (max - min + 1);
  // от красного к зелёному
  const r = Math.round(255 * (1 - ratio));
  const g = Math.round(200 * ratio);
  return `rgb(${r},${g},50)`;
}

function getRadius(count: number, max: number): number {
  const ratio = count / max;
  return 8 + ratio * 25;
}

export default function KazakhstanMapLeaflet({ data }: Props) {
  const maxCount = Math.max(...data.map((d) => d.vacancy_count), 1);
  const salaries = data.map((d) => d.avg_salary).filter(Boolean) as number[];
  const maxSalary = Math.max(...salaries, 1);
  const minSalary = Math.min(...salaries, 0);

  return (
    <MapContainer
      center={[48.0, 68.0]}
      zoom={5}
      className="w-full h-[400px] rounded-xl z-0"
      scrollWheelZoom={false}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />
      {data.map((point) => (
        <CircleMarker
          key={point.region}
          center={[point.latitude, point.longitude]}
          radius={getRadius(point.vacancy_count, maxCount)}
          fillColor={getSalaryColor(point.avg_salary, maxSalary, minSalary)}
          color="#fff"
          weight={2}
          fillOpacity={0.85}
        >
          <Tooltip>
            <div className="text-sm font-medium">{point.region}</div>
            <div className="text-xs text-gray-600">
              Вакансий: {formatNumber(point.vacancy_count)}
            </div>
            {point.avg_salary && (
              <div className="text-xs text-gray-600">
                Ср. зарплата: {formatSalaryShort(point.avg_salary)}
              </div>
            )}
            {point.top_profession && (
              <div className="text-xs text-blue-600">
                Топ: {point.top_profession}
              </div>
            )}
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
