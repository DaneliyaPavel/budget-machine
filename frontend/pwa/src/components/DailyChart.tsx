import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { apiFetch } from '../api';

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend);

type Item = { date: string; total: number };

export default function DailyChart() {
  const [data, setData] = useState<Item[]>([]);

  useEffect(() => {
    apiFetch('/аналитика/дни')
      .then((r) => r.json())
      .then(setData)
      .catch(() => setData([]));
  }, []);

  if (!data.length) return null;

  const chartData = {
    labels: data.map((d) => d.date.slice(8, 10)),
    datasets: [
      {
        label: 'Расходы',
        data: data.map((d) => d.total),
        borderColor: 'rgb(59 130 246)',
        backgroundColor: 'rgba(59,130,246,0.5)',
        tension: 0.3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true } },
  } as const;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded shadow h-60">
      <h2 className="text-lg font-semibold mb-2">Расходы по дням</h2>
      <Line data={chartData} options={options} />
    </div>
  );
}
