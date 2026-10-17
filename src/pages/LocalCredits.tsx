import { useEffect, useState } from 'react'
import {
  BadgeCheck,
  Check,
  Copy,
  CreditCard,
  KeyRound,
  Send,
  ShieldCheck,
  Wallet,
} from 'lucide-react'
import { api, errorMessage, fa, persianDate } from '../api'
import type { AppContext } from '../types'
import type { QuotaPayload } from '../quota'
import { Spinner } from '../components/ui'

const digits = (value: string) => value.replace(/\D/g, '')
const grouped = (value: string) =>
  digits(value)
    .slice(0, 16)
    .replace(/(.{4})/g, '$1 ')
    .trim()

/**
 * «اعتبار من» in the offline edition: the real counter the analysis guard uses, the four
 * support packages priced from the owner's day rate, the destination card, and the two
 * honest ways to unlock more analyses (activation code or a receipt the owner confirms).
 */
export default function LocalCredits({ ctx }: { ctx: AppContext }) {
  const [quota, setQuota] = useState<QuotaPayload | null>(null)
  const [code, setCode] = useState('')
  const [receipt, setReceipt] = useState({ payer: '', amount_toman: '', reference: '' })
  const [showReceipt, setShowReceipt] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState('')
  const [copied, setCopied] = useState(false)

  async function load() {
    try {
      setQuota(await api<QuotaPayload>('/local/quota'))
    } catch (e) {
      setError(errorMessage(e))
    }
  }
  useEffect(() => {
    let active = true
    void api<QuotaPayload>('/local/quota')
      .then((payload) => active && setQuota(payload))
      .catch((e) => active && setError(errorMessage(e)))
    return () => {
      active = false
    }
  }, [])

  async function redeem() {
    if (busy || !code.trim()) return
    setBusy(true)
    setError('')
    try {
      const answer = await api<{ added: number; expires_on: string | null }>(
        '/local/quota/redeem',
        { method: 'POST', body: JSON.stringify({ code }) }
      )
      const message = answer.expires_on
        ? `${fa(answer.added)} تحلیل اضافه شد؛ اعتبار کد تا ${persianDate(answer.expires_on)}.`
        : `${fa(answer.added)} تحلیل اضافه شد.`
      setDone(message)
      ctx.notify(message, 'success')
      setCode('')
      await ctx.refresh()
      await load()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function submitReceipt() {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await api('/local/billing/receipts', {
        method: 'POST',
        body: JSON.stringify({
          payer: receipt.payer,
          amount_toman: Number(digits(receipt.amount_toman)),
          paid_at: new Date().toISOString().slice(0, 10),
          reference: receipt.reference,
          note: 'ثبت از صفحه اعتبار',
        }),
      })
      const message = 'رسید ثبت شد؛ پس از تأیید واریز توسط مدیر، تحلیل‌ها آزاد می‌شود.'
      setDone(message)
      ctx.notify(message, 'success')
      setReceipt({ payer: '', amount_toman: '', reference: '' })
      setShowReceipt(false)
      await ctx.refresh()
      await load()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  const card = quota?.card
  return (
    <div className="reference-page local-credits">
      <section className="credit-balance">
        <span className="wallet-block">
          <Wallet size={26} />
        </span>
        <div>
          <h1>اعتبار من</h1>
          <strong>
            {fa(quota?.total_left ?? 0)} <small>تحلیل</small>
          </strong>
        </div>
        <div className="credit-counters">
          <span>
            رایگان<strong>{fa(quota?.free_left ?? 0)}</strong>
          </span>
          <span>
            خریداری‌شده<strong>{fa(quota?.credits ?? 0)}</strong>
          </span>
        </div>
      </section>
      <p className="quota-line">
        {quota?.blocked
          ? 'دو تحلیل رایگان تمام شد؛ برای ادامه یکی از بسته‌های زیر را تهیه کنید.'
          : `از ${fa(quota?.free_limit ?? 2)} تحلیل رایگان، ${fa(quota?.free_left ?? 0)} باقی مانده است.`}{' '}
        باغ، پرونده، عکس، دانشنامه و تقویم بدون محدودیت کار می‌کنند.
      </p>

      <section className="reference-card plans-card" aria-label="بسته‌های حمایتی">
        <h2>
          <CreditCard size={21} /> بسته‌های تحلیل
        </h2>
        <div className="plan-grid">
          {(quota?.plans ?? []).map((p) => (
            <article
              key={p.id}
              className={p.discount_percent ? 'plan-card discounted' : 'plan-card'}
            >
              {p.discount_percent > 0 && (
                <span className="plan-discount">{fa(p.discount_percent)}٪ تخفیف</span>
              )}
              <strong>{p.name}</strong>
              <b>
                {fa(p.price_toman)} <small>تومان</small>
              </b>
              <span className="plan-per">{fa(p.per_analysis_toman)} تومان هر تحلیل</span>
              <p>{p.note}</p>
            </article>
          ))}
        </div>
        <p className="muted">
          هر تحلیل {fa(quota?.base_toman ?? 0)} تومان است؛ بسته‌های بزرگ‌تر تا ۳۰٪ ارزان‌تر می‌شوند.
        </p>
      </section>

      <section className="reference-card transfer-card" aria-label="کارت واریز">
        <h2>
          <CreditCard size={21} /> کارت واریز
        </h2>
        {card ? (
          <div className="bank-card-display">
            <div>
              <strong dir="ltr">{grouped(card.card_number)}</strong>
              <p>به نام: {card.holder}</p>
              {card.bank && <p>بانک: {card.bank}</p>}
            </div>
            <button
              className="button secondary small"
              onClick={() =>
                void navigator.clipboard
                  .writeText(digits(card.card_number))
                  .then(() => {
                    setCopied(true)
                    ctx.notify('شماره کارت کپی شد.')
                  })
                  .catch(() => ctx.notify('کپی ممکن نشد؛ شماره را از همین صفحه بخوانید.'))
              }
            >
              {copied ? <Check size={16} /> : <Copy size={16} />}
              {copied ? 'کپی شد' : 'کپی'}
            </button>
          </div>
        ) : (
          <p className="muted">کارت مقصد در پنل مدیر ثبت نشده است؛ تا آن زمان واریز نکنید.</p>
        )}
        <p className="muted">
          پس از واریز، کد پیگیری را برای مدیر بفرستید تا کد فعال‌سازی بگیرید. این برنامه درگاه بانکی
          ندارد.
        </p>
      </section>

      <section className="reference-card" aria-label="فعال‌سازی کد">
        <h2>
          <KeyRound size={21} /> کد فعال‌سازی دارم
        </h2>
        <div className="code-row">
          <input
            dir="ltr"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="PST-…"
            spellCheck={false}
            disabled={busy}
            aria-label="کد فعال‌سازی"
          />
          <button
            className="button primary"
            disabled={busy || !code.trim()}
            onClick={() => void redeem()}
          >
            {busy ? <Spinner /> : <KeyRound size={17} />}
            فعال‌سازی
          </button>
        </div>
        <button className="text-button" onClick={() => setShowReceipt(!showReceipt)}>
          <Send size={15} /> {showReceipt ? 'بستن فرم رسید' : 'واریز کرده‌ام؛ رسید را ثبت کن'}
        </button>
        {showReceipt && (
          <div className="receipt-form">
            <div className="reference-form-grid">
              <label>
                نام پرداخت‌کننده
                <input
                  value={receipt.payer}
                  onChange={(e) => setReceipt({ ...receipt, payer: e.target.value })}
                  maxLength={80}
                />
              </label>
              <label>
                مبلغ (تومان)
                <input
                  dir="ltr"
                  inputMode="numeric"
                  value={receipt.amount_toman}
                  onChange={(e) => setReceipt({ ...receipt, amount_toman: e.target.value })}
                />
              </label>
              <label>
                کد پیگیری
                <input
                  dir="ltr"
                  value={receipt.reference}
                  onChange={(e) => setReceipt({ ...receipt, reference: e.target.value })}
                  maxLength={60}
                />
              </label>
            </div>
            <button
              className="button secondary"
              disabled={busy || !receipt.payer.trim() || digits(receipt.amount_toman).length < 4}
              onClick={() => void submitReceipt()}
            >
              <Send size={16} /> ثبت رسید برای تأیید مدیر
            </button>
          </div>
        )}
        {done && (
          <p className="paywall-done" role="status">
            <BadgeCheck size={18} /> {done}
          </p>
        )}
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
      </section>

      <button className="button secondary admin-link" onClick={() => ctx.navigate('admin')}>
        <ShieldCheck size={18} /> پنل مدیر
      </button>
    </div>
  )
}
