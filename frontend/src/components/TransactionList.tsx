import { useEffect, useState } from 'react';
import { apiFetch } from '../api';

type Tx = {
  id: number;
  amount: number;
  currency: string;
  description: string;
  created_at: string;
};

export default function TransactionList() {
  const [items, setItems] = useState<Tx[]>([]);

  useEffect(() => {
    apiFetch('/операции?limit=5')
      .then((r) => r.json())
      .then(setItems)
      .catch(() => setItems([]));
  }, []);

  if (!items.length) return null;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded shadow">
      <h2 className="text-lg font-semibold mb-2">Последние операции</h2>
      <ul className="space-y-1 text-sm">
        {items.map((tx) => (
          <li key={tx.id} className="flex justify-between">
            <span>{new Date(tx.created_at).toLocaleDateString()}</span>
            <span>{tx.amount.toFixed(2)} {tx.currency}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
