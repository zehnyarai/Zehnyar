import { useState } from 'react'
import {
  BadgeCheck,
  CreditCard,
  KeyRound,
  RefreshCw,
  Send,
  ShoppingBag,
  Wallet,
} from 'lucide-react'
import { api, errorMessage, fa, persianDate } from '../api'
import { InfoBanner, Spinner } from './ui'
import type { AppContext } from '../types'
import { QuotaRequired } from '../quota'
import type { QuotaPayload } from '../quota'

const digits = (value: string) => value.replace(/\D/g, '')
const cardPattern = (value: string) =>
  value
    .slice(0, 16)
    .replace(/(.{4})/g, '$1 ')
    .trim()

/**
 * Shown when the two free analyses are used up. Payment is an honest manual card-to-card
 * transfer: the farmer pays, sends the reference, and the owner replies with an activation
 * code. Nothing here claims an automatic bank verification.
 */
export default function Paywall({
  ctx,
  quota,
  onUnlocked,
}: {
  ctx: AppContext
  quota: QuotaPayload
  onUnlocked: () => Promise<void> | void
}) {
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState('')
  const [receipt, setReceipt] = useState({ payer: '', reference: '', amount_toman: '' })
  const card = quota.card
  const price = quota.price_toman
  const needsPrice = quota.needs_price

  async function redeem() {
    if (busy || !code.trim()) return
    setBusy(true)
    setError('')
    try {
      const answer = await api<{ added: number; expires_on: string | null }>(
        '/local/quota/redeem',
        {
          method: 'POST',
          body: JSON.stringify({ code }),
        }
      )
      const message = answer.expires_on
        ? `${fa(answer.added)} تحلیل به دستگاه شما اضافه شد؛ اعتبار کد تا ${persianDate(answer.expires_on)} است.`
        : `${fa(answer.added)} تحلیل به دستگاه شما اضافه شد.`
      // The paywall disappears the moment the quota is unblocked, so the confirmation has to
      // live in the app-level toast as well as here.
      setDone(message)
      ctx.notify(message, 'success')
      setCode('')
      await ctx.refresh()
      await onUnlocked()
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
          note: 'ثبت از صفحه خرید تحلیل',
        }),
      })
      const message = 'رسید شما ثبت شد؛ پس از تأیید واریز توسط مالک، تحلیل‌ها آزاد می‌شود.'
      setDone(message)
      ctx.notify(message, 'success')
      setReceipt({ payer: '', reference: '', amount_toman: '' })
      await ctx.refresh()
      await onUnlocked()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="paywall" aria-label="خرید تحلیل">
      <header className="paywall-head">
        <span className="paywall-badge">
          <Wallet size={18} />
          دو تحلیل رایگان تمام شد
        </span>
        <h2>برای ادامه، یک بستهٔ تحلیل تهیه کنید</h2>
        <p>
          باغ، پرونده‌ها، عکس‌ها، دانشنامه و تقویم بدون هیچ محدودیتی و آفلاین کار می‌کنند؛ فقط تحلیل
          هوشمند عکس و آزمایش شمارش می‌شود.
        </p>
      </header>

      <div className="paywall-price">
        <ShoppingBag size={22} />
        <div>
          <strong>
            {needsPrice
              ? `${fa(quota.analyses_per_package)} تحلیل — قیمت را مالک در پنل تعیین می‌کند`
              : `${fa(quota.analyses_per_package)} تحلیل — ${fa(price)} تومان`}
          </strong>
          {quota.usd_price && quota.usd_rate ? (
            <small>
              پایهٔ دلاری {fa(quota.usd_price, 2)} دلار × نرخ روز {fa(quota.usd_rate)}
              {quota.rate_date ? ` (${persianDate(quota.rate_date)})` : ''} — قیمت تومانی از همین
              نرخ ساخته شده است.
            </small>
          ) : null}
        </div>
      </div>

      <div className="paywall-steps">
        <div className="paywall-card">
          <h3>
            <CreditCard size={18} /> ۱) واریز کارت‌به‌کارت
          </h3>
          {card ? (
            <>
              <p className="paywall-card-number" dir="ltr">
                {cardPattern(digits(card.card_number))}
              </p>
              <p className="muted">
                به نام {card.holder}
                {card.bank ? ` — ${card.bank}` : ''}
              </p>
            </>
          ) : (
            <p className="muted">
              کارت مقصد هنوز در پنل مدیر ثبت نشده است؛ تا آن زمان وجهی واریز نکنید و از مالک بپرسید.
            </p>
          )}
          <p className="muted">
            پس از واریز، شمارهٔ پیگیری را برای مالک بفرستید تا برای شما کد فعال‌سازی بسازد. بدون
            هماهنگی واریز نکنید.
          </p>
        </div>
        <div className="paywall-code">
          <h3>
            <KeyRound size={18} /> ۲) وارد کردن کد فعال‌سازی
          </h3>
          <label>
            کد فعال‌سازی
            <input
              dir="ltr"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="PST-…"
              spellCheck={false}
              disabled={busy}
            />
          </label>
          <button
            className="button primary"
            disabled={busy || !code.trim()}
            onClick={() => void redeem()}
          >
            {busy ? <Spinner /> : <KeyRound size={17} />}
            فعال‌سازی تحلیل
          </button>
        </div>
      </div>

      <details className="paywall-manual">
        <summary>
          <Send size={16} /> پرداخت کردم ولی کد نگرفته‌ام (ثبت رسید روی همین دستگاه)
        </summary>
        <p className="muted">
          این فرم برای وقتی است که خودِ مالک همین دستگاه را تحویل می‌گیرد؛ رسید ثبت می‌شود و پس از
          تأیید واریز در پنل مدیر، تحلیل‌ها آزاد می‌شود. تأیید خودکار بانکی وجود ندارد.
        </p>
        <div className="reference-form-grid">
          <label>
            نام پرداخت‌کننده
            <input
              value={receipt.payer}
              onChange={(e) => setReceipt({ ...receipt, payer: e.target.value })}
              maxLength={80}
              disabled={busy}
            />
          </label>
          <label>
            مبلغ (تومان)
            <input
              dir="ltr"
              value={receipt.amount_toman}
              onChange={(e) => setReceipt({ ...receipt, amount_toman: e.target.value })}
              disabled={busy}
            />
          </label>
          <label>
            کد پیگیری
            <input
              dir="ltr"
              value={receipt.reference}
              onChange={(e) => setReceipt({ ...receipt, reference: e.target.value })}
              maxLength={60}
              disabled={busy}
            />
          </label>
        </div>
        <button
          className="button secondary"
          disabled={busy || !receipt.payer.trim() || digits(receipt.amount_toman).length < 4}
          onClick={() => void submitReceipt()}
        >
          <Send size={16} /> ثبت رسید برای تأیید مالک
        </button>
      </details>

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
      <InfoBanner tone="warning">{quota.notice}</InfoBanner>
      <p className="muted">
        تحلیل باقی‌مانده: {fa(quota.total_left)} — رایگان {fa(quota.free_left)} · بستهٔ خریداری‌شده{' '}
        {fa(quota.credits)}
        <button className="text-button" onClick={() => void ctx.refresh()}>
          <RefreshCw size={14} /> به‌روزرسانی وضعیت
        </button>
      </p>
    </section>
  )
}

export function isQuotaError(error: unknown) {
  return (
    error instanceof QuotaRequired || (error as { code?: string } | null)?.code === 'QUOTA_REQUIRED'
  )
}
