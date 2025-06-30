import BalanceCard from './components/BalanceCard';
import CategoryList from './components/CategoryList';
import GoalsList from './components/GoalsList';
import DailyChart from './components/DailyChart';
import TransactionList from './components/TransactionList';
import CurrencyConverter from './components/CurrencyConverter';
import LoginForm from './components/LoginForm';
import { useDarkMode } from './hooks/useDarkMode';
import { useState } from 'react';

export default function App() {
  const { enabled, toggle } = useDarkMode();
  const [logged, setLogged] = useState(() => Boolean(localStorage.getItem('token')));

  if (!logged) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        <LoginForm onLogin={() => setLogged(true)} />
      </div>
    );
  }

  function logout() {
    localStorage.removeItem('token');
    setLogged(false);
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <header className="p-4 flex justify-between items-center container mx-auto">
        <h1 className="text-2xl font-bold">Учет бюджета</h1>
        <div className="space-x-2">
          <button onClick={toggle} className="px-3 py-1 border rounded text-sm">
            {enabled ? 'Светлая тема' : 'Темная тема'}
          </button>
          <button onClick={logout} className="px-3 py-1 border rounded text-sm">
            Выйти
          </button>
        </div>
      </header>
      <main className="container mx-auto grid gap-4 p-4 md:grid-cols-2">
        <BalanceCard />
        <CategoryList />
        <GoalsList />
        <DailyChart />
        <CurrencyConverter />
        <TransactionList />
      </main>
    </div>
  );
}
