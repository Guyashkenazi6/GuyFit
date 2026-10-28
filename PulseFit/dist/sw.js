const CACHE='pulsefit-v3';
const ASSETS=['./','./index.html','./styles.css','./exercise-atlas.css','./app.js','./manifest.webmanifest','./icon.svg','./assets/chest-atlas.png','./assets/triceps-atlas.png','./assets/back-atlas.png','./assets/biceps-atlas.png','./assets/shoulders-atlas.png','./assets/core-atlas.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r;}).catch(()=>caches.match('./index.html'))));});
