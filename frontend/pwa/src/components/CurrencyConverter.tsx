import { useEffect, useState } from 'react';
import { apiFetch } from '../api';

type Rates = Record<string, number>;

export default function CurrencyConverter() {
  const [rates, setRates] = useState<Rates>({});
  const [amount, setAmount] = useState(1);
  const [source, setSource] = useState('USD');
  const [target, setTarget] = useState('RUB');
  const [result, setResult] = useState<number | null>(null);

  useEffect(() => {
    apiFetch('/валюты/')
      .then((r) => r.json())
      .then(setRates)
      .catch(() => setRates({}));
  }, []);

  async function convert(e: React.FormEvent) {
    e.preventDefault();
    const resp = await apiFetch(
      `/валюты/конвертировать?amount=${amount}&from=${source}&to=${target}`,
    );
    if (resp.ok) {
      const data = await resp.json();
      setResult(data.result);
    }
  }

  const codes = Object.keys(rates);

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded shadow">
      <h2 className="text-lg font-semibold mb-2">Конвертер валют</h2>
      <form onSubmit={convert} className="space-y-2">
        <input
          type="number"
          step="0.01"
          value={amount}
          onChange={(e) => setAmount(parseFloat(e.target.value))}
          className="w-full px-3 py-1 border rounded"
        />
        <div className="flex space-x-2">
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="flex-1 px-2 py-1 border rounded"
          >
            {codes.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <select
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="flex-1 px-2 py-1 border rounded"
          >
            {codes.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          className="w-full py-1 bg-blue-600 text-white rounded"
        >
          Конвертировать
        </button>
      </form>
      {result !== null && (
        <p className="mt-2 text-center text-lg">{result.toFixed(2)}</p>
      )}
    </div>
  );
}
