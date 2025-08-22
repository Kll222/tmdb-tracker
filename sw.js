const CACHE_NAME = 'tmdb-cache-v1';

self.addEventListener('install', event => {
  self.skipWaiting(); // 强制激活新版本
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.map(key => caches.delete(key)) // 删除旧缓存
    ))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request) // 先从网络获取
      .then(response => {
        const resClone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, resClone));
        return response;
      })
      .catch(() => caches.match(event.request)) // 网络失败才用缓存
  );
});
