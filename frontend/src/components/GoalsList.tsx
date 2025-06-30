import { useEffect, useState } from 'react';
import { apiFetch } from '../api';

type Item = { id: number; name: string; progress: number };

export default function GoalsList() {
  const [data, setData] = useState<Item[]>([]);

  useEffect(() => {
    apiFetch('/аналитика/цели')
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData([]));
  }, []);

  if (!data.length) return null;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded shadow">
      <h2 className="text-lg font-semibold mb-2">Цели</h2>
      <ul className="space-y-2">
        {data.map((g) => (
          <li key={g.id}>
            <div className="flex justify-between mb-1">
              <span>{g.name}</span>
              <span>{g.progress.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded">
              <div
                className="bg-green-500 h-2 rounded"
                style={{ width: `${g.progress}%` }}
              ></div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
