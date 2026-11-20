const CACHE_NAME = "college-app-v3";

const STATIC_FILES = [
    "/static/style.css",
    "/static/manifest.json",
    "/static/icon-192.png",
    "/static/icon-512.png"
];


// ==========================================
// INSTALL
// ==========================================

self.addEventListener("install", function(event) {

    self.skipWaiting();

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {

                return cache.addAll(
                    STATIC_FILES
                );

            })
    );

});


// ==========================================
// ACTIVATE
// ==========================================

self.addEventListener("activate", function(event) {

    event.waitUntil(

        caches.keys()
            .then(function(cacheNames) {

                return Promise.all(

                    cacheNames.map(
                        function(cacheName) {

                            if (
                                cacheName !== CACHE_NAME
                            ) {

                                return caches.delete(
                                    cacheName
                                );

                            }

                        }
                    )

                );

            })

    );

    self.clients.claim();

});


// ==========================================
// FETCH
// ==========================================

self.addEventListener("fetch", function(event) {

    if (
        event.request.method !== "GET"
    ) {

        return;

    }


    // HTML / dashboard pages
    // Prefer newest online version

    if (
        event.request.mode === "navigate"
    ) {

        event.respondWith(

            fetch(event.request)

                .catch(function() {

                    return caches.match(
                        event.request
                    );

                })

        );

        return;

    }


    // CSS / icons / static files

    event.respondWith(

        caches.match(event.request)

            .then(function(cachedResponse) {

                if (cachedResponse) {

                    return cachedResponse;

                }

                return fetch(
                    event.request
                );

            })

    );

});