/* صفحه‌ی پرمیوم: برجسته‌سازی طرح انتخاب‌شده (بدون اسکریپت درون‌خطی، برای CSP) */
(function () {
  'use strict';
  var radios = document.querySelectorAll('.plan-radio input[type="radio"]');
  function sync() {
    radios.forEach(function (r) {
      var holder = r.closest('.plan-radio');
      var card = holder && holder.querySelector('.plan');
      if (!card) return;
      card.style.outline = r.checked ? '2px solid #0ea5e9' : '';
      card.style.outlineOffset = r.checked ? '3px' : '';
    });
  }
  radios.forEach(function (r) { r.addEventListener('change', sync); });
  sync();
})();
