const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
const ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩';

/** Converts Persian / Arabic-Indic digits to ASCII and strips separators. */
export function toAsciiDigits(input: string): string {
  return input
    .replace(/[۰-۹]/g, (d) => String(PERSIAN_DIGITS.indexOf(d)))
    .replace(/[٠-٩]/g, (d) => String(ARABIC_DIGITS.indexOf(d)))
    .replace(/[\s\-()]/g, '');
}

/**
 * Normalizes an Iranian mobile number to the canonical form 09XXXXXXXXX.
 * Accepts: 09121234567, 9121234567, +989121234567, 00989121234567, ۰۹۱۲...
 * Returns null when the input is not a valid Iranian mobile number.
 */
export function normalizeIranianMobile(input: string): string | null {
  let s = toAsciiDigits(String(input ?? '').trim());
  if (s.startsWith('+')) s = s.slice(1);
  if (s.startsWith('00')) s = s.slice(2);
  if (s.startsWith('98') && s.length === 12) s = s.slice(2);
  if (s.length === 10 && s.startsWith('9')) s = '0' + s;
  return /^09\d{9}$/.test(s) ? s : null;
}
