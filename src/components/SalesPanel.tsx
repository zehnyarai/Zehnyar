import { useEffect, useState } from 'react'
import { BadgeCheck, Gift, KeyRound, Save, ShoppingBag, Wallet } from 'lucide-react'
import { api, errorMessage, fa, persianDate } from '../api'
import type { AppContext } from '../types'
import { BASE_ANALYSIS_TOMAN, SUPPORT_PLANS, planPrice } from '../quota'
import type { QuotaPayload } from '../quota'
import { InfoBanner, Spinner } from './ui'

const digits = (value: string) => value.replace(/[^\d۰-۹٠-٩]/g, '')
const toEnglish = (value: string) =>
  [...value]
    .map((ch) => {
      const fa = '۰۱۲۳۴۵۶۷۸۹'.indexOf(ch)
      if (fa >= 0) return String(fa)
      const ar = '٠١٢٣٤٥٦٧٨٩'.indexOf(ch)
      return ar >= 0 ? String(ar) : ch
    })
    .join('')
const number = (value: string) => Number(toEnglish(digits(value) || '0'))

/**
 * The owner's shop: two free analyses, then the four support packages that are all priced
 * from the same single-analysis base (owner's 2026-10-17 decision: 350,000 Toman), with
 * 10%, 20% and 30% volume discounts. The owner edits that base price and the code
 * generator; the credits page and the receipt check follow automatically.
 */
export default function SalesPanel({ ctx }: { ctx: AppContext }) {
  const [quota, setQuota] = useState<QuotaPayload | null>(null)
  const [form, setForm] = useState({
    free_limit: '2',
    base: String(BASE_ANALYSIS_TOMAN),
  })
  const [planId, setPlanId] = useState('five')
  const [days, setDays] = useState('')
  const [code, setCode] = useState<{
    code: string
    analyses: number
    expires_on: string | null
  } | null>(null)
  const [gift, setGift] = useState('5')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [note, setNote] = useState('')

  useEffect(() => {
    let active = true
    void api<QuotaPayload>('/local/quota')
      .then((payload) => {
        if (!active) return
        setQuota(payload)
        setForm({
          free_limit: String(payload.free_limit),
          base: String(payload.base_toman || BASE_ANALYSIS_TOMAN),
        })
      })
      .catch((e) => active && setError(errorMessage(e)))
    return () => {
      active = false
    }
  }, [])

  const base = number(form.base) || BASE_ANALYSIS_TOMAN
  const plan = SUPPORT_PLANS.find((p) => p.id === planId) ?? SUPPORT_PLANS[1]
  async function run(action: () => Promise<unknown>, message: string) {
    if (busy) return
    setBusy(true)
    setError('')
    setNote('')
    try {
      await action()
      const payload = await api<QuotaPayload>('/local/quota')
      setQuota(payload)
      setForm({
        free_limit: String(payload.free_limit),
        base: String(payload.base_toman || base),
      })
      await ctx.refresh()
      setNote(message)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  const save = () =>
    run(
      () =>
        api('/local/quota', {
          method: 'PUT',
          body: JSON.stringify({
            free_limit: number(form.free_limit),
            package: {
              analyses: SUPPORT_PLANS[SUPPORT_PLANS.length - 1].analyses,
              base_toman: base,
              price_toman: planPrice(SUPPORT_PLANS[SUPPORT_PLANS.length - 1], base),
            },
          }),
        }),
      'قیمت هر تحلیل و تحلیل‌های رایگان ذخیره شد؛ هر چهار بسته به‌روز شد.'
    )
  const makeCode = () =>
    run(async () => {
      const generated = await api<{ code: string; analyses: number; expires_on: string | null }>(
        '/local/quota/code',
        {
          method: 'POST',
          body: JSON.stringify({
            analyses: plan.analyses,
            days: days ? number(days) : null,
          }),
        }
      )
      setCode(generated)
    }, 'کد ساخته شد؛ آن را برای پرداخت‌کننده بفرستید.')
  const grant = () =>
    run(
      () =>
        api('/local/quota/grant', {
          method: 'POST',
          body: JSON.stringify({ analyses: number(gift) }),
        }),
      'تحلیل هدیه به همین دستگاه اضافه شد.'
    )

  return (
    <section className="reference-card" aria-label="فروش تحلیل">
      <h2>
        <ShoppingBag size={22} /> قیمت‌گذاری و کد فعال‌سازی
      </h2>
      <p className="section-description">
        قیمت یک تحلیل را به تومان بنویسید؛ هر چهار بسته از همان عدد با تخفیف ۱۰، ۲۰ و ۳۰ درصد حساب
        می‌شوند. کاربر فقط قیمت تومانی را می‌بیند.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          void save()
        }}
      >
        <fieldset disabled={busy}>
          <div className="reference-form-grid">
            <label>
              تحلیل رایگان هر دستگاه
              <input
                dir="ltr"
                inputMode="numeric"
                value={form.free_limit}
                onChange={(e) => setForm({ ...form, free_limit: e.target.value })}
              />
            </label>
            <label>
              قیمت هر تحلیل (تومان)
              <input
                dir="ltr"
                inputMode="numeric"
                value={form.base}
                onChange={(e) => setForm({ ...form, base: e.target.value })}
              />
            </label>
          </div>
          <div className="table-scroll">
            <table className="plan-table">
              <thead>
                <tr>
                  <th>بسته</th>
                  <th>تحلیل</th>
                  <th>تخفیف</th>
                  <th>تومان</th>
                  <th>هر تحلیل</th>
                </tr>
              </thead>
              <tbody>
                {SUPPORT_PLANS.map((p) => {
                  const price = planPrice(p, base)
                  return (
                    <tr key={p.id}>
                      <td>{p.name}</td>
                      <td>{fa(p.analyses)}</td>
                      <td>{p.discount_percent ? `${fa(p.discount_percent)}٪` : '—'}</td>
                      <td dir="ltr">{fa(price)}</td>
                      <td dir="ltr">{fa(Math.round(price / p.analyses))}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <button className="button primary" type="submit">
            <Save size={17} /> ذخیرهٔ قیمت
          </button>
        </fieldset>
      </form>
      {quota && (
        <p className="muted">
          این دستگاه: {fa(quota.free_left)} تحلیل رایگان از {fa(quota.free_limit)} · بستهٔ
          خریداری‌شده: {fa(quota.credits)}
          {quota.pending_receipts ? ` · رسید در انتظار تأیید: ${fa(quota.pending_receipts)}` : ''}
        </p>
      )}

      <div className="sales-actions">
        <div className="sales-block">
          <h3>
            <KeyRound size={18} /> ساخت کد پس از واریز
          </h3>
          <div className="reference-form-grid">
            <label>
              بسته
              <select value={planId} onChange={(e) => setPlanId(e.target.value)}>
                {SUPPORT_PLANS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} — {fa(planPrice(p, base))} تومان
                  </option>
                ))}
              </select>
            </label>
            <label>
              اعتبار کد (روز) — اختیاری
              <input
                dir="ltr"
                inputMode="numeric"
                value={days}
                onChange={(e) => setDays(e.target.value)}
                placeholder="خالی = بدون انقضا"
              />
            </label>
          </div>
          <button className="button secondary" disabled={busy} onClick={() => void makeCode()}>
            {busy ? <Spinner /> : <KeyRound size={17} />}
            ساخت کد
          </button>
          {code && (
            <div className="activation-code">
              <label>
                کد برای فرستادن به پرداخت‌کننده
                <input dir="ltr" readOnly value={code.code} onFocus={(e) => e.target.select()} />
              </label>
              <p className="muted">
                {fa(code.analyses)} تحلیل
                {code.expires_on ? ` · تا ${persianDate(code.expires_on)}` : ' · بدون تاریخ انقضا'}
              </p>
            </div>
          )}
        </div>
        <div className="sales-block">
          <h3>
            <Gift size={18} /> هدیه یا تسویهٔ حضوری
          </h3>
          <label>
            تعداد تحلیل
            <input
              dir="ltr"
              inputMode="numeric"
              value={gift}
              onChange={(e) => setGift(e.target.value)}
            />
          </label>
          <button className="button secondary" disabled={busy} onClick={() => void grant()}>
            <Wallet size={17} /> افزودن به این دستگاه
          </button>
        </div>
      </div>
      {note && (
        <p className="paywall-done" role="status">
          <BadgeCheck size={18} /> {note}
        </p>
      )}
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      <InfoBanner>
        پرداخت کارت‌به‌کارت است: کاربر واریز می‌کند، شما کد می‌سازید و می‌فرستید. تأیید خودکار بانکی
        وجود ندارد و این برنامه وجهی دریافت نمی‌کند.
      </InfoBanner>
    </section>
  )
}
