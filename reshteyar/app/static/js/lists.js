/* صفحه‌های فهرست کامل: /fields و /universities */
(function () {
  'use strict';
  var RZ = window.RZ;

  var fieldList = document.getElementById('f-list');
  if (fieldList) {
    var fq = document.getElementById('f-q');
    var fg = document.getElementById('f-group');
    var fd = document.getElementById('f-degree');
    var fieldsPager = RZ.paginated({
      list: fieldList,
      count: document.getElementById('f-count'),
      more: document.getElementById('f-more'),
      endpoint: '/api/fields',
      params: function () { return { q: fq.value.trim(), group: fg.value, degree: fd.value }; },
      render: RZ.renderFieldItem,
      empty: 'رشته‌ای با این فیلتر پیدا نشد.'
    });
    var fieldSearch = RZ.debounce(function () { fieldsPager.reload(); }, 300);
    fq.addEventListener('input', fieldSearch);
    fg.addEventListener('change', function () { fieldsPager.reload(); });
    fd.addEventListener('change', function () { fieldsPager.reload(); });
    document.getElementById('f-reset').addEventListener('click', function () {
      fq.value = '';
      fg.value = '';
      fd.value = '';
      fieldsPager.reload();
    });
    fieldsPager.reload();
  }

  var uniList = document.getElementById('u-list');
  if (uniList) {
    var uq = document.getElementById('u-q');
    var ut = document.getElementById('u-type');
    var up = document.getElementById('u-province');
    var ug = document.getElementById('u-group');
    var uniPager = RZ.paginated({
      list: uniList,
      count: document.getElementById('u-count'),
      more: document.getElementById('u-more'),
      endpoint: '/api/universities',
      params: function () {
        return {
          q: uq.value.trim(),
          type: ut.value,
          province: up.value,
          group: ug.value,
          mode: ug.value ? 'related' : 'all'
        };
      },
      render: RZ.renderUniItem,
      empty: 'دانشگاهی با این فیلتر پیدا نشد.'
    });
    var uniSearch = RZ.debounce(function () { uniPager.reload(); }, 300);
    uq.addEventListener('input', uniSearch);
    [ut, up, ug].forEach(function (el) {
      el.addEventListener('change', function () { uniPager.reload(); });
    });
    document.getElementById('u-reset').addEventListener('click', function () {
      uq.value = '';
      ut.value = '';
      up.value = '';
      ug.value = '';
      uniPager.reload();
    });
    uniPager.reload();
  }
})();
