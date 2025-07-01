import { useEffect, useState } from 'react';
import { apiFetch } from '../api';

export default function BalanceCard() {
  const [data, setData] = useState<{ spent: number; forecast: number } | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiFetch('/аналитика/баланс')
      .then((r) => r.json())
      .then(setData)
      .catch(() => setError(true));
  }, []);

  if (error) return <div className="text-red-600">Ошибка загрузки</div>;
  if (!data) return <div>Загрузка...</div>;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded shadow">
      <h2 className="text-lg font-semibold mb-2">Баланс месяца</h2>
      <p className="text-3xl font-bold mb-1">{data.spent.toFixed(2)} ₽</p>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Прогноз: {data.forecast.toFixed(2)} ₽
      </p>
    </div>
  );
}
