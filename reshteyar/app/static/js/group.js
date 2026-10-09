/* صفحه‌ی گروه: تب‌ها، ماشین‌حساب تخمینی، فهرست رشته‌ها و دانشگاه‌ها */
(function () {
  'use strict';
  var RZ = window.RZ;
  var root = document.querySelector('[data-group]');
  if (!root) return;

  var el = RZ.el;
  var slug = root.getAttribute('data-group');
  var premium = root.getAttribute('data-premium') === 'yes';
  var STORAGE_KEY = 'rz-profile-' + slug;
  var form = document.getElementById('calc-form');
  var results = document.getElementById('calc-results');
  var submitBtn = form.querySelector('button[type="submit"]');

  var LEVEL_CHIP = { high: 'chip chip-green', mid: 'chip', close: 'chip chip-amber', low: 'chip chip-red' };

  // ---------------------------------------------------------------- تب‌ها
  function showTab(name) {
    root.querySelectorAll('.tab').forEach(function (t) {
      t.setAttribute('aria-selected', t.getAttribute('data-tab') === name ? 'true' : 'false');
    });
    root.querySelectorAll('[data-panel]').forEach(function (p) {
      var on = p.getAttribute('data-panel') === name;
      p.classList.toggle('is-active', on);
      p.hidden = !on;
    });
    if (name === 'fields') loadFields();
    if (name === 'unis') loadUnis();
  }

  root.querySelectorAll('.tab').forEach(function (t) {
    t.addEventListener('click', function () {
      var name = t.getAttribute('data-tab');
      showTab(name);
      if (history.replaceState) history.replaceState(null, '', '#' + name);
    });
  });
  var initialTab = (location.hash || '').slice(1);
  if (['fields', 'unis', 'factors'].indexOf(initialTab) > -1) showTab(initialTab);

  // ---------------------------------------------------------------- فرم و ذخیره‌ی محلی
  function readRaw() {
    var raw = {};
    form.querySelectorAll('input[type="number"], input[type="text"], select').forEach(function (field) {
      if (field.name) raw[field.name] = field.value;
    });
    raw.univ_type = Array.prototype.map.call(
      form.querySelectorAll('input[name="univ_type"]:checked'), function (c) { return c.value; });
    return raw;
  }

  function applyRaw(raw) {
    Object.keys(raw).forEach(function (name) {
      if (name === 'univ_type') {
        form.querySelectorAll('input[name="univ_type"]').forEach(function (c) {
          c.checked = (raw.univ_type || []).indexOf(c.value) > -1;
        });
        return;
      }
      var field = form.querySelector('[name="' + name + '"]');
      if (field && typeof raw[name] === 'string') field.value = raw[name];
    });
  }

  function toNum(v) {
    if (v === '' || v === null || v === undefined) return null;
    var n = Number(v);
    return isNaN(n) ? null : n;
  }

  function buildPayload(raw) {
    var pct = {}, coef = {};
    Object.keys(raw).forEach(function (name) {
      if (name.indexOf('pct_') === 0) pct[name.slice(4)] = toNum(raw[name]);
      if (name.indexOf('coef_') === 0) coef[name.slice(5)] = toNum(raw[name]);
    });
    var rankNo = toNum(raw.rank_no_quota), rankQ = toNum(raw.rank_quota);
    return {
      gpa: toNum(raw.gpa),
      pct: pct,
      coef: coef,
      rank_no_quota: rankNo === null ? null : Math.round(rankNo),
      rank_quota: rankQ === null ? null : Math.round(rankQ),
      quota: raw.quota || 'none',
      province: raw.province || null,
      univ_types: raw.univ_type || [],
      interests: (raw.interests || '').trim(),
      degree: raw.degree || null
    };
  }

  try {
    var saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    if (saved) applyRaw(saved);
  } catch (e) { /* مرورگر اجازه نمی‌دهد: بی‌خیال */ }

  function hasAnyInput(p) {
    if (p.gpa !== null || p.rank_no_quota !== null || p.rank_quota !== null || p.interests) return true;
    return Object.keys(p.pct).some(function (k) { return p.pct[k] !== null; });
  }

  // ---------------------------------------------------------------- نمایش نتیجه
  function showMessage(text, cls) {
    results.innerHTML = '';
    results.appendChild(el('div', { class: cls || 'notice notice-warn', text: text }));
  }

  function barRow(label, value, weight) {
    var pct = value === null || value === undefined ? 0 : Math.max(0, Math.min(100, value));
    return el('div', null, [
      el('div', { class: 'bar-label' }, [
        el('span', { text: label + ' (سهم ' + RZ.fa(weight) + '٪)' }),
        el('b', { class: 'num', text: value === null || value === undefined ? 'وارد نشده' : RZ.num(value, 1) + '٪' })
      ]),
      el('div', { class: 'bar' }, [el('i', { style: { width: pct + '%' } })])
    ]);
  }

  function lockBox(text) {
    return el('div', { class: 'locked-box' }, [
      el('p', { text: text }),
      el('a', { class: 'btn btn-primary btn-sm', href: '/premium', text: 'مشاهده‌ی اشتراک پرمیوم' })
    ]);
  }

  function section(title, subtitle, count) {
    return el('div', { style: { marginTop: '18px' } }, [
      el('div', { class: 'result-head' }, [
        el('h3', { text: title, style: { margin: '0' } }),
        count !== undefined ? el('span', { class: 'chip', text: RZ.num(count) + ' مورد' }) : null
      ]),
      subtitle ? el('p', { class: 'small muted', text: subtitle, style: { margin: '4px 0 0' } }) : null
    ]);
  }

  function renderResult(d) {
    results.innerHTML = '';
    var s = d.score;
    var pct = s.score === null ? 0 : Math.max(0, Math.min(100, s.score));

    var ring = el('div', { class: 'score-ring', style: { '--p': String(pct) } }, [
      el('div', null, [
        el('b', { text: s.score === null ? '—' : RZ.num(s.score, 1) }),
        el('span', { text: 'نمره‌ی تخمینی از ۱۰۰' })
      ])
    ]);
    ring.style.setProperty('--p', String(pct));

    results.appendChild(el('div', { class: 'result-head' }, [
      el('h2', { text: 'نتیجه‌ی تخمینی ' + d.group.title, style: { margin: '0', fontSize: '1.2rem' } }),
      premium
        ? el('button', { class: 'btn btn-ghost btn-sm no-print', type: 'button', text: 'چاپ یا ذخیره‌ی گزارش', onclick: function () { window.print(); } })
        : el('a', { class: 'chip chip-gold', href: '/premium', text: 'نسخه‌ی رایگان' })
    ]));

    results.appendChild(el('div', { class: 'score-wrap', style: { marginTop: '14px' } }, [
      ring,
      el('div', { class: 'bars' }, [
        barRow('سوابق تحصیلی', s.school_percent, s.weights.school),
        barRow('آزمون اختصاصی', s.exam_percent, s.weights.exam)
      ])
    ]));

    var ranksText = [];
    if (d.ranks.no_quota) ranksText.push('رتبه‌ی کل: ' + RZ.num(d.ranks.no_quota));
    if (d.ranks.quota) ranksText.push('رتبه‌ی سهمیه‌ای: ' + RZ.num(d.ranks.quota) + ' (' + d.ranks.quota_label + ')');
    if (ranksText.length) results.appendChild(el('p', { class: 'small muted', text: ranksText.join('  ·  ') }));

    if (s.warnings && s.warnings.length) {
      results.appendChild(el('div', { class: 'notice notice-warn' }, s.warnings.map(function (w) {
        return el('div', { text: '• ' + w });
      })));
    }
    results.appendChild(el('div', { class: 'notice notice-info small', text: 'این نمره تخمینی است. سازمان سنجش نمره‌ی تراز را مبنا قرار می‌دهد؛ مرجع نهایی دفترچه‌ی همان سال است.' }));

    if (!premium) {
      results.appendChild(el('div', { class: 'notice notice-ok small' }, [
        el('span', { text: 'نسخه‌ی رایگان: حداکثر ' + RZ.num(d.free_limit) + ' مورد از هر فهرست نمایش داده می‌شود. ' }),
        el('a', { href: '/premium', text: 'اشتراک پرمیوم' })
      ]));
    }

    // رشته‌ها
    results.appendChild(section('رشته‌های پیشنهادی',
      d.fields.interest_matched ? 'مرتب‌شده بر اساس علاقه‌مندی‌های شما' : 'فهرست رشته‌های این گروه (با علاقه‌مندی، مرتب‌سازی می‌شود)',
      d.fields.total));
    var fieldBox = el('div', { class: 'result-list' });
    d.fields.items.forEach(function (f) {
      fieldBox.appendChild(el('div', { class: 'result-item' }, [
        el('h4', { text: f.name }),
        el('div', { class: 'chips' }, f.degrees.map(function (dg) { return el('span', { class: 'chip chip-muted', text: dg }); })),
        f.reasons && f.reasons.length ? el('div', { class: 'reasons', text: f.reasons.join(' · ') }) : null
      ]));
    });
    if (!d.fields.items.length) fieldBox.appendChild(el('div', { class: 'empty-state', text: 'رشته‌ای برای این گروه پیدا نشد.' }));
    results.appendChild(fieldBox);
    if (d.fields.locked) {
      results.appendChild(lockBox(RZ.num(d.fields.total - d.fields.shown) + ' رشته‌ی دیگر در اشتراک پرمیوم است.'));
    }

    // دانشگاه‌ها
    results.appendChild(section('دانشگاه‌های هم‌خوان', 'اولویت با دانشگاه‌های تخصصی گروه و استان شماست', d.universities.total));
    var uniBox = el('div', { class: 'result-list' });
    d.universities.items.forEach(function (u) {
      uniBox.appendChild(el('div', { class: 'result-item' }, [
        el('h4', { text: u.name }),
        el('div', { class: 'chips' }, [el('span', { class: 'chip', text: u.type }), el('span', { class: 'chip chip-muted', text: [u.province, u.city].filter(Boolean).join(' · ') })]),
        u.reasons && u.reasons.length ? el('div', { class: 'reasons', text: u.reasons.join(' · ') }) : null
      ]));
    });
    if (!d.universities.items.length) uniBox.appendChild(el('div', { class: 'empty-state', text: 'دانشگاهی با این ترجیحات پیدا نشد.' }));
    results.appendChild(uniBox);
    if (d.universities.locked) {
      results.appendChild(lockBox(RZ.num(d.universities.total - d.universities.shown) + ' دانشگاه‌ی دیگر در اشتراک پرمیوم است.'));
    }

    // شانس قبولی
    results.appendChild(section('شانس قبولی', null, d.chances.available ? d.chances.total : undefined));
    if (!d.chances.available || !d.chances.items.length) {
      results.appendChild(el('div', { class: 'notice notice-info small', text: d.chances.message || 'داده‌ای برای این بخش موجود نیست.' }));
    } else {
      var table = el('table', { class: 'chance-table' }, [
        el('thead', null, [el('tr', null, ['رشته', 'دانشگاه', 'سال', 'آخرین رتبه', 'رتبه‌ی شما', 'وضعیت'].map(function (h) { return el('th', { text: h }); }))]),
        el('tbody', null, d.chances.items.map(function (c) {
          return el('tr', null, [
            el('td', { text: c.field }),
            el('td', { text: c.university }),
            el('td', { class: 'num', text: c.year ? RZ.fa(c.year) : '—' }),
            el('td', { class: 'num', text: RZ.num(c.last_rank) }),
            el('td', { class: 'num', text: RZ.num(c.your_rank) }),
            el('td', null, [el('span', { class: LEVEL_CHIP[c.level] || 'chip', text: c.label })])
          ]);
        }))
      ]);
      results.appendChild(el('div', { class: 'table-wrap', style: { border: 'none', boxShadow: 'none', background: 'transparent' } }, [table]));
      if (d.chances.locked) results.appendChild(lockBox(RZ.num(d.chances.total - d.chances.shown) + ' مورد دیگر در اشتراک پرمیوم است.'));
    }

    results.appendChild(el('ul', { class: 'small muted', style: { marginTop: '18px', paddingInlineStart: '18px' } },
      d.notes.map(function (n) { return el('li', { text: n }); })));
  }

  // ---------------------------------------------------------------- ارسال فرم
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var raw = readRaw();
    var payload = buildPayload(raw);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(raw)); } catch (err) { /* اختیاری */ }
    if (!hasAnyInput(payload)) {
      showMessage('برای شروع، حداقل معدل، یک درصد آزمون، رتبه یا علاقه‌مندی را وارد کنید.');
      return;
    }
    submitBtn.disabled = true;
    showMessage('در حال محاسبه…', 'notice notice-info');
    RZ.api('/api/groups/' + slug + '/analyze', { method: 'POST', body: JSON.stringify(payload) })
      .then(renderResult)
      .catch(function (err) {
        showMessage(err.status === 422
          ? 'مقادیر واردشده معتبر نیستند: معدل بین ۰ تا ۲۰، درصدها بین ۰ تا ۱۰۰ و رتبه‌ها عدد مثبت باشند.'
          : err.message, 'notice notice-bad');
      })
      .finally(function () { submitBtn.disabled = false; });
  });

  // ---------------------------------------------------------------- فهرست رشته‌ها
  var fieldsLoaded = false;
  var gfQ = document.getElementById('gf-q');
  var gfDegree = document.getElementById('gf-degree');
  var fieldsPager = RZ.paginated({
    list: document.getElementById('gf-list'),
    count: document.getElementById('gf-count'),
    more: document.getElementById('gf-more'),
    endpoint: '/api/fields',
    params: function () { return { group: slug, q: gfQ.value.trim(), degree: gfDegree.value }; },
    render: RZ.renderFieldItem,
    empty: 'رشته‌ای با این فیلتر پیدا نشد.'
  });
  function loadFields() {
    if (fieldsLoaded) return;
    fieldsLoaded = true;
    fieldsPager.reload();
  }
  gfQ.addEventListener('input', RZ.debounce(function () { fieldsPager.reload(); }, 300));
  gfDegree.addEventListener('change', function () { fieldsPager.reload(); });
  document.getElementById('gf-reset').addEventListener('click', function () {
    gfQ.value = '';
    gfDegree.value = '';
    fieldsPager.reload();
  });

  // ---------------------------------------------------------------- فهرست دانشگاه‌ها
  var unisLoaded = false;
  var guQ = document.getElementById('gu-q');
  var guType = document.getElementById('gu-type');
  var guProvince = document.getElementById('gu-province');
  var guMode = document.getElementById('gu-mode');
  var unisPager = RZ.paginated({
    list: document.getElementById('gu-list'),
    count: document.getElementById('gu-count'),
    more: document.getElementById('gu-more'),
    endpoint: '/api/universities',
    params: function () {
      return { group: slug, q: guQ.value.trim(), type: guType.value, province: guProvince.value, mode: guMode.value };
    },
    render: RZ.renderUniItem,
    empty: 'دانشگاهی با این فیلتر پیدا نشد.'
  });
  function loadUnis() {
    if (unisLoaded) return;
    unisLoaded = true;
    unisPager.reload();
  }
  guQ.addEventListener('input', RZ.debounce(function () { unisPager.reload(); }, 300));
  [guType, guProvince, guMode].forEach(function (f) {
    f.addEventListener('change', function () { unisPager.reload(); });
  });
  document.getElementById('gu-reset').addEventListener('click', function () {
    guQ.value = '';
    guType.value = '';
    guProvince.value = '';
    guMode.value = 'related';
    unisPager.reload();
  });
})();
