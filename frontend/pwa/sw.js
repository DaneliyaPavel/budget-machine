self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('budget-cache').then((cache) => cache.add('/'))
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});
