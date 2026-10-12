import { useEffect, useState } from 'react'
import { DollarSign, Save } from 'lucide-react'
import { api, errorMessage, persianDate, today } from '../api'
import type { AppContext } from '../types'
import type { DollarPricing } from '../fieldwork'
import { InfoBanner, Spinner } from './ui'

export default function PricingAdmin({
  ctx,
  allowed,
  reload,
}: {
  ctx: AppContext
  allowed: boolean
  reload: () => Promise<void>
}) {
  const [rate, setRate] = useState(''),
    [date, setDate] = useState(today()),
    [source, setSource] = useState(''),
    [url, setUrl] = useState('')
  const [prices, setPrices] = useState<Record<string, string>>({ trial: '', season: '', large: '' })
  const [requested, setRequested] = useState(false),
    [confirmed, setConfirmed] = useState(false),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState<DollarPricing | null>(null)
  useEffect(() => {
    let active = true
    if (!allowed) return
    void api<DollarPricing>('/billing/admin/pricing')
      .then((p) => {
        if (!active) return
        setSaved(p)
        setRate(p.rate_toman_per_usd ?? '')
        setDate(p.rate_date ?? p.today ?? today())
        setSource(p.source ?? '')
        setUrl(p.source_url ?? '')
        setRequested(p.receiving_requested ?? false)
        setConfirmed(p.confirmed ?? false)
        setPrices({
          trial: p.usd_prices?.trial ?? '',
          season: p.usd_prices?.season ?? '',
          large: p.usd_prices?.large ?? '',
        })
      })
      .catch((e) => {
        if (active) setError(errorMessage(e))
      })
    return () => {
      active = false
    }
  }, [allowed])
  function changed() {
    setConfirmed(false)
  }
  async function save() {
    setBusy(true)
    setError('')
    try {
      const p = await api<DollarPricing>('/billing/admin/pricing', {
        method: 'PUT',
        body: JSON.stringify({
          receiving_requested: requested,
          confirmed,
          rate_toman_per_usd: rate.trim() || null,
          rate_date: date || null,
          source,
          source_url: url,
          usd_prices: Object.fromEntries(Object.entries(prices).filter(([, v]) => v.trim())),
        }),
      })
      setSaved(p)
      await reload()
      ctx.notify(
        'تنظیمات قیمت ذخیره شد؛ دریافت وجه فقط با تکمیل همه کنترل‌ها فعال می‌شود.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <section className="reference-card admin-pricing">
      <h2>
        <DollarSign size={22} /> قیمت‌گذاری بر مبنای دلار روز
      </h2>
      <InfoBanner tone="warning">
        فید خودکار نرخ دلار متصل نیست. نرخ واقعیِ تومان برای هر دلار، تاریخ امروز تهران و منبع را
        مدیر ثبت و تأیید می‌کند. مبالغ دلاری بدون تصمیم مالک حدس زده نمی‌شوند. قیمت هر رسید با همان
        پیشنهاد قیمت ذخیره می‌شود و با تغییر نرخ بعدی عوض نمی‌شود.
      </InfoBanner>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          void save()
        }}
      >
        <fieldset disabled={!allowed || busy}>
          <div className="reference-form-grid">
            <label>
              نرخ دلار — تومان، نه ریال
              <input
                value={rate}
                onChange={(e) => {
                  setRate(e.target.value)
                  changed()
                }}
                type="number"
                min="0.01"
                step="0.01"
                dir="ltr"
                placeholder="نرخ تأییدشده امروز"
              />
            </label>
            <label>
              تاریخ نرخ
              <input
                type="date"
                value={date}
                onChange={(e) => {
                  setDate(e.target.value)
                  changed()
                }}
              />
            </label>
            <label>
              منبع و نوع نرخ
              <input
                value={source}
                maxLength={160}
                onChange={(e) => {
                  setSource(e.target.value)
                  changed()
                }}
                placeholder="مرجع واقعی و نوع نرخ خرید/فروش"
              />
            </label>
            <label>
              پیوند منبع (اختیاری)
              <input
                value={url}
                type="url"
                dir="ltr"
                maxLength={500}
                placeholder="https://…"
                onChange={(e) => {
                  setUrl(e.target.value)
                  changed()
                }}
              />
            </label>
            {(
              [
                ['trial', 'بسته ۱۰ تحلیل'],
                ['season', 'بسته ۴۰ تحلیل'],
                ['large', 'بسته ۱۲۰ تحلیل'],
              ] as const
            ).map(([id, label]) => (
              <label key={id}>
                {label} — USD
                <input
                  value={prices[id]}
                  type="number"
                  min="0.01"
                  max="1000"
                  step="0.01"
                  dir="ltr"
                  placeholder="مبلغ دلاری مورد تأیید مالک"
                  onChange={(e) => {
                    setPrices((p) => ({ ...p, [id]: e.target.value }))
                    changed()
                  }}
                />
              </label>
            ))}
          </div>
          <label className="consent-check">
            <input
              type="checkbox"
              checked={requested}
              onChange={(e) => setRequested(e.target.checked)}
            />
            <span>دریافت وجه را پس از تکمیل مقصد، آمادگی مدل و قیمت معتبر درخواست می‌کنم.</span>
          </label>
          <label className="consent-check">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
            />
            <span>
              هر سه مبلغ دلاری و نرخ امروز را از منبع واقعی کنترل کرده‌ام و گرد کردن رو به بالا تا
              هزار تومان را تأیید می‌کنم.
            </span>
          </label>
          <button className="button primary" type="submit">
            {busy ? (
              <Spinner />
            ) : (
              <>
                <Save size={18} /> ذخیره قیمت و درخواست دریافت وجه
              </>
            )}
          </button>
        </fieldset>
      </form>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {saved && (
        <p className="section-description">
          وضعیت نرخ: {saved.ready ? 'کامل و مربوط به امروز' : 'ناقص، تأییدنشده یا قدیمی'}
          {saved.rate_date && ` · ${persianDate(saved.rate_date)}`}؛ ثبت درخواست به‌تنهایی دریافت
          وجه را روشن نمی‌کند.
        </p>
      )}
    </section>
  )
}
