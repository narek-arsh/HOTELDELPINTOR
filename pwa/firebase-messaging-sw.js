importScripts("https://www.gstatic.com/firebasejs/10.13.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.13.0/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyC8RXNwBkGK4BaJVRCDa8ezQLn00E1JUzU",
  authDomain: "hoteldelpintor.firebaseapp.com",
  projectId: "hoteldelpintor",
  storageBucket: "hoteldelpintor.firebasestorage.app",
  messagingSenderId: "587720154488",
  appId: "1:587720154488:web:f5f3a45eeffd41cab6fc8d"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const title = payload.notification?.title || "Hotel del Pintor";
  const options = {
    body: payload.notification?.body || "",
    icon: "/icon-192.png",
    badge: "/icon-192.png",
    data: payload.data || {},
  };
  self.registration.showNotification(title, options);
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const link = event.notification.data?.link || "/";
  event.waitUntil(clients.openWindow(link));
});
