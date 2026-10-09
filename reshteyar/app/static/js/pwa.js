/* ثبت service worker و دکمه‌ی نصب (بدون اسکریپت درون‌خطی، برای CSP) */
(function () {
  'use strict';
  if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () { /* بدون کش، سایت عادی کار می‌کند */ });
    });
  }

  var deferredPrompt = null;
  var btn = document.getElementById('install-app');
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (btn) btn.hidden = false;
  });
  if (btn) {
    btn.addEventListener('click', function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      deferredPrompt.userChoice.finally(function () { deferredPrompt = null; btn.hidden = true; });
    });
  }
  window.addEventListener('appinstalled', function () { if (btn) btn.hidden = true; });
})();
