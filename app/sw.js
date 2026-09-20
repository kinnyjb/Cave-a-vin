const CACHE='cave-v8';
const CORE=['./','./index.html','./manifest.webmanifest','./icon-180.png','./icon-192.png','./icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)));self.skipWaiting()});
// on ne touche QU'AUX caches de l'appli Cave : celles des autres appli's ne nous regardent pas
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(
  ks.filter(k=>k.startsWith('cave-')&&k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim()});
// réseau d'abord (pour recevoir les nouvelles bouteilles), cache si hors ligne
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return r})
    .catch(()=>caches.match(e.request).then(r=>r||caches.match('./index.html'))));
});
