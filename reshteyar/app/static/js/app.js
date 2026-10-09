/* رشته‌یار — ابزارهای مشترک فرانت‌اند (بدون وابستگی) */
(function () {
  'use strict';
  var RZ = (window.RZ = window.RZ || {});
  var FA = '۰۱۲۳۴۵۶۷۸۹';

  RZ.fa = function (value) {
    return String(value === null || value === undefined ? '' : value).replace(/[0-9]/g, function (d) { return FA[d]; });
  };

  RZ.num = function (value, decimals) {
    if (value === null || value === undefined || value === '' || isNaN(Number(value))) return '—';
    var n = Number(value);
    var s = decimals ? n.toFixed(decimals) : String(Math.round(n));
    var parts = s.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '٬');
    return RZ.fa(parts.join('٫'));
  };

  // ساخت امن DOM؛ داده‌های کاربر هرگز به‌صورت HTML درج نمی‌شوند
  RZ.el = function (tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v === null || v === undefined || v === false) return;
        if (k === 'class') node.className = v;
        else if (k === 'text') node.textContent = v;
        else if (k === 'style' && typeof v === 'object') Object.assign(node.style, v);
        else if (k.indexOf('on') === 0 && typeof v === 'function') node.addEventListener(k.slice(2), v);
        else node.setAttribute(k, v === true ? '' : v);
      });
    }
    (Array.isArray(children) ? children : [children]).forEach(function (c) {
      if (c === null || c === undefined || c === false) return;
      node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return node;
  };

  RZ.api = function (url, options) {
    var opts = Object.assign({ headers: { 'Content-Type': 'application/json', Accept: 'application/json' } }, options || {});
    return fetch(url, opts).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) {
          var err = new Error(typeof data.detail === 'string' ? data.detail : 'خطا در ارتباط با سرور');
          err.status = res.status;
          throw err;
        }
        return data;
      });
    });
  };

  RZ.debounce = function (fn, ms) {
    var t;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms || 280);
    };
  };

  RZ.query = function (params) {
    var parts = [];
    Object.keys(params).forEach(function (k) {
      var v = params[k];
      if (v === '' || v === null || v === undefined || v === false) return;
      parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v === true ? 'true' : v));
    });
    return parts.length ? '?' + parts.join('&') : '';
  };

  /**
   * فهرست صفحه‌بندی‌شده با فیلتر.
   * opts: {list, count, more, endpoint, params(), render(item), empty, pageSize}
   * reload() فهرست را از اول می‌خواند؛ درخواست‌های قدیمی نتیجه‌شان نادیده گرفته می‌شود.
   */
  RZ.paginated = function (opts) {
    var offset = 0, total = 0, busy = false, seq = 0, pageSize = opts.pageSize || 40;

    function setCount(text) { if (opts.count) opts.count.textContent = text; }
    function showMore() { if (opts.more) opts.more.hidden = !(offset < total); }

    function fetchPage(reset) {
      if (!reset && busy) return Promise.resolve();
      var mySeq = reset ? ++seq : seq;
      if (reset) {
        offset = 0;
        total = 0;
        opts.list.innerHTML = '';
        setCount('در حال بارگذاری…');
        showMore();
      }
      busy = true;
      var params = Object.assign({}, opts.params(), { offset: offset, limit: pageSize });
      return RZ.api(opts.endpoint + RZ.query(params)).then(function (data) {
        if (mySeq !== seq) return;
        total = data.total;
        if (offset === 0 && data.items.length === 0) {
          opts.list.appendChild(RZ.el('div', { class: 'empty-state', text: opts.empty || 'موردی پیدا نشد.' }));
        }
        data.items.forEach(function (item) { opts.list.appendChild(opts.render(item)); });
        offset += data.items.length;
        setCount(total ? 'نمایش ' + RZ.num(offset) + ' از ' + RZ.num(total) : '');
        showMore();
      }).catch(function (err) {
        if (mySeq !== seq) return;
        opts.list.appendChild(RZ.el('div', { class: 'empty-state', text: err.message }));
        setCount('');
      }).finally(function () {
        if (mySeq === seq) busy = false;
      });
    }

    if (opts.more) opts.more.addEventListener('click', function () { fetchPage(false); });
    return { reload: function () { return fetchPage(true); } };
  };

  // ---- کارت‌های مشترک رشته و دانشگاه
  RZ.renderFieldItem = function (item) {
    return RZ.el('article', { class: 'item' }, [
      RZ.el('h4', { text: item.name }),
      RZ.el('div', { class: 'chips' }, item.degrees.map(function (d) {
        return RZ.el('span', { class: 'chip chip-muted', text: d });
      })),
      RZ.el('div', { class: 'chips' }, item.groups.map(function (g) {
        return RZ.el('a', { class: 'chip', href: '/groups/' + g.slug, text: g.title });
      })),
      item.category ? RZ.el('div', { class: 'sub', text: 'دسته: ' + item.category }) : null
    ]);
  };

  RZ.renderUniItem = function (item) {
    var focus = item.focus.length
      ? item.focus.map(function (g) { return RZ.el('a', { class: 'chip chip-gold', href: '/groups/' + g.slug, text: 'تخصصی ' + g.title }); })
      : [RZ.el('span', { class: 'chip chip-muted', text: 'عمومی' })];
    return RZ.el('article', { class: 'item' }, [
      RZ.el('h4', { text: item.name }),
      RZ.el('div', { class: 'sub', text: [item.province, item.city].filter(Boolean).join(' · ') }),
      RZ.el('div', { class: 'chips' }, [RZ.el('span', { class: 'chip', text: item.type })].concat(focus))
    ]);
  };

  // ---- ناوبری موبایل
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // ---- کپی کردن کد فعال‌سازی
  document.querySelectorAll('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy');
      if (navigator.clipboard) navigator.clipboard.writeText(text);
      var old = btn.textContent;
      btn.textContent = 'کپی شد';
      setTimeout(function () { btn.textContent = old; }, 1400);
    });
  });
})();
