"""
Service Worker for ME_CAM Web Push Notifications
==============================================
Handles push notifications, notification clicks, and actions
"""

// Service Worker version
const VERSION = 'v1.0.0';
const CACHE_NAME = `mecam-sw-${VERSION}`;

// Install event
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker version', VERSION);
    self.skipWaiting(); // Activate immediately
});

// Activate event
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker version', VERSION);
    event.waitUntil(
        // Clean up old caches
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(name => name.startsWith('mecam-sw-') && name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        })
    );
    return self.clients.claim(); // Take control of all clients
});

// Push notification received
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');

    try {
        // Parse notification data
        const data = event.data ? event.data.json() : {};

        const title = data.title || 'ME_CAM Alert';
        const options = {
            body: data.body || 'Motion detected',
            icon: data.icon || '/static/img/camera-icon.png',
            badge: data.badge || '/static/img/badge-icon.png',
            image: data.image, // Large image (snapshot)
            timestamp: data.timestamp || Date.now(),
            requireInteraction: data.requireInteraction !== false,
            tag: data.tag || 'mecam-notification',
            data: data.data || {},
            actions: data.actions || [
                {
                    action: 'view',
                    title: 'View',
                    icon: '/static/img/eye-icon.png'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss',
                    icon: '/static/img/close-icon.png'
                }
            ]
        };

        // Show notification
        event.waitUntil(
            self.registration.showNotification(title, options)
        );

    } catch (error) {
        console.error('[SW] Push notification error:', error);

        // Fallback notification
        event.waitUntil(
            self.registration.showNotification('ME_CAM Alert', {
                body: 'Motion detected',
                icon: '/static/img/camera-icon.png'
            })
        );
    }
});

// Notification click
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event.action);

    event.notification.close();

    const action = event.action;
    const data = event.notification.data || {};

    // Handle actions
    if (action === 'view') {
        // Open camera feed or event page
        const url = data.url || data.event_url || '/';
        event.waitUntil(
            clients.openWindow(url)
        );

    } else if (action === 'dismiss') {
        // Just close (already done above)
        console.log('[SW] Notification dismissed');

    } else if (action === 'arm') {
        // Arm the camera system
        event.waitUntil(
            fetch('/api/arm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ armed: true })
            })
            .then(response => {
                if (response.ok) {
                    console.log('[SW] System armed');
                    return self.registration.showNotification('ME_CAM', {
                        body: 'System armed successfully',
                        icon: '/static/img/camera-icon.png',
                        tag: 'mecam-armed'
                    });
                }
            })
            .catch(error => {
                console.error('[SW] Arm failed:', error);
            })
        );

    } else if (action === 'disarm') {
        // Disarm the camera system
        event.waitUntil(
            fetch('/api/disarm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ armed: false })
            })
            .then(response => {
                if (response.ok) {
                    console.log('[SW] System disarmed');
                    return self.registration.showNotification('ME_CAM', {
                        body: 'System disarmed successfully',
                        icon: '/static/img/camera-icon.png',
                        tag: 'mecam-disarmed'
                    });
                }
            })
            .catch(error => {
                console.error('[SW] Disarm failed:', error);
            })
        );

    } else {
        // Default: open app to home page or event page
        const url = data.url || data.event_url || '/';
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then(clientList => {
                // Try to focus existing window
                for (let client of clientList) {
                    if (client.url.startsWith(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
        );
    }
});

// Background sync (for offline support)
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync:', event.tag);

    if (event.tag === 'sync-events') {
        event.waitUntil(
            // Sync motion events when back online
            syncMotionEvents()
        );
    }
});

// Sync motion events from IndexedDB
async function syncMotionEvents() {
    try {
        // This would integrate with IndexedDB for offline event storage
        console.log('[SW] Syncing motion events...');

        // Placeholder for actual sync logic
        // In production, this would:
        // 1. Open IndexedDB
        // 2. Get pending events
        // 3. Upload to server
        // 4. Mark as synced

        return Promise.resolve();
    } catch (error) {
        console.error('[SW] Sync failed:', error);
        return Promise.reject(error);
    }
}

// Message from client
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);

    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: VERSION });
    }
});

// Fetch event (for offline support)
self.addEventListener('fetch', (event) => {
    // Only cache GET requests to same origin
    if (event.request.method !== 'GET' || !event.request.url.startsWith(self.location.origin)) {
        return;
    }

    // Network-first strategy for dynamic content
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clone response before caching
                const responseToCache = response.clone();

                // Cache successful responses
                if (response.ok) {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, responseToCache);
                    });
                }

                return response;
            })
            .catch(() => {
                // Network failed, try cache
                return caches.match(event.request).then(response => {
                    if (response) {
                        return response;
                    }

                    // Return offline page for HTML requests
                    if (event.request.headers.get('accept').includes('text/html')) {
                        return caches.match('/offline.html');
                    }

                    return new Response('Offline', { status: 503 });
                });
            })
    );
});

console.log('[SW] Service worker loaded, version', VERSION);
