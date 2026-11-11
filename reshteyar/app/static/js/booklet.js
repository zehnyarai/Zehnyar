// فیلتر جست‌وجوی فهرست‌های پذیرش ۱۴۰۵ در صفحه‌ی گروه
(function () {
  document.querySelectorAll('[data-filter]').forEach(function (input) {
    var list = document.getElementById(input.getAttribute('data-filter'));
    if (!list) return;
    input.addEventListener('input', function () {
      var q = input.value.trim().replace(/\s+/g, ' ');
      list.querySelectorAll('li').forEach(function (li) {
        li.hidden = q !== '' && li.textContent.indexOf(q) === -1;
      });
    });
  });
})();
