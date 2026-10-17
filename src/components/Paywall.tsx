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
  const card = quota.card
  const price = quota.price_toman
  const needsPrice = quota.needs_price
  const plans = quota.plans ?? []

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

      {plans.length > 0 ? (
        <div className="paywall-plans" aria-label="بسته‌های تحلیل">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={plan.discount_percent ? 'paywall-plan discounted' : 'paywall-plan'}
            >
              {plan.discount_percent > 0 && <span>{fa(plan.discount_percent)}٪ تخفیف</span>}
              <strong>{plan.name}</strong>
              <b>
                {fa(plan.price_toman)} <small>تومان</small>
              </b>
              <small>{fa(plan.per_analysis_toman)} تومان هر تحلیل</small>
            </div>
          ))}
          <p className="muted">
            هر تحلیل {fa(quota.base_toman)} تومان است؛ بسته‌های بزرگ‌تر تا ۳۰٪ ارزان‌تر می‌شوند.
          </p>
        </div>
      ) : (
        <div className="paywall-price">
          <ShoppingBag size={22} />
          <div>
            <strong>
              {needsPrice
                ? `${fa(quota.analyses_per_package)} تحلیل — قیمت را مالک در پنل تعیین می‌کند`
                : `${fa(quota.analyses_per_package)} تحلیل — ${fa(price)} تومان`}
            </strong>
          </div>
        </div>
      )}

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

      <button className="button primary" onClick={() => ctx.navigate('subscription')}>
        <Send size={17} /> انتخاب بسته و ارسال عکس فیش
      </button>

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
