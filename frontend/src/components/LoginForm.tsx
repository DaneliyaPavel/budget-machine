import { useState } from 'react';

export default function LoginForm({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      const body = new URLSearchParams();
      body.append('username', email);
      body.append('password', password);
      const resp = await fetch('/пользователи/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      if (!resp.ok) throw new Error('auth');
      const data = await resp.json();
      localStorage.setItem('token', data.access_token);
      onLogin();
    } catch {
      setError('Неверные учетные данные');
    }
  }

  return (
    <form
      onSubmit={submit}
      className="max-w-sm mx-auto mt-20 p-4 bg-white dark:bg-gray-800 rounded shadow"
    >
      <h2 className="text-lg font-semibold mb-4 text-center">Вход</h2>
      <input
        type="email"
        required
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full mb-2 px-3 py-2 border rounded"
      />
      <input
        type="password"
        required
        placeholder="Пароль"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="w-full mb-4 px-3 py-2 border rounded"
      />
      {error && <p className="text-red-600 mb-2 text-sm">{error}</p>}
      <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded">
        Войти
      </button>
    </form>
  );
}
