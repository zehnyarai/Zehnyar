const PERSIAN_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];

export function toPersianDigits(value) {
  return String(value).replace(/[0-9]/g, (digit) => PERSIAN_DIGITS[Number(digit)]);
}

export function localiseNumber(value, lang) {
  const text = String(value);
  return lang === 'fa' ? toPersianDigits(text) : text;
}

export function groupThousands(value) {
  const rounded = Math.round(Number(value) || 0);
  return rounded.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

export function money(value, lang, currency = 'USD', symbol) {
  const symbols = { USD: '$', EUR: '€', CAD: 'C$', AUD: 'A$', GBP: '£', AED: 'AED', OMR: 'OMR', TRY: '₺', SEK: 'kr', DKK: 'kr', NZD: 'NZ$' };
  const mark = symbol || symbols[currency] || currency;
  const amount = groupThousands(value);
  if (lang === 'fa') {
    const local = toPersianDigits(amount).replace(/,/g, '٬');
    return currency === 'USD' ? `${local} دلار` : `${local} ${mark}`;
  }
  return `${mark}${amount}`;
}

export function percent(value, lang, digits = 0) {
  const rounded = Number(value).toFixed(digits).replace(/\.0$/, '');
  if (lang !== 'fa') return `${rounded}%`;
  return `${toPersianDigits(rounded).replace(/\./g, '٫')}٪`;
}

/** Localised plain number, with optional thousands grouping. */
export function num(value, lang, group = false) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return lang === 'fa' ? '—' : '—';
  const numeric = Number(value);
  const text = Number.isInteger(numeric) ? String(numeric) : String(Math.round(numeric * 10) / 10);
  const decorated = group ? groupThousands(text) : text;
  if (lang !== 'fa') return decorated;
  return toPersianDigits(decorated).replace(/,/g, '٬').replace(/\./g, '٫');
}

/** "12 / 20" style score, respecting the active language's digits. */
export function scorePair(value, max, lang) {
  return `${num(value, lang)} / ${num(max, lang)}`;
}

export function duration(years) {
  return Number(years) || 0;
}

export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}
