import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  Check,
  CreditCard,
  FileText,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
  Wallet,
} from 'lucide-react'
import type { AppContext, Payment, Plan } from '../types'
import { api, errorMessage, fa, persianDate } from '../api'
import { Badge, EmptyState, InfoBanner, PageTitle, Spinner } from '../components/ui'

export function PaymentBadge({ status }: { status: string }) {
  const labels: Record<string, string> = {
    paid: 'موفق',
    pending: 'در انتظار تأیید',
    verifying: 'در حال تأیید',
    failed: 'ناموفق',
    cancelled: 'لغوشده',
  }
  return (
    <Badge
      tone={
        status === 'paid' ? 'green' : ['pending', 'verifying'].includes(status) ? 'amber' : 'gray'
      }
    >
      {labels[status] ?? status}
    </Badge>
  )
}
export default function Subscription({ ctx }: { ctx: AppContext }) {
  const [payments, setPayments] = useState<Payment[]>([])
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [confirmPlan, setConfirmPlan] = useState<Plan | null>(null)
  const outcome = new URLSearchParams(location.search).get('payment')
  const verifiedReturn =
    outcome === 'success' && ctx.data.usage.premium && payments.some((p) => p.status === 'paid')
  useEffect(() => {
    let active = true
    void api<Payment[]>('/payments')
      .then((p) => {
        if (active) setPayments(p)
      })
      .catch((e) => {
        if (active && ctx.data.user) setError(errorMessage(e))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [ctx.data.user])
  async function buy(plan: Plan) {
    if (!ctx.data.services.payment_configured) {
      ctx.notify('درگاه هنوز متصل نیست؛ هیچ وجهی دریافت نمی‌شود.', 'info')
      setConfirmPlan(null)
      return
    }
    if (!ctx.data.services.vision_configured) {
      ctx.notify('تا تنظیم سرویس بررسی تصویر، فروش طرح پولی غیرفعال است.', 'info')
      setConfirmPlan(null)
      return
    }
    if (!ctx.data.user || ctx.data.user.is_demo) {
      ctx.openAuth()
      setConfirmPlan(null)
      return
    }
    setBusy(plan.id)
    setError('')
    try {
      const result = await api<{ redirect_url: string }>('/payments/request', {
        method: 'POST',
        body: JSON.stringify({ plan: plan.id }),
      })
      const target = new URL(result.redirect_url)
      if (
        target.protocol !== 'https:' ||
        !['www.zarinpal.com', 'sandbox.zarinpal.com'].includes(target.hostname)
      )
        throw new Error('آدرس درگاه معتبر نیست.')
      location.assign(target.href)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy('')
      setConfirmPlan(null)
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="یک همراه برای تمام فصل‌های باغ"
        title="اشتراک و پرداخت"
        subtitle="طرح مناسب باغت را انتخاب کن؛ پرداخت‌ها شفاف و قابل پیگیری‌اند."
        action={
          <Badge tone={ctx.data.usage.premium ? 'green' : 'gray'}>
            <Wallet size={14} />
            {ctx.data.usage.premium ? 'اشتراک حرفه‌ای' : 'طرح همراه · رایگان'}
          </Badge>
        }
      />
      {outcome && (
        <InfoBanner tone={verifiedReturn ? 'success' : 'warning'}>
          {verifiedReturn
            ? 'پرداخت ثبت‌شده شما توسط سرور درگاه تأیید شده است. اشتراک فعال است.'
            : outcome === 'success'
              ? 'از مسیر بازگشت پرداخت وارد شده‌اید. پارامتر آدرس به‌تنهایی اثبات پرداخت نیست؛ وضعیت واقعی فقط در حساب و تاریخچه تأییدشده نمایش داده می‌شود.'
              : outcome === 'pending'
                ? 'تأیید درگاه هنوز کامل نشده است؛ پیش از پرداخت دوباره، با پشتیبانی پیگیری کنید.'
                : 'پرداخت موفق ثبت نشده است. وضعیت تراکنش را در تاریخچه بررسی کنید.'}
        </InfoBanner>
      )}
      <div className="subscription-intro">
        <div className="subscription-icon">
          <SproutIcon />
        </div>
        <h2>برای باغت، هوشمندانه‌تر تصمیم بگیر.</h2>
        <p>همه طرح‌ها به دانشنامه و ابزارهای پایه مدیریت باغ دسترسی دارند.</p>
        <span>
          <LockKeyhole size={13} />
          کلیدهای سرویس هرگز داخل اپ قرار نمی‌گیرند.
        </span>
      </div>
      <div className="plans-grid">
        {ctx.data.plans.map((plan) => (
          <section className={`plan-card ${plan.id === 'monthly' ? 'featured' : ''}`} key={plan.id}>
            {plan.id === 'monthly' && (
              <span className="popular-plan">
                <Sparkles size={13} />
                پیشنهاد برای باغداران
              </span>
            )}
            <span className="plan-name">{plan.name}</span>
            <p>
              {plan.id === 'free'
                ? 'برای شروع و آشنایی'
                : plan.id === 'monthly'
                  ? 'برای مراقبت پیوسته از باغ'
                  : 'برای یک سال همراهی'}
            </p>
            <div className="plan-price">
              <strong>{plan.price_toman ? fa(plan.price_toman) : 'رایگان'}</strong>
              {!!plan.price_toman && (
                <span>تومان / {plan.id === 'monthly' ? '۳۰ روز' : '۳۶۵ روز'}</span>
              )}
            </div>
            {plan.id === 'yearly' && <Badge tone="green">حدود ۲۰٪ به‌صرفه‌تر از خرید ماهانه</Badge>}
            <div className="plan-line" />
            <ul>
              {plan.features.map((f) => (
                <li key={f}>
                  <Check size={16} />
                  {f}
                </li>
              ))}
            </ul>
            <button
              className={`button ${plan.id === 'monthly' ? 'primary' : 'secondary'}`}
              disabled={plan.id === 'free' || !!busy}
              onClick={() => setConfirmPlan(plan)}
            >
              {busy === plan.id ? (
                <Spinner />
              ) : plan.id === 'free' ? (
                'طرح پایه رایگان'
              ) : (
                <>
                  انتخاب این طرح
                  <ArrowLeft size={15} />
                </>
              )}
            </button>
          </section>
        ))}
      </div>
      {!ctx.data.services.payment_configured ? (
        <InfoBanner tone="warning">
          <strong>درگاه پرداخت هنوز متصل نشده است.</strong> قیمت‌ها طرح اولیه محصول‌اند و تا تنظیم
          درگاه، پرداختی انجام نمی‌شود.
        </InfoBanner>
      ) : (
        ctx.data.services.payment_sandbox && (
          <InfoBanner tone="warning">
            درگاه در حالت Sandbox است. تراکنش‌های این محیط آزمایشی‌اند و نباید به‌عنوان فروش واقعی
            گزارش شوند.
          </InfoBanner>
        )
      )}
      {ctx.data.usage.premium && !!ctx.data.user?.subscription_until && (
        <InfoBanner tone="success">
          اعتبار اشتراک: تا {persianDate(ctx.data.user.subscription_until, { year: 'numeric' })}.
          سقف بررسی تصویر در هر بازه ۳۰ روزه محاسبه می‌شود.
        </InfoBanner>
      )}
      <section className="card payment-history">
        <div className="card-header">
          <div>
            <h2>تاریخچه پرداخت‌های من</h2>
            <p>فعال شدن اشتراک فقط پس از تأیید سرور درگاه</p>
          </div>
          <FileText size={20} />
        </div>
        {error && <div className="form-error">{error}</div>}
        {loading ? (
          <div className="loading-inline">
            <Spinner />
          </div>
        ) : payments.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>شناسه</th>
                  <th>طرح</th>
                  <th>مبلغ (تومان)</th>
                  <th>وضعیت</th>
                  <th>تاریخ</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td className="latin-cell">{p.id.slice(0, 10)}</td>
                    <td>
                      {p.plan === 'monthly' ? 'ماهانه' : 'سالانه'}
                      {!!p.is_sandbox && <small>Sandbox · آزمایشی</small>}
                    </td>
                    <td>{fa(p.amount_rial / 10)}</td>
                    <td>
                      <PaymentBadge status={p.status} />
                    </td>
                    <td>{persianDate(p.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={<CreditCard size={27} />}
            title="هنوز پرداختی ثبت نشده"
            text="بعد از اتصال درگاه، تراکنش‌های شما اینجا نمایش داده می‌شوند."
          />
        )}
      </section>
      <div className="billing-guarantee">
        <ShieldCheck size={18} />
        <span>
          مبالغ در پنل به تومان نمایش داده می‌شوند و درگاه، مبلغ را به ریال دریافت می‌کند. نتیجه
          بررسی تصویر، تضمین سلامت یا افزایش محصول نیست.
        </span>
      </div>
      {confirmPlan && (
        <div className="inline-confirm card">
          <div>
            <strong>انتخاب {confirmPlan.name}</strong>
            <p>
              {fa(confirmPlan.price_toman)} تومان · {fa(confirmPlan.duration_days)} روز اعتبار ·{' '}
              {ctx.data.services.payment_configured
                ? 'انتقال به درگاه امن'
                : 'درگاه در حال حاضر متصل نیست'}
            </p>
          </div>
          <button
            className="button primary"
            disabled={!!busy}
            onClick={() => {
              void buy(confirmPlan)
            }}
          >
            {busy ? (
              <Spinner />
            ) : ctx.data.services.payment_configured ? (
              'ادامه به درگاه'
            ) : (
              'بررسی وضعیت پرداخت'
            )}
          </button>
          <button
            className="button secondary"
            disabled={!!busy}
            onClick={() => setConfirmPlan(null)}
          >
            انصراف
          </button>
        </div>
      )}
    </>
  )
}
function SproutIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path
        d="M24 39V24M24 31C10 31 10 15 10 15s14-1 14 16ZM24 24C24 11 39 11 39 11s0 13-15 17"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
