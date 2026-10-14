import { describe, expect, it } from 'vitest'
import {
  DEFAULT_FREE_ANALYSES,
  consumeQuota,
  createActivationCode,
  defaultPackage,
  defaultQuota,
  quotaDecision,
  quotaView,
  readQuotaMirror,
  reconcileQuota,
  refundQuota,
  suggestedToman,
  validatePackage,
  verifyActivationCode,
  writeQuotaMirror,
} from './quota'

const today = '2026-10-14'
const memory = (initial: Record<string, string> = {}) => {
  const store = new Map(Object.entries(initial))
  return {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    size: () => store.size,
  }
}

describe('free analyses, then a Toman package', () => {
  it('starts with exactly two free analyses and blocks the third', () => {
    expect(DEFAULT_FREE_ANALYSES).toBe(2)
    let quota = defaultQuota()
    expect(quotaDecision(quota)).toMatchObject({ free: true, allowed: true })
    quota = consumeQuota(quota)
    expect(quota.used).toBe(1)
    quota = consumeQuota(quota)
    expect(quota.used).toBe(2)
    const view = quotaView(quota, defaultPackage())
    expect(view.free_left).toBe(0)
    expect(view.blocked).toBe(true)
    expect(quotaDecision(quota).allowed).toBe(false)
    expect(quotaDecision(quota).reason).toContain('تحلیل رایگان')
    // A blocked device never gains or loses anything by pressing again.
    expect(consumeQuota(quota)).toEqual(quota)
  })
  it('spends paid credits only after the free ones, and never charges for a failure', () => {
    let quota = { ...defaultQuota(), used: 2, credits: 3 }
    expect(quotaDecision(quota)).toMatchObject({ free: false, allowed: true })
    quota = consumeQuota(quota)
    expect(quota.credits).toBe(2)
    // Refund puts back exactly what was taken — a refused or failed model call is free.
    expect(refundQuota(quota, false).credits).toBe(3)
    const free = consumeQuota({ ...defaultQuota(), used: 1 })
    expect(refundQuota(free, true).used).toBe(1)
  })
  it('prices the package from the dollar day rate and refuses a cheaper Toman price', () => {
    expect(suggestedToman(2, 92_000)).toBe(190_000) // 184,000 rounded up to 10,000
    const pack = validatePackage({
      analyses: 20,
      usd_price: 2,
      usd_rate: 92_000,
      rate_date: '2026-10-14',
      price_toman: 250_000,
    })
    expect(pack.price_toman).toBe(250_000)
    expect(() =>
      validatePackage({ analyses: 20, usd_price: 2, usd_rate: 92_000, price_toman: 100_000 })
    ).toThrow(/کمتر/)
    expect(() => validatePackage({ analyses: 0, price_toman: 100_000 })).toThrow()
    // No dollar input: the owner's own Toman price is accepted as-is.
    expect(validatePackage({ analyses: 5, price_toman: 500_000 }).price_toman).toBe(500_000)
    // Persian digits typed on a phone keyboard must work.
    expect(validatePackage({ analyses: '۱۰', price_toman: '۱۲۰۰۰۰' }).analyses).toBe(10)
  })
  it('signs activation codes the owner can send after a real transfer', () => {
    const generated = createActivationCode({ analyses: 20, today, serial: 4821, days: 30 })
    expect(generated.code).toMatch(/^PST-[0-9A-Z]+-20261113-4821-[0-9A-Z]{6}$/)
    const verified = verifyActivationCode(generated.code, { today })
    expect(verified).toEqual({ ok: true, analyses: 20, expires_on: '2026-11-13' })
    // Every generated code must verify: an off-by-one alphabet once produced "undefined".
    for (let i = 0; i < 400; i += 1) {
      const sample = createActivationCode({ analyses: 1 + (i % 500), today })
      expect(sample.code).not.toContain('undefined')
      expect(verifyActivationCode(sample.code, { today }).ok).toBe(true)
    }
    // Persian digits and loose spacing are normalised before checking.
    const typed = generated.code.replace('PST-', 'pst ').replace(/-/g, ' ')
    expect(verifyActivationCode(typed, { today }).ok).toBe(true)
  })
  it('rejects a forged, reused or expired code', () => {
    const generated = createActivationCode({ analyses: 5, today, serial: 1111 })
    const forged = `${generated.code.slice(0, -1)}${generated.code.endsWith('A') ? 'B' : 'A'}`
    expect(verifyActivationCode(forged, { today })).toMatchObject({ ok: false })
    expect(verifyActivationCode('PST-20-0-4821-AAAAAA', { today })).toMatchObject({ ok: false })
    const nonsense = verifyActivationCode('سلام', { today })
    expect(nonsense.ok).toBe(false)
    expect(nonsense.ok ? '' : nonsense.reason).toContain('قالب کد')
    expect(verifyActivationCode(generated.code, { today, used: [generated.code] })).toMatchObject({
      ok: false,
    })
    const short = createActivationCode({ analyses: 3, today, serial: 7, days: 1 })
    expect(verifyActivationCode(short.code, { today: '2026-10-20' })).toMatchObject({ ok: false })
  })
  it('keeps a tamper-evident mirror so editing one store cannot mint free analyses', () => {
    const store = memory()
    writeQuotaMirror(store, { used: 2, credits: 1, codes: ['PST-A'] })
    expect(readQuotaMirror(store)).toEqual({ used: 2, credits: 1, codes: ['PST-A'] })
    // Someone rewrites the mirror to look unused; the checksum no longer matches.
    store.setItem(
      'pestino-quota',
      JSON.stringify({ used: 0, credits: 99, codes: [], check: 'WRONG' })
    )
    expect(readQuotaMirror(store)).toBeNull()
    // Even with a valid mirror, the counter only ever moves against the cheater.
    writeQuotaMirror(store, { used: 2, credits: 0, codes: [] })
    const merged = reconcileQuota(
      { ...defaultQuota(), used: 1, credits: 5, codes: [] },
      readQuotaMirror(store)
    )
    expect(merged.used).toBe(2)
    expect(merged.credits).toBe(0)
  })
})
