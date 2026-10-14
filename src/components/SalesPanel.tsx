import { useEffect, useState } from 'react'
import { BadgeCheck, Gift, KeyRound, RefreshCw, Save, ShoppingBag, Wallet } from 'lucide-react'
import { api, errorMessage, fa, persianDate, today } from '../api'
import type { AppContext } from '../types'
import { suggestedToman } from '../quota'
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
 * The owner's side of the rule "two free analyses, then a Toman package": set the limits and
 * the price, generate an activation code after a real transfer, and unlock this device.
 */
export default function SalesPanel({ ctx }: { ctx: AppContext }) {
  const [quota, setQuota] = useState<QuotaPayload | null>(null)
  const [form, setForm] = useState({
    free_limit: '2',
    analyses: '20',
    usd_price: '',
    usd_rate: '',
    rate_date: today(),
    price_toman: '',
  })
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

  const suggested = suggestedToman(
    form.usd_price ? number(form.usd_price) : null,
    form.usd_rate ? number(form.usd_rate) : null
  )
  async function load() {
    try {
      const payload = await api<QuotaPayload>('/local/quota')
      setQuota(payload)
      setForm({
        free_limit: String(payload.free_limit),
        analyses: String(payload.analyses_per_package),
        usd_price: payload.usd_price ? String(payload.usd_price) : '',
        usd_rate: payload.usd_rate ? String(payload.usd_rate) : '',
        rate_date: payload.rate_date ?? today(),
        price_toman: payload.price_toman ? String(payload.price_toman) : '',
      })
    } catch (e) {
      setError(errorMessage(e))
    }
  }
  useEffect(() => {
    let active = true
    void api<QuotaPayload>('/local/quota')
      .then((payload) => {
        if (!active) return
        setQuota(payload)
        setForm((old) => ({
          ...old,
          free_limit: String(payload.free_limit),
          analyses: String(payload.analyses_per_package),
          usd_price: payload.usd_price ? String(payload.usd_price) : '',
          usd_rate: payload.usd_rate ? String(payload.usd_rate) : '',
          rate_date: payload.rate_date ?? old.rate_date,
          price_toman: payload.price_toman ? String(payload.price_toman) : '',
        }))
      })
      .catch((e) => active && setError(errorMessage(e)))
    return () => {
      active = false
    }
  }, [])
  async function run(action: () => Promise<unknown>, message: string) {
    if (busy) return
    setBusy(true)
    setError('')
    setNote('')
    try {
      await action()
      await load()
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
              analyses: number(form.analyses),
              usd_price: form.usd_price ? number(form.usd_price) : null,
              usd_rate: form.usd_rate ? number(form.usd_rate) : null,
              rate_date: form.usd_rate ? form.rate_date : null,
              price_toman: number(form.price_toman) || suggested,
            },
          }),
        }),
      'تنظیمات تحلیل رایگان و بستهٔ تومانی ذخیره شد.'
    )
  const makeCode = () =>
    run(async () => {
      const generated = await api<{ code: string; analyses: number; expires_on: string | null }>(
        '/local/quota/code',
        {
          method: 'POST',
          body: JSON.stringify({
            analyses: number(form.analyses),
            days: days ? number(days) : null,
          }),
        }
      )
      setCode(generated)
    }, 'کد فعال‌سازی ساخته شد؛ آن را برای پرداخت‌کننده بفرستید.')
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
    <section className="reference-card" aria-label="فروش تحلیل و تحلیل‌های رایگان">
      <h2>
        <ShoppingBag size={22} /> تحلیل رایگان، بستهٔ تومانی و کد فعال‌سازی
      </h2>
      <InfoBanner>
        هر دستگاه {fa(quota?.free_limit ?? 2)} تحلیل رایگان دارد؛ بعد از آن برای هر تحلیل باید یک
        بستهٔ تومانی تهیه شود. باغ، پرونده، عکس، دانشنامه و تقویم هیچ محدودیتی ندارند و آفلاین کار
        می‌کنند. پرداخت کارت‌به‌کارت است: پس از واریز، شما کد فعال‌سازی می‌سازید و برای پرداخت‌کننده
        می‌فرستید.
      </InfoBanner>
      {quota && (
        <p className="muted">
          وضعیت این دستگاه: <strong>{fa(quota.free_left)}</strong> تحلیل رایگان باقی‌مانده از{' '}
          {fa(quota.free_limit)} · بستهٔ خریداری‌شده: <strong>{fa(quota.credits)}</strong> · کدهای
          استفاده‌شده: {fa(quota.codes_used)}
          {quota.pending_receipts ? ` · رسید در انتظار تأیید: ${fa(quota.pending_receipts)}` : ''}
        </p>
      )}
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
              تعداد تحلیل هر بسته
              <input
                dir="ltr"
                inputMode="numeric"
                value={form.analyses}
                onChange={(e) => setForm({ ...form, analyses: e.target.value })}
              />
            </label>
            <label>
              قیمت پایهٔ بسته (دلار) — اختیاری
              <input
                dir="ltr"
                inputMode="decimal"
                value={form.usd_price}
                onChange={(e) => setForm({ ...form, usd_price: e.target.value })}
                placeholder="مثلاً 2"
              />
            </label>
            <label>
              نرخ دلار امروز (تومان) — اختیاری
              <input
                dir="ltr"
                inputMode="numeric"
                value={form.usd_rate}
                onChange={(e) => setForm({ ...form, usd_rate: e.target.value })}
                placeholder="نرخ روز را خودتان وارد کنید"
              />
            </label>
            <label>
              تاریخ نرخ
              <input
                dir="ltr"
                value={form.rate_date}
                onChange={(e) => setForm({ ...form, rate_date: e.target.value })}
                placeholder="2026-10-13"
              />
            </label>
            <label>
              قیمت نهایی بسته (تومان)
              <input
                dir="ltr"
                inputMode="numeric"
                value={form.price_toman}
                onChange={(e) => setForm({ ...form, price_toman: e.target.value })}
                placeholder={suggested ? `پیشنهاد: ${fa(suggested)}` : 'بدون قیمت دلاری'}
              />
            </label>
          </div>
          <p className="muted">
            {suggested
              ? `قیمت پیشنهادی از دلار و نرخ روز ساخته می‌شود: ${fa(suggested)} تومان (به بالا گرد شده). قیمت تومانی نمی‌تواند از این عدد کمتر باشد.`
              : 'اگر قیمت دلاری و نرخ روز را وارد کنید، قیمت تومانی به‌صورت خودکار پیشنهاد می‌شود؛ در غیر این صورت فقط قیمت تومانی خودتان ثبت می‌شود.'}{' '}
            نرخ دلار را خودتان وارد می‌کنید؛ برنامه نرخ زنده نمی‌سازد.
          </p>
          <button className="button primary" type="submit">
            <Save size={17} /> ذخیرهٔ تنظیمات فروش
          </button>
        </fieldset>
      </form>

      <div className="sales-actions">
        <div className="sales-block">
          <h3>
            <KeyRound size={18} /> ساخت کد فعال‌سازی پس از واریز
          </h3>
          <div className="reference-form-grid">
            <label>
              تعداد تحلیل کد
              <input
                dir="ltr"
                inputMode="numeric"
                value={form.analyses}
                onChange={(e) => setForm({ ...form, analyses: e.target.value })}
              />
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
            ساخت کد فعال‌سازی
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
            <Gift size={18} /> هدیه یا تسویهٔ این دستگاه
          </h3>
          <p className="muted">
            اگر مشتری را همین‌جا تسویه کرده‌اید یا می‌خواهید هدیه بدهید، مستقیم به همین دستگاه تحلیل
            اضافه کنید.
          </p>
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
          <button className="button ghost" disabled={busy} onClick={() => void load()}>
            <RefreshCw size={16} /> به‌روزرسانی وضعیت
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
      <p className="muted">{quota?.notice}</p>
    </section>
  )
}
