'use client';
import { useEffect, useState } from 'react';
import { formatSalaryShort } from '@/lib/utils';

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

export default function KazakhstanMap({ data }: Props) {
  const [Map, setMap] = useState<React.ComponentType<{ data: MapPoint[] }> | null>(null);

  useEffect(() => {
    // Динамический импорт Leaflet только на клиенте
    import('./KazakhstanMapLeaflet').then((mod) => {
      setMap(() => mod.default);
    });
  }, []);

  if (!Map) {
    return (
      <div className="w-full h-[400px] bg-gray-100 rounded-xl flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm">Загрузка карты...</p>
        </div>
      </div>
    );
  }

  return <Map data={data} />;
}
