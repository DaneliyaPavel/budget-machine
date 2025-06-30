import { useEffect, useState } from 'react';
import { apiFetch } from '../api';

type Item = { category: string; total: number };

export default function CategoryList() {
  const [data, setData] = useState<Item[]>([]);

  useEffect(() => {
    apiFetch('/аналитика/категории')
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData([]));
  }, []);

  if (!data.length) return null;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded shadow">
      <h2 className="text-lg font-semibold mb-2">Категории</h2>
      <ul className="space-y-1">
        {data.map((item) => (
          <li key={item.category} className="flex justify-between">
            <span>{item.category}</span>
            <span>{item.total.toFixed(2)} ₽</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
