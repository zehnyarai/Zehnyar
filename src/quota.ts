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
/**
 * Owner's decision of 2026-10-17 (second round): one analysis costs 350,000 Toman, and
 * every larger package is calculated from that same base with a volume discount.
 * No dollar rate is involved in the farmer's price any more.
 */
export const BASE_ANALYSIS_TOMAN = 350_000
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
  /** Analyses in the owner's default (largest) package, kept for the receipt fallback. */
  analyses: number
  price_toman: number
  /** What one single analysis costs; the whole discount ladder is built on this number. */
  base_toman: number
}

/**
 * Support packages for the owner's shop. Every price is the single-analysis base
 * multiplied by the number of analyses, minus the volume discount, rounded up to 10,000
 * Toman (5,000 is enough for every step) so it is easy to type into a banking app. With the
 * owner's 350,000 Toman base:
 * one analysis 350,000; five at 10% off = 1,575,000 (315,000 each);
 * ten at 20% off = 2,800,000 (280,000 each); twenty at 30% off = 4,900,000 (245,000 each).
 */
export interface SupportPlan {
  id: string
  analyses: number
  discount_percent: number
  name: string
  note: string
}
export const SUPPORT_PLANS: SupportPlan[] = [
  {
    id: 'single',
    analyses: 1,
    discount_percent: 0,
    name: 'تک‌تحلیل',
    note: 'یک بررسی فوری؛ بدون تخفیف.',
  },
  {
    id: 'five',
    analyses: 5,
    discount_percent: 10,
    name: 'بستهٔ ۵ تحلیلی',
    note: '۱۰٪ ارزان‌تر از خرید تک‌تک؛ برای یک فصل سبک.',
  },
  {
    id: 'ten',
    analyses: 10,
    discount_percent: 20,
    name: 'بستهٔ ۱۰ تحلیلی',
    note: '۲۰٪ ارزان‌تر؛ مناسب پایش ماهانهٔ باغ.',
  },
  {
    id: 'twenty',
    analyses: 20,
    discount_percent: 30,
    name: 'بستهٔ ۲۰ تحلیلی',
    note: '۳۰٪ ارزان‌تر؛ کامل‌ترین بسته برای یک فصل.',
  },
]
/** Rounded up to 5,000 Toman so every discounted step stays a whole, typeable amount. */
export function planPrice(plan: SupportPlan, base = BASE_ANALYSIS_TOMAN): number {
  const raw = plan.analyses * base * (1 - plan.discount_percent / 100)
  return Math.ceil(raw / 5_000) * 5_000
}
export interface PricedPlan extends SupportPlan {
  price_toman: number
  per_analysis_toman: number
}
export function pricedPlans(base = BASE_ANALYSIS_TOMAN): PricedPlan[] {
  return SUPPORT_PLANS.map((plan) => {
    const price = planPrice(plan, base)
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
    price_toman: planPrice(tier),
    base_toman: BASE_ANALYSIS_TOMAN,
  }
}

/**
 * Reads a package saved by an older build (which stored dollar fields). Anything that
 * does not carry the new per-analysis Toman base is replaced by the current ladder, so a
 * device upgraded from 0.7.4 never shows a stale 9,900,000-Toman price.
 */
export function normalizePackage(raw: unknown): AnalysisPackage {
  const body = (raw ?? {}) as Record<string, unknown>
  const base = Number(body.base_toman)
  if (!Number.isInteger(base) || base < 1_000 || base > 100_000_000) return defaultPackage()
  const analyses = Number(body.analyses)
  const size = SUPPORT_PLANS.some((p) => p.analyses === analyses)
    ? analyses
    : SUPPORT_PLANS[SUPPORT_PLANS.length - 1].analyses
  const tier = SUPPORT_PLANS.find((p) => p.analyses === size) ?? SUPPORT_PLANS[0]
  return { analyses: size, price_toman: planPrice(tier, base), base_toman: base }
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
    base_toman: pack.base_toman,
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

/** Only whole paid analyses; exact discounted package amounts retain their discount. */
export function analysesForPayment(amount: number, pack: AnalysisPackage): number {
  if (!Number.isFinite(amount) || amount < 0) return 0
  const plans = pricedPlans(pack.base_toman)
  const exact = [{ analyses: pack.analyses, price_toman: pack.price_toman }, ...plans].find(
    (p) => p.price_toman === amount
  )
  return Math.min(
    MAX_PACKAGE_ANALYSES,
    exact ? exact.analyses : Math.floor(amount / plans[0].per_analysis_toman)
  )
}

export function validatePackage(raw: unknown): AnalysisPackage {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw))
    throw new Error('تنظیمات بسته معتبر نیست.')
  const body = raw as Record<string, unknown>
  const analyses = wholeNumber(body.analyses, 'تعداد تحلیل هر بسته', 1, MAX_PACKAGE_ANALYSES)
  const base = wholeNumber(body.base_toman, 'قیمت هر تحلیل', 10_000, 100_000_000)
  const suppliedPrice = body.price_toman
  const given = !(suppliedPrice === undefined || suppliedPrice === null || suppliedPrice === '')
  // A package can never cost more than its analyses bought one by one, so a typo in the
  // package price cannot overcharge a farmer.
  const fullPrice = analyses * base
  const tier = SUPPORT_PLANS.find((p) => p.analyses === analyses)
  const suggested = tier ? planPrice(tier, base) : fullPrice
  const price = given
    ? wholeNumber(suppliedPrice, 'قیمت بسته به تومان', base, fullPrice)
    : suggested
  return { analyses, price_toman: price, base_toman: base }
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
