import { useEffect, useState } from 'react';

export function useDarkMode() {
  const [enabled, setEnabled] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches || localStorage.getItem('theme') === 'dark'
  );

  useEffect(() => {
    const classList = document.documentElement.classList;
    if (enabled) {
      classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [enabled]);

  return { enabled, toggle: () => setEnabled((e) => !e) };
}
