/* موتور تحلیل رشته‌یار (نسخه‌ی آفلاین).
 * منطق این فایل مستقیماً از app/scoring.py و app/analysis.py (بخش نمره و پیشنهاد) ترجمه شده است.
 * محاسبه تخمینی است؛ نمره‌ی رسمی سازمان سنجش بر اساس نمره‌ی تراز است.
 */
(function (global) {
  'use strict';

  var INTEREST_SYNONYMS = {
    'برنامه‌نویسی': ['کامپیوتر', 'نرم افزار', 'هوش مصنوعی', 'علوم کامپیوتر', 'فناوری اطلاعات', 'شبکه'],
    'پزشکی': ['پزشکی', 'دندان', 'داروساز', 'پرستاری', 'مامایی', 'علوم آزمایشگاهی', 'هوشبری', 'فیزیوتراپی'],
    'طراحی': ['طراحی', 'گرافیک', 'صنعتی', 'پوشاک', 'تصویرسازی'],
    'حقوق': ['حقوق', 'قضایی', 'قضا'],
    'مدیریت': ['مدیریت', 'حسابداری', 'بازرگانی', 'کسب و کار'],
    'روان‌شناسی': ['روان شناسی', 'روانشناسی', 'مشاوره'],
    'زبان': ['زبان', 'مترجمی', 'ترجمه', 'آموزش زبان'],
    'معماری': ['معماری', 'شهرسازی'],
    'عمران': ['عمران', 'سازه', 'راهسازی', 'ساختمان'],
    'برق': ['برق', 'الکترونیک', 'مخابرات', 'کنترل'],
    'مکانیک': ['مکانیک', 'خودرو', 'ساخت', 'هوافضا'],
    'شیمی': ['شیمی', 'پلیمر', 'پتروشیمی'],
    'فیزیک': ['فیزیک', 'هسته‌ای', 'ستاره'],
    'ریاضی': ['ریاضی', 'آمار'],
    'کشاورزی': ['کشاورزی', 'زراعی', 'باغی', 'دامپروری', 'گیاه'],
    'محیط زیست': ['محیط زیست', 'منابع طبیعی', 'آبزی', 'شیلات'],
    'تاریخ': ['تاریخ', 'باستان'],
    'اقتصاد': ['اقتصاد', 'بازرگانی'],
    'هنر': ['هنر', 'نقاشی', 'گرافیک', 'سینما', 'موسیقی'],
    'سینما': ['سینما', 'فیلم', 'تصویربرداری', 'تئاتر', 'بازیگری'],
    'موسیقی': ['موسیقی', 'آهنگسازی', 'نوازندگی'],
    'ورزش': ['ورزش', 'تربیت بدنی'],
    'دین': ['الهیات', 'فقه', 'قرآن', 'معارف', 'حدیث', 'کلام']
  };

  var QUOTAS = [
    ['none', 'بدون سهمیه (رقابت آزاد)'], ['martyr', 'شاهد و ایثارگران'], ['basij', 'بسیجیان'],
    ['local', 'بومی (استانی)'], ['disabled', 'معلولان'], ['needy', 'مددجویان و کم‌برخوردار'],
    ['other', 'سایر سهمیه‌ها']
  ];

  function norm(value) {
    var text = value === null || value === undefined ? '' : String(value);
    return text.replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/\u200c/g, ' ')
      .replace(/[\u200f\u200e\u00ad]/g, '').toLowerCase().split(/\s+/).filter(Boolean).join(' ');
  }

  function interestVariants(term) {
    var n = norm(term);
    var variants = {};
    variants[n] = true;
    Object.keys(INTEREST_SYNONYMS).forEach(function (key) {
      var group = [norm(key)].concat(INTEREST_SYNONYMS[key].map(norm));
      var hit = group.some(function (g) { return n === g || (n.length >= 3 && g.indexOf(n) !== -1); });
      if (hit) group.forEach(function (g) { variants[g] = true; });
    });
    return Object.keys(variants).filter(Boolean).sort();
  }

  function parseInterests(text) {
    return String(text || '').split(/[،,;؛\n]+/).map(function (p) { return p.trim(); })
      .filter(Boolean).slice(0, 8);
  }

  function round2(x) { return Math.round(x * 100) / 100; }

  function examPercent(group, pct, coef) {
    var total = 0, weight = 0, used = [];
    group.exam_subjects.forEach(function (subject) {
      var key = subject.key;
      var p = pct[key];
      var c = (coef[key] !== undefined && coef[key] !== null) ? coef[key] : subject.coef;
      if (p === null || p === undefined || isNaN(p) || c === null || isNaN(c) || c <= 0) return;
      total += p * c;
      weight += c;
      used.push(key);
    });
    if (weight === 0) return { value: null, used: used };
    return { value: total / weight, used: used };
  }

  function schoolPercent(gpa) {
    if (gpa === null || gpa === undefined || isNaN(gpa)) return null;
    return Math.max(0, Math.min(20, gpa)) / 20 * 100;
  }

  function combinedScore(group, profile) {
    var warnings = [];
    var ex = examPercent(group, profile.pct, profile.coef);
    var exam = ex.value;
    var total = group.exam_subjects.length;
    if (exam !== null && ex.used.length < total) {
      warnings.push('بعضی دروس آزمون وارد نشده‌اند؛ میانگین فقط از دروس واردشده محاسبه شد.');
    }
    var school = schoolPercent(profile.gpa);
    var schoolW = group.school_weight / 100;
    var examW = group.exam_weight / 100;
    var score = null;
    if (exam === null && school === null) {
      warnings.push('برای محاسبه، حداقل معدل یا یک درصد آزمون را وارد کنید.');
    } else if (school === null) {
      score = exam;
      warnings.push('معدل وارد نشده؛ نمره فقط از آزمون محاسبه شده است.');
    } else if (exam === null) {
      score = school;
      warnings.push('درصد دروس آزمون وارد نشده؛ نمره فقط از معدل محاسبه شده است.');
    } else {
      score = schoolW * school + examW * exam;
    }
    if (group.weights_status !== 'verified') {
      warnings.push('سهم‌بندی این گروه در منابع تأیید نشده؛ نتیجه تقریبی است.');
    }
    if (group.coef_status === 'unverified') {
      warnings.push('ضرایب دروس این گروه تأیید نشده است؛ نتیجه تقریبی است.');
    }
    return {
      score: score === null ? null : round2(score),
      exam_percent: exam === null ? null : round2(exam),
      school_percent: school === null ? null : round2(school),
      weights: { school: group.school_weight, exam: group.exam_weight },
      subjects: group.exam_subjects.map(function (s) {
        return {
          key: s.key, label: s.label,
          pct: profile.pct[s.key] === undefined ? null : profile.pct[s.key],
          coef: (profile.coef[s.key] !== undefined && profile.coef[s.key] !== null) ? profile.coef[s.key] : s.coef
        };
      }),
      warnings: warnings
    };
  }

  function fieldSuggestions(groupKey, fields, profile) {
    var terms = profile.interests.map(function (t) { return [t, interestVariants(t)]; });
    var out = [];
    fields.forEach(function (f) {
      if (f.groups.indexOf(groupKey) === -1) return;
      var nameN = norm(f.name);
      var catN = norm(f.category);
      var padded = ' ' + nameN + ' ';
      var score = 0, reasons = [];
      terms.forEach(function (t) {
        var label = t[0], variants = t[1];
        if (nameN === norm(label)) {
          score += 8; reasons.push('مرتبط با علاقه‌ی «' + label + '»');
        } else if (variants.some(function (v) { return nameN === v; })) {
          score += 6; reasons.push('مرتبط با علاقه‌ی «' + label + '»');
        } else if (variants.some(function (v) { return padded.indexOf(' ' + v + ' ') !== -1; })) {
          score += 4; reasons.push('مرتبط با علاقه‌ی «' + label + '»');
        } else if (variants.some(function (v) { return nameN.indexOf(v) !== -1; })) {
          score += 2; reasons.push('مرتبط با علاقه‌ی «' + label + '»');
        } else if (variants.some(function (v) { return catN.indexOf(v) !== -1; })) {
          score += 1; reasons.push('هم‌دسته با علاقه‌ی «' + label + '»');
        }
      });
      out.push({ field: f, score: score, reasons: reasons });
    });
    if (terms.length) {
      var matched = out.filter(function (x) { return x.score > 0; });
      if (matched.length) out = matched;
    }
    out.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      return a.field.name < b.field.name ? -1 : (a.field.name > b.field.name ? 1 : 0);
    });
    return out;
  }

  function universitySuggestions(groupKey, unis, profile) {
    var out = [];
    var wanted = profile.univTypes;
    unis.forEach(function (u) {
      if (u.focus && u.focus.length && u.focus.indexOf(groupKey) === -1) return;
      if (wanted.length && wanted.indexOf(u.type) === -1) return;
      var score = 0, reasons = [];
      if (u.focus && u.focus.indexOf(groupKey) !== -1) { score += 5; reasons.push('تخصصی این گروه'); }
      else { score += 2; reasons.push('عمومی و چندرشته‌ای'); }
      if (profile.province && u.province === profile.province) { score += 3; reasons.push('در استان شما'); }
      if (wanted.length) { score += 2; reasons.push('نوع دانشگاه مورد نظر'); }
      out.push({ university: u, score: score, reasons: reasons });
    });
    out.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      var pa = a.university.province !== (profile.province || '') ? 1 : 0;
      var pb = b.university.province !== (profile.province || '') ? 1 : 0;
      if (pa !== pb) return pa - pb;
      return a.university.name < b.university.name ? -1 : (a.university.name > b.university.name ? 1 : 0);
    });
    return out;
  }

  function runAnalysis(data, groupSlug, profile) {
    var group = null;
    data.groups.forEach(function (g) { if (g.slug === groupSlug) group = g; });
    if (!group) return null;
    var key = group.data_key;
    return {
      group: group,
      score: combinedScore(group, profile),
      fields: fieldSuggestions(key, data.fields, profile),
      universities: universitySuggestions(key, data.universities, profile)
    };
  }

  global.RZEngine = {
    norm: norm,
    QUOTAS: QUOTAS,
    parseInterests: parseInterests,
    interestVariants: interestVariants,
    examPercent: examPercent,
    schoolPercent: schoolPercent,
    combinedScore: combinedScore,
    fieldSuggestions: fieldSuggestions,
    universitySuggestions: universitySuggestions,
    runAnalysis: runAnalysis
  };
})(window);
