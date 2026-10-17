/**
 * Analysis quota and Toman payment rules — the owner's decision of 2026-10-13:
 * every farmer gets 2 free AI analyses, after that each analysis needs a paid package.
 *
 * Everything here is plain arithmetic and a keyed checksum, not cryptography:
 * an offline APK can always be tampered with by a determined user, so the checksum only
 * stops accidental/cheap editing of the counter. The panel states this openly.
 */

export const DEFAULT_FREE_ANALYSES = 2
export const DEFAULT_PACKAGE_ANALYSES = 20
/** Owner's decision of 2026-10-17: the day rate is fixed at 275,000 Toman per dollar. */
export const DEFAULT_USD_RATE = 275_000
/** And every paid analysis is priced at 3 dollars before the package discount. */
export const DEFAULT_ANALYSIS_USD = 3
export const MAX_FREE_ANALYSES = 50
export const MAX_PACKAGE_ANALYSES = 500
export const QUOTA_MIRROR_KEY = 'pestino-quota'
/** Bundled when signing activation codes. Obfuscation, not a secret delivery system. */
const CODE_SECRET = 'pestino-1404-pistachio-nilgoon-asemani'

export interface QuotaSettings {
  free_limit: number
  used: number
  credits: number
  /** Activation codes already redeemed on this device; the same code never works twice. */
  codes: string[]
}

export interface AnalysisPackage {
  analyses: number
  price_toman: number
  /** Optional USD-linked reference: base price in dollars and the dated day rate. */
  usd_price: number | null
  usd_rate: number | null
  rate_date: string | null
}

/**
 * Support packages for the owner's shop. The ladder starts at the single-analysis
 * price ($3) and gets cheaper per analysis as the farmer buys more: 20% off for five,
 * 30% off for ten and 40% off for twenty. Prices are recalculated from the day rate,
 * so changing the rate in the panel changes every package at once.
 */
export interface SupportPlan {
  id: string
  analyses: number
  usd: number
  discount_percent: number
  name: string
  note: string
}
export const SUPPORT_PLANS: SupportPlan[] = [
  {
    id: 'single',
    analyses: 1,
    usd: DEFAULT_ANALYSIS_USD,
    discount_percent: 0,
    name: 'تک‌تحلیل',
    note: 'برای یک بررسی فوری؛ بدون تخفیف.',
  },
  {
    id: 'five',
    analyses: 5,
    usd: 12,
    discount_percent: 20,
    name: 'بستهٔ ۵ تحلیلی',
    note: '۲۰٪ ارزان‌تر از خرید تک‌تک؛ برای یک فصل سبک.',
  },
  {
    id: 'ten',
    analyses: 10,
    usd: 21,
    discount_percent: 30,
    name: 'بستهٔ ۱۰ تحلیلی',
    note: '۳۰٪ ارزان‌تر؛ مناسب پایش ماهانهٔ باغ.',
  },
  {
    id: 'twenty',
    analyses: 20,
    usd: 36,
    discount_percent: 40,
    name: 'بستهٔ ۲۰ تحلیلی',
    note: '۴۰٪ ارزان‌تر؛ کامل‌ترین بسته برای یک فصل.',
  },
]
/** Rounded up to 10,000 Toman so the price is easy to type into a banking app. */
export function planPrice(plan: SupportPlan, rate = DEFAULT_USD_RATE): number {
  return Math.ceil((plan.usd * rate) / 10_000) * 10_000
}
export interface PricedPlan extends SupportPlan {
  price_toman: number
  per_analysis_toman: number
}
export function pricedPlans(rate = DEFAULT_USD_RATE): PricedPlan[] {
  return SUPPORT_PLANS.map((plan) => {
    const price = planPrice(plan, rate)
    return {
      ...plan,
      price_toman: price,
      per_analysis_toman: Math.round(price / plan.analyses),
    }
  })
}

export function defaultQuota(): QuotaSettings {
  return { free_limit: DEFAULT_FREE_ANALYSES, used: 0, credits: 0, codes: [] }
}

export function defaultPackage(): AnalysisPackage {
  const tier = SUPPORT_PLANS[SUPPORT_PLANS.length - 1]
  return {
    analyses: tier.analyses,
    price_toman: planPrice(tier, DEFAULT_USD_RATE),
    usd_price: tier.usd,
    usd_rate: DEFAULT_USD_RATE,
    rate_date: '2026-10-17',
  }
}

export function quotaView(quota: QuotaSettings, pack: AnalysisPackage) {
  const freeLeft = Math.max(0, quota.free_limit - quota.used)
  const credits = Math.max(0, Math.floor(quota.credits))
  return {
    free_limit: quota.free_limit,
    used: quota.used,
    free_left: freeLeft,
    credits,
    total_left: freeLeft + credits,
    blocked: freeLeft <= 0 && credits <= 0,
    analyses_per_package: pack.analyses,
    price_toman: pack.price_toman,
    usd_price: pack.usd_price,
    usd_rate: pack.usd_rate,
    rate_date: pack.rate_date,
    needs_price: pack.price_toman <= 0,
  }
}
export type QuotaView = ReturnType<typeof quotaView>

/** Full payload of GET /local/quota: what the payment screen needs to be honest. */
export interface QuotaPayload extends QuotaView {
  package: AnalysisPackage
  /** The four support packages, priced from the owner's day rate. */
  plans: PricedPlan[]
  card: { card_number: string; holder: string; bank: string } | null
  pending_receipts: number
  codes_used: number
  notice: string
}

const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'
export function normaliseDigits(value: string): string {
  return [...value]
    .map((ch) => {
      const fa = FA_DIGITS.indexOf(ch)
      if (fa >= 0) return String(fa)
      const ar = AR_DIGITS.indexOf(ch)
      return ar >= 0 ? String(ar) : ch
    })
    .join('')
}
function wholeNumber(value: unknown, label: string, min: number, max: number): number {
  const n = Number(
    typeof value === 'string' ? normaliseDigits(value).replace(/[,٬\s]/g, '') : value
  )
  if (!Number.isInteger(n) || n < min || n > max)
    throw new Error(
      `${label} باید عددی بین ${min.toLocaleString('fa-IR')} و ${max.toLocaleString('fa-IR')} باشد.`
    )
  return n
}

/** Toman price the owner should ask for: dollars × the day rate, rounded up to 10,000. */
export function suggestedToman(usdPrice: number | null, usdRate: number | null): number {
  if (!usdPrice || !usdRate || usdPrice <= 0 || usdRate <= 0) return 0
  return Math.ceil((usdPrice * usdRate) / 10_000) * 10_000
}

export function validatePackage(raw: unknown): AnalysisPackage {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw))
    throw new Error('تنظیمات بسته معتبر نیست.')
  const body = raw as Record<string, unknown>
  const analyses = wholeNumber(body.analyses, 'تعداد تحلیل هر بسته', 1, MAX_PACKAGE_ANALYSES)
  const usd =
    body.usd_price === null || body.usd_price === undefined || body.usd_price === ''
      ? null
      : Number(normaliseDigits(String(body.usd_price)).replace(/[,٬\s]/g, ''))
  const rate =
    body.usd_rate === null || body.usd_rate === undefined || body.usd_rate === ''
      ? null
      : Number(normaliseDigits(String(body.usd_rate)).replace(/[,٬\s]/g, ''))
  if (usd !== null && (!Number.isFinite(usd) || usd <= 0 || usd > 100_000))
    throw new Error('قیمت پایه دلاری باید عددی مثبت و کمتر از ۱۰۰٬۰۰۰ دلار باشد.')
  if (rate !== null && (!Number.isFinite(rate) || rate <= 0 || rate > 100_000_000))
    throw new Error('نرخ دلار روز باید عددی مثبت و کمتر از ۱۰۰ میلیون تومان باشد.')
  const suggested = suggestedToman(usd, rate)
  const suppliedPrice = body.price_toman
  const given = !(suppliedPrice === undefined || suppliedPrice === null || suppliedPrice === '')
  // No price at all is allowed while the owner is still deciding; the panel says "needs price".
  const price = given
    ? wholeNumber(suppliedPrice, 'قیمت بسته به تومان', 10_000, 5_000_000_000)
    : suggested
  if (suggested && price && price < suggested)
    throw new Error('قیمت تومانی نباید از قیمت پایه دلاری × نرخ روز کمتر باشد.')
  const rateDate =
    body.rate_date === null || body.rate_date === undefined ? null : String(body.rate_date)
  if (rateDate && !/^\d{4}-\d{2}-\d{2}$/.test(rateDate))
    throw new Error('تاریخ نرخ دلار باید به شکل ۲۰۲۶-۱۰-۱۳ باشد.')
  return { analyses, price_toman: price, usd_price: usd, usd_rate: rate, rate_date: rateDate }
}

/* ------------------------------------------------------------------ *
 * Activation codes the owner generates and sends after a real payment *
 * ------------------------------------------------------------------ */

const ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
function fnv1a(text: string, seed: number): number {
  let hash = seed >>> 0
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 16_777_619)
  }
  return hash >>> 0
}
/** 6 characters, 30 bits of keyed mixing — enough to make codes guesswork-proof-ish. */
export function codeChecksum(payload: string, secret = CODE_SECRET): string {
  const a = fnv1a(`${secret}|${payload}`, 0x811c9dc5)
  const b = fnv1a(`${payload}|${secret}|${a}`, 0x01000193 ^ a)
  let value = ((a >>> 2) ^ Math.imul(b, 2_246_822_519)) >>> 0
  let out = ''
  for (let i = 0; i < 6; i += 1) {
    // The alphabet has no lookalike letters (I/L/O/0/1), so it is 31 long, not 32:
    // index with a modulo and never with a bit mask.
    out += ALPHABET[value % ALPHABET.length]
    value = Math.floor(value / ALPHABET.length)
  }
  return out
}
export function addDays(stamp: string, days: number): string {
  const base = new Date(`${stamp}T12:00:00Z`)
  base.setUTCDate(base.getUTCDate() + days)
  return base.toISOString().slice(0, 10)
}

export interface GeneratedCode {
  code: string
  analyses: number
  expires_on: string | null
}
/** Owner side: one code per paid package, optionally with a validity window in days. */
export function createActivationCode(input: {
  analyses: number
  days?: number | null
  today: string
  serial?: number
}): GeneratedCode {
  const analyses = wholeNumber(input.analyses, 'تعداد تحلیل کد', 1, MAX_PACKAGE_ANALYSES)
  const days = input.days ? wholeNumber(input.days, 'اعتبار کد (روز)', 1, 3650) : null
  const expiresOn = days ? addDays(input.today, days) : null
  const expiry = expiresOn ? expiresOn.replace(/-/g, '') : '0'
  const serial = String(input.serial ?? Math.floor(1000 + Math.random() * 9000)).padStart(4, '0')
  const payload = `${analyses.toString(36).toUpperCase()}-${expiry}-${serial}`
  return {
    code: `PST-${payload}-${codeChecksum(payload)}`,
    analyses,
    expires_on: expiresOn,
  }
}

export type CodeResult =
  { ok: true; analyses: number; expires_on: string | null } | { ok: false; reason: string }

/**
 * Farmer side. The same code never works twice on one device, and expired codes are
 * refused with the date the owner set.
 */
export function verifyActivationCode(
  raw: string,
  options: { today: string; used?: string[] }
): CodeResult {
  const compact = normaliseDigits(String(raw ?? ''))
    .toUpperCase()
    .replace(/[\s,_ـ]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
  const parts = compact.split('-')
  if (parts.length !== 5 || parts[0] !== 'PST')
    return { ok: false, reason: 'قالب کد فعال‌سازی درست نیست؛ کد به شکل PST-… فرستاده می‌شود.' }
  const [, analysesPart, expiryPart, serial, check] = parts
  if (
    !/^[0-9A-Z]{1,3}$/.test(analysesPart) ||
    !/^\d{4}$/.test(serial) ||
    !/^[0-9A-Z]{6}$/.test(check)
  )
    return { ok: false, reason: 'قالب کد فعال‌سازی درست نیست.' }
  if (expiryPart !== '0' && !/^\d{8}$/.test(expiryPart))
    return { ok: false, reason: 'تاریخ اعتبار کد درست نیست.' }
  const payload = `${analysesPart}-${expiryPart}-${serial}`
  if (codeChecksum(payload) !== check) return { ok: false, reason: 'این کد معتبر نیست.' }
  if ((options.used ?? []).includes(compact))
    return { ok: false, reason: 'این کد قبلاً روی همین دستگاه استفاده شده است.' }
  const analyses = parseInt(analysesPart, 36)
  if (!Number.isInteger(analyses) || analyses < 1 || analyses > MAX_PACKAGE_ANALYSES)
    return { ok: false, reason: 'تعداد تحلیل این کد درست نیست.' }
  let expiresOn: string | null = null
  if (expiryPart !== '0') {
    expiresOn = `${expiryPart.slice(0, 4)}-${expiryPart.slice(4, 6)}-${expiryPart.slice(6, 8)}`
    if (Number.isNaN(Date.parse(`${expiresOn}T12:00:00Z`)))
      return { ok: false, reason: 'تاریخ اعتبار کد درست نیست.' }
    if (options.today > expiresOn)
      return { ok: false, reason: `این کد در تاریخ ${expiresOn} منقضی شده است.` }
  }
  return { ok: true, analyses, expires_on: expiresOn }
}

/* ------------------------------------------------------------- *
 * Tamper-evident mirror of the counter (localStorage + IndexedDB) *
 * ------------------------------------------------------------- */
export interface QuotaMirror {
  used: number
  credits: number
  codes: string[]
}
function fingerprint(mirror: QuotaMirror): string {
  return codeChecksum(`${mirror.used}.${mirror.credits}.${mirror.codes.length}`)
}
export function writeQuotaMirror(store: Pick<Storage, 'setItem'>, mirror: QuotaMirror): void {
  try {
    store.setItem(QUOTA_MIRROR_KEY, JSON.stringify({ ...mirror, check: fingerprint(mirror) }))
  } catch {
    /* private mode or full storage: the IndexedDB copy still holds the truth */
  }
}
export function readQuotaMirror(store: Pick<Storage, 'getItem'>): QuotaMirror | null {
  try {
    const raw = store.getItem(QUOTA_MIRROR_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<QuotaMirror> & { check?: string }
    const mirror: QuotaMirror = {
      used: Number(parsed.used) || 0,
      credits: Number(parsed.credits) || 0,
      codes: Array.isArray(parsed.codes) ? parsed.codes.filter((c) => typeof c === 'string') : [],
    }
    if (mirror.used < 0 || mirror.credits < 0 || parsed.check !== fingerprint(mirror)) return null
    return mirror
  } catch {
    return null
  }
}
/**
 * The counter can only move against the cheater: the higher "used" and the lower
 * "credits" win, so editing either store by hand never buys free analyses.
 */
export function reconcileQuota(stored: QuotaSettings, mirror: QuotaMirror | null): QuotaSettings {
  if (!mirror) return stored
  return {
    free_limit: stored.free_limit,
    used: Math.max(stored.used, mirror.used),
    credits: Math.min(stored.credits, mirror.credits),
    codes: [...new Set([...stored.codes, ...mirror.codes])],
  }
}
/** True when a free analysis is still available; otherwise a paid credit is spent. */
export function quotaDecision(quota: QuotaSettings): {
  free: boolean
  allowed: boolean
  reason: string
} {
  if (quota.used < quota.free_limit) return { free: true, allowed: true, reason: '' }
  if (quota.credits > 0) return { free: false, allowed: true, reason: '' }
  return {
    free: false,
    allowed: false,
    reason: `از ${quota.free_limit.toLocaleString('fa-IR')} تحلیل رایگان این دستگاه استفاده شده است؛ برای تحلیل بعدی یک بستهٔ تومانی تهیه کنید.`,
  }
}
export function consumeQuota(quota: QuotaSettings): QuotaSettings {
  const decision = quotaDecision(quota)
  if (!decision.allowed) return quota
  if (decision.free) return { ...quota, used: quota.used + 1 }
  return { ...quota, credits: quota.credits - 1 }
}
/** A failed model call must never cost the farmer anything. */
export function refundQuota(quota: QuotaSettings, wasFree: boolean): QuotaSettings {
  if (wasFree) return { ...quota, used: Math.max(0, quota.used - 1) }
  return { ...quota, credits: quota.credits + 1 }
}
export const QUOTA_REQUIRED = 'QUOTA_REQUIRED'
/** Marker thrown by the device API so the UI can open the payment card instead of an error. */
export class QuotaRequired extends Error {
  code = QUOTA_REQUIRED
  constructor(message: string) {
    super(message)
  }
}
