/* رشته‌یار — نسخه‌ی آفلاین داخل اندروید. همه‌چیز محلی است؛ به اینترنت نیاز ندارد. */
(function () {
  'use strict';

  var DATA = window.RZ_DATA;
  var E = window.RZEngine;
  var app = document.getElementById('app');
  var LIST_LIMIT = 150;

  // ------------------------------------------------------------ ابزارها
  function esc(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function faDigits(value) {
    return String(value).replace(/[0-9]/g, function (d) { return '۰۱۲۳۴۵۶۷۸۹'[d]; }).replace(/\./g, '٫');
  }

  function toLatinNumber(text) {
    var s = String(text || '').trim()
      .replace(/[۰-۹]/g, function (d) { return String(d.charCodeAt(0) - 1776); })
      .replace(/[٠-٩]/g, function (d) { return String(d.charCodeAt(0) - 1632); })
      .replace(/[٫,]/g, '.');
    return s;
  }

  // مقدار عددی یا null. خطا فقط وقتی برمی‌گردد که ورودی خالی نیست ولی نامعتبر است.
  function parseNumber(text, min, max) {
    var s = toLatinNumber(text);
    if (s === '') return { value: null };
    if (!/^-?\d+(\.\d+)?$/.test(s)) return { error: 'عدد نامعتبر است: ' + text };
    var n = Number(s);
    if (n < min || n > max) return { error: 'عدد باید بین ' + faDigits(min) + ' و ' + faDigits(max) + ' باشد: ' + text };
    return { value: n };
  }

  function uniqueSorted(list) {
    var seen = {};
    list.forEach(function (x) { if (x) seen[x] = true; });
    return Object.keys(seen).sort(function (a, b) { return a < b ? -1 : (a > b ? 1 : 0); });
  }

  function groupBySlugOrKey(key) {
    for (var i = 0; i < DATA.groups.length; i++) {
      if (DATA.groups[i].data_key === key) return DATA.groups[i];
    }
    return null;
  }

  function groupTitleByKey(key) {
    var g = groupBySlugOrKey(key);
    return g ? g.title : key;
  }

  function matchesQuery(text, q) {
    return !q || E.norm(text).indexOf(q) !== -1;
  }

  function setTitle(t) { document.title = t + ' · رشته‌یار'; }

  function nav() {
    var hash = (location.hash || '#/').replace(/^#/, '');
    var parts = hash.split('/').filter(Boolean);
    try {
      if (parts.length === 0) return home();
      if (parts[0] === 'group' && parts[1]) return group(decodeURIComponent(parts[1]));
      if (parts[0] === 'universities') return universities();
      if (parts[0] === 'fields') return fields();
      if (parts[0] === 'factors') return factors();
      if (parts[0] === 'about') return about();
      return notFound();
    } catch (err) {
      app.innerHTML = '<section class="card"><h1>خطا</h1><p>صفحه بارگذاری نشد. دوباره تلاش کنید.</p></section>';
      if (window.console) console.error(err);
    }
  }

  // ------------------------------------------------------------ صفحه‌ها
  function home() {
    setTitle('صفحه‌ی اصلی');
    var cards = DATA.groups.map(function (g) {
      return '<a class="group-card" href="#/group/' + esc(g.slug) + '">' +
        '<span class="group-title">' + esc(g.title) + '</span>' +
        '<span class="group-tag">' + esc(g.tagline) + '</span>' +
        '<span class="group-weights">سوابق ' + faDigits(g.school_weight) + '٪ · آزمون ' + faDigits(g.exam_weight) + '٪</span>' +
        '</a>';
    }).join('');
    app.innerHTML =
      '<section class="hero"><h1>راهنمای انتخاب رشته‌ی کنکور</h1>' +
      '<p>گروه آزمایشی خود را انتخاب کنید، دانشگاه‌ها و رشته‌های مرتبط را ببینید و نمره‌ی تخمینی خود را حساب کنید.</p></section>' +
      '<section class="grid">' + cards + '</section>' +
      '<section class="card stats">' +
      '<div><strong>' + faDigits(DATA.meta.universities_total) + '</strong><span>دانشگاه و موسسه</span></div>' +
      '<div><strong>' + faDigits(DATA.meta.fields_total) + '</strong><span>رشته‌ی تحصیلی</span></div>' +
      '<div><strong>' + faDigits(DATA.groups.length) + '</strong><span>گروه آزمایشی</span></div></section>';
  }

  function group(slug) {
    var g = null;
    DATA.groups.forEach(function (x) { if (x.slug === slug) g = x; });
    if (!g) return notFound();
    setTitle(g.title);
    var key = g.data_key;

    var related = DATA.universities.filter(function (u) {
      return !u.focus || !u.focus.length || u.focus.indexOf(key) !== -1;
    });
    related.sort(function (a, b) {
      var fa = a.focus && a.focus.indexOf(key) !== -1 ? 0 : 1;
      var fb = b.focus && b.focus.indexOf(key) !== -1 ? 0 : 1;
      if (fa !== fb) return fa - fb;
      return a.name < b.name ? -1 : (a.name > b.name ? 1 : 0);
    });
    var relFields = DATA.fields.filter(function (f) { return f.groups.indexOf(key) !== -1; });

    var subjects = g.exam_subjects.map(function (s) {
      return '<tr><td>' + esc(s.label) + '</td><td>' + faDigits(s.coef) + '</td></tr>';
    }).join('');
    var notes = (g.factor_notes || []).map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('');

    var subjectInputs = g.exam_subjects.map(function (s) {
      return '<div class="subject-row"><label>' + esc(s.label) + ' — درصد</label>' +
        '<input name="pct_' + esc(s.key) + '" inputmode="decimal" placeholder="مثلاً ۶۵">' +
        '<label>ضریب</label><input name="coef_' + esc(s.key) + '" inputmode="decimal" value="' + esc(s.coef) + '"></div>';
    }).join('');

    var types = uniqueSorted(DATA.universities.map(function (u) { return u.type; }));
    var typeChecks = types.map(function (t) {
      return '<label class="chip"><input type="checkbox" name="univ_type" value="' + esc(t) + '"> ' + esc(t) + '</label>';
    }).join('');
    var provinces = uniqueSorted(DATA.universities.map(function (u) { return u.province; }));
    var provinceOpts = '<option value="">همه‌ی استان‌ها</option>' + provinces.map(function (p) {
      return '<option value="' + esc(p) + '">' + esc(p) + '</option>';
    }).join('');

    app.innerHTML =
      '<a class="back" href="#/">← بازگشت به گروه‌ها</a>' +
      '<section class="card"><h1>' + esc(g.title) + '</h1>' +
      '<p class="muted">' + esc(g.konkur_name) + '</p>' +
      '<p>' + esc(g.description) + '</p>' +
      '<h3>سهم‌بندی نمره</h3>' +
      '<p>سوابق تحصیلی: <strong>' + faDigits(g.school_weight) + '٪</strong> · آزمون اختصاصی: <strong>' + faDigits(g.exam_weight) + '٪</strong></p>' +
      '<table class="table"><thead><tr><th>درس آزمون اختصاصی</th><th>ضریب</th></tr></thead><tbody>' + subjects + '</tbody></table>' +
      (g.coef_note ? '<p class="note">' + esc(g.coef_note) + '</p>' : '') +
      '<h3>عوامل مؤثر در این گروه</h3><ul class="bullets">' + notes + '</ul></section>' +

      '<section class="card" id="calc"><h2>محاسبه‌ی نمره‌ی تخمینی</h2>' +
      '<p class="muted">اعداد را وارد کنید؛ خانه‌های خالی نادیده گرفته می‌شوند.</p>' +
      '<form id="calc-form" novalidate>' +
      '<div class="field"><label for="gpa">معدل کل سوابق (از ۲۰)</label><input id="gpa" name="gpa" inputmode="decimal" placeholder="مثلاً ۱۷٫۵"></div>' +
      subjectInputs +
      '<div class="field"><label for="rank_no">رتبه‌ی کل (بدون سهمیه) — اختیاری</label><input id="rank_no" name="rank_no" inputmode="numeric" placeholder="مثلاً ۲۵۰۰۰"></div>' +
      '<div class="field"><label for="interests">علاقه‌مندی‌ها (با ، جدا کنید)</label><input id="interests" name="interests" placeholder="مثلاً پزشکی، برنامه‌نویسی"></div>' +
      '<div class="field"><span>نوع دانشگاه مورد نظر (اختیاری)</span><div class="chips">' + typeChecks + '</div></div>' +
      '<div class="field"><label for="province">استان شما (اختیاری)</label><select id="province" name="province">' + provinceOpts + '</select></div>' +
      '<div id="form-error" class="error" role="alert"></div>' +
      '<button type="submit" class="btn">محاسبه کن</button>' +
      '</form></section>' +
      '<section id="result"></section>' +

      '<section class="card"><h2>دانشگاه‌های مرتبط (' + faDigits(related.length) + ')</h2>' +
      '<p class="muted">دانشگاه‌های تخصصی این گروه بالاتر آمده‌اند. فهرست کامل را در بخش دانشگاه‌ها جستجو کنید.</p>' +
      '<ul class="list">' + related.slice(0, LIST_LIMIT).map(uniItem).join('') + '</ul>' +
      (related.length > LIST_LIMIT ? '<p class="muted">' + faDigits(LIST_LIMIT) + ' مورد اول نمایش داده شد.</p>' : '') +
      '</section>' +

      '<section class="card"><h2>رشته‌های این گروه (' + faDigits(relFields.length) + ')</h2>' +
      '<input id="field-filter" class="search" placeholder="جستجوی رشته…" aria-label="جستجوی رشته">' +
      '<ul class="list" id="group-fields">' + relFields.slice(0, 400).map(fieldItem).join('') + '</ul>' +
      (relFields.length > 400 ? '<p class="muted">برای دیدن همه، از بخش رشته‌ها استفاده کنید.</p>' : '') +
      '</section>';

    bindGroup(g, relFields);
  }

  function bindGroup(g, relFields) {
    var form = document.getElementById('calc-form');
    var filter = document.getElementById('field-filter');
    var list = document.getElementById('group-fields');

    filter.addEventListener('input', function () {
      var q = E.norm(filter.value);
      var items = relFields.filter(function (f) { return matchesQuery(f.name, q); }).slice(0, 400);
      list.innerHTML = items.map(fieldItem).join('') || '<li class="muted">موردی پیدا نشد.</li>';
    });

    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var errorBox = document.getElementById('form-error');
      errorBox.textContent = '';
      var profile = readProfile(form, g);
      if (profile.error) { errorBox.textContent = profile.error; return; }
      var res = E.runAnalysis(DATA, g.slug, profile.value);
      renderResult(res, profile.value);
      document.getElementById('result').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  function readProfile(form, g) {
    var errors = [];
    function num(name, min, max) {
      var r = parseNumber(form.elements[name] ? form.elements[name].value : '', min, max);
      if (r.error) errors.push(r.error);
      return r.value;
    }
    var gpa = num('gpa', 0, 20);
    var pct = {}, coef = {};
    g.exam_subjects.forEach(function (s) {
      var p = num('pct_' + s.key, 0, 100);
      if (p !== null) pct[s.key] = p;
      var c = num('coef_' + s.key, 0, 100);
      if (c !== null) coef[s.key] = c;
    });
    var rankNo = num('rank_no', 1, 10000000);
    if (errors.length) return { error: errors[0] };

    var interests = E.parseInterests(form.elements.interests.value);
    var types = Array.prototype.slice.call(form.querySelectorAll('input[name="univ_type"]:checked'))
      .map(function (el) { return el.value; });
    var province = form.elements.province.value || null;
    return {
      value: {
        gpa: gpa, pct: pct, coef: coef,
        interests: interests, univTypes: types, province: province,
        rankNo: rankNo
      }
    };
  }

  function renderResult(res, profile) {
    var box = document.getElementById('result');
    if (!res) { box.innerHTML = ''; return; }
    var s = res.score;
    var scoreText = s.score === null ? 'ثبت نشد' : faDigits(s.score.toFixed(2)) + ' از ۱۰۰';
    var warn = s.warnings.map(function (w) { return '<li>' + esc(w) + '</li>'; }).join('');
    var fields = res.fields.slice(0, 25).map(function (x) {
      return '<li><strong>' + esc(x.field.name) + '</strong>' +
        (x.field.category ? ' <span class="muted">· ' + esc(x.field.category) + '</span>' : '') +
        (x.reasons.length ? '<div class="reason">' + esc(x.reasons.join('، ')) + '</div>' : '') + '</li>';
    }).join('');
    var unis = res.universities.slice(0, 25).map(function (x) {
      return '<li><strong>' + esc(x.university.name) + '</strong> <span class="muted">· ' +
        esc(x.university.type) + ' · ' + esc(x.university.province) + '</span>' +
        (x.reasons.length ? '<div class="reason">' + esc(x.reasons.join('، ')) + '</div>' : '') + '</li>';
    }).join('');
    box.innerHTML =
      '<section class="card result"><h2>نتیجه‌ی تحلیل</h2>' +
      '<div class="score">' + scoreText + '</div>' +
      (s.school_percent !== null ? '<p>درصد سوابق: ' + faDigits(s.school_percent.toFixed(1)) + ' · درصد آزمون: ' +
        (s.exam_percent !== null ? faDigits(s.exam_percent.toFixed(1)) : '—') + '</p>' : '') +
      (warn ? '<ul class="warn">' + warn + '</ul>' : '') +
      '<h3>رشته‌های پیشنهادی</h3>' +
      (fields ? '<ol class="list">' + fields + '</ol>' : '<p class="muted">رشته‌ای پیدا نشد.</p>') +
      '<h3>دانشگاه‌های پیشنهادی</h3>' +
      (unis ? '<ol class="list">' + unis + '</ol>' : '<p class="muted">دانشگاهی پیدا نشد.</p>') +
      '<p class="note">' + esc('داده‌ی رتبه‌های قبولی در این نسخه نیست، بنابراین شانس قبولی نشان داده نمی‌شود. محاسبه تخمینی است؛ مرجع نهایی دفترچه‌ی رسمی سازمان سنجش است.') + '</p>' +
      '</section>';
  }

  function uniItem(u) {
    return '<li><strong>' + esc(u.name) + '</strong> <span class="muted">· ' + esc(u.type) +
      ' · ' + esc(u.province) + (u.city ? '، ' + esc(u.city) : '') + '</span></li>';
  }

  function fieldItem(f) {
    return '<li><strong>' + esc(f.name) + '</strong> <span class="muted">· ' + esc(f.category) +
      ' · ' + esc((f.degrees || []).join('، ')) + '</span></li>';
  }

  function universities() {
    setTitle('دانشگاه‌ها');
    var types = uniqueSorted(DATA.universities.map(function (u) { return u.type; }));
    var provinces = uniqueSorted(DATA.universities.map(function (u) { return u.province; }));
    app.innerHTML =
      '<h1>فهرست دانشگاه‌ها و موسسات</h1>' +
      '<section class="card filters">' +
      '<input id="uq" class="search" placeholder="جستجوی نام، شهر یا استان…" aria-label="جستجو">' +
      '<select id="ut" aria-label="نوع"><option value="">همه‌ی انواع</option>' +
      types.map(function (t) { return '<option>' + esc(t) + '</option>'; }).join('') + '</select>' +
      '<select id="up" aria-label="استان"><option value="">همه‌ی استان‌ها</option>' +
      provinces.map(function (p) { return '<option>' + esc(p) + '</option>'; }).join('') + '</select>' +
      '</section><p id="ucount" class="muted"></p><ul class="list" id="ulist"></ul>';
    var q = document.getElementById('uq'), t = document.getElementById('ut'), p = document.getElementById('up');
    function draw() {
      var qq = E.norm(q.value);
      var items = DATA.universities.filter(function (u) {
        return (!t.value || u.type === t.value) && (!p.value || u.province === p.value) &&
          (!qq || matchesQuery(u.name + ' ' + u.city + ' ' + u.province, qq));
      });
      document.getElementById('ucount').textContent = 'تعداد: ' + faDigits(items.length) +
        (items.length > LIST_LIMIT ? ' (' + faDigits(LIST_LIMIT) + ' مورد اول نمایش داده شد — جستجو را دقیق‌تر کنید)' : '');
      document.getElementById('ulist').innerHTML = items.slice(0, LIST_LIMIT).map(uniItem).join('') ||
        '<li class="muted">موردی پیدا نشد.</li>';
    }
    q.addEventListener('input', draw);
    t.addEventListener('change', draw);
    p.addEventListener('change', draw);
    draw();
  }

  function fields() {
    setTitle('رشته‌ها');
    var groups = DATA.groups.map(function (g) { return g.data_key; });
    app.innerHTML =
      '<h1>فهرست رشته‌های تحصیلی</h1>' +
      '<section class="card filters">' +
      '<input id="fq" class="search" placeholder="جستجوی رشته…" aria-label="جستجو">' +
      '<select id="fg" aria-label="گروه"><option value="">همه‌ی گروه‌ها</option>' +
      groups.map(function (k) { return '<option value="' + esc(k) + '">' + esc(groupTitleByKey(k)) + '</option>'; }).join('') +
      '</select></section><p id="fcount" class="muted"></p><ul class="list" id="flist"></ul>';
    var q = document.getElementById('fq'), g = document.getElementById('fg');
    function draw() {
      var qq = E.norm(q.value);
      var items = DATA.fields.filter(function (f) {
        return (!g.value || f.groups.indexOf(g.value) !== -1) && matchesQuery(f.name + ' ' + f.category, qq);
      });
      document.getElementById('fcount').textContent = 'تعداد: ' + faDigits(items.length) +
        (items.length > LIST_LIMIT ? ' (' + faDigits(LIST_LIMIT) + ' مورد اول نمایش داده شد)' : '');
      document.getElementById('flist').innerHTML = items.slice(0, LIST_LIMIT).map(fieldItem).join('') ||
        '<li class="muted">موردی پیدا نشد.</li>';
    }
    q.addEventListener('input', draw);
    g.addEventListener('change', draw);
    draw();
  }

  function factors() {
    setTitle('عوامل مؤثر');
    app.innerHTML = '<h1>عوامل مؤثر در انتخاب رشته و پذیرش</h1>' +
      DATA.factors.map(function (f) {
        return '<section class="card"><h2>' + esc(f.title) + '</h2><p>' + esc(f.summary) + '</p>' +
          '<p><strong>چرا مهم است؟</strong> ' + esc(f.why) + '</p>' +
          '<p><strong>کجا بررسی کنیم؟</strong> ' + esc(f.where) + '</p></section>';
      }).join('');
  }

  function about() {
    setTitle('درباره');
    app.innerHTML = '<section class="card"><h1>درباره‌ی رشته‌یار</h1>' +
      '<p>رشته‌یار راهنمای انتخاب رشته‌ی کنکور است. داده‌های دانشگاه‌ها و رشته‌ها از فهرست‌های عمومی وزارت علوم گردآوری شده‌اند.</p>' +
      '<ul class="bullets">' +
      '<li>نمره‌ی محاسبه‌شده تخمینی است و جای محاسبه‌ی رسمی سازمان سنجش (نمره‌ی تراز) را نمی‌گیرد.</li>' +
      '<li>ضرایب، سهم‌بندی و فهرست رشته‌ها باید با دفترچه‌ی انتخاب رشته‌ی همان سال تطبیق داده شود.</li>' +
      '<li>داده‌ی رتبه‌های قبولی در این نسخه نیست و شانس قبولی نشان داده نمی‌شود.</li>' +
      '<li>نسخه‌ی آفلاین بدون پرداخت و بدون حساب کاربری است.</li>' +
      '</ul><p>آخرین به‌روزرسانی داده: ' + faDigits(DATA.meta.generated_at.slice(0, 10)) + '</p></section>';
  }

  function notFound() {
    setTitle('یافت نشد');
    app.innerHTML = '<section class="card"><h1>صفحه پیدا نشد</h1><p><a href="#/">بازگشت به صفحه‌ی اصلی</a></p></section>';
  }

  window.addEventListener('hashchange', nav);
  if (!DATA) {
    app.innerHTML = '<section class="card"><h1>خطا</h1><p>داده‌ها بارگذاری نشدند.</p></section>';
  } else {
    nav();
  }
})();
