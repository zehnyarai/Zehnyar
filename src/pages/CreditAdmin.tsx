import { useEffect, useState } from 'react'
import { CreditCard, Image, LockKeyhole, Save, ShieldCheck, Users } from 'lucide-react'
import type { AppContext } from '../types'
import type { BillingConfig, CreditReceipt } from '../fieldwork'
import { EMPTY_BILLING } from '../fieldwork'
import { api, errorMessage, fa, persianDate } from '../api'
import { IS_STANDALONE } from '../config'
import { Badge, InfoBanner, Modal, Spinner } from '../components/ui'
import { receiptLabels } from './Credits'
import PricingAdmin from '../components/PricingAdmin'
import VisionActivation from '../components/VisionActivation'
import LocalAdminPanel from '../components/LocalAdminPanel'

interface BillingAdmin {
  config: BillingConfig
  receipts: (CreditReceipt & { user_name: string })[]
  accounts: {
    id: string
    name: string
    email: string
    balance: number
    purchased: number
    used: number
  }[]
}
export default function CreditAdmin({ ctx }: { ctx: AppContext }) {
  // The offline edition gets a real panel instead of a disabled server form.
  if (IS_STANDALONE) return <LocalAdminPanel ctx={ctx} />
  const allowed = ctx.data.user?.role === 'admin'
  const [data, setData] = useState<BillingAdmin>({
      config: EMPTY_BILLING,
      receipts: [],
      accounts: [],
    }),
    [card, setCard] = useState(''),
    [holder, setHolder] = useState(''),
    [bank, setBank] = useState(''),
    [status, setStatus] = useState('pending'),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false)
  const [review, setReview] = useState<(CreditReceipt & { user_name: string }) | null>(null),
    [confirmed, setConfirmed] = useState(false),
    [reason, setReason] = useState('')
  async function load() {
    const result = await api<BillingAdmin>('/billing/admin')
    setData(result)
    setCard(result.config.card_number)
    setHolder(result.config.holder)
    setBank(result.config.bank)
  }
  useEffect(() => {
    if (!allowed) return
    let active = true
    setLoading(true)
    void api<BillingAdmin>('/billing/admin')
      .then((result) => {
        if (active) {
          setData(result)
          setCard(result.config.card_number)
          setHolder(result.config.holder)
          setBank(result.config.bank)
        }
      })
      .catch((e) => {
        if (active) setError(errorMessage(e))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [allowed])
  async function saveBank() {
    setBusy(true)
    setError('')
    try {
      await api('/billing/admin/bank', {
        method: 'PUT',
        body: JSON.stringify({ card_number: card.replace(/[\s-]/g, ''), holder, bank }),
      })
      await load()
      ctx.notify(
        'اطلاعات حساب مقصد ذخیره شد؛ این کار به‌تنهایی دریافت وجه را فعال نمی‌کند.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  async function decide(decision: 'approved' | 'rejected') {
    if (!review) return
    setBusy(true)
    setError('')
    try {
      await api(`/billing/admin/receipts/${review.id}/review`, {
        method: 'POST',
        body: JSON.stringify({ status: decision, reason }),
      })
      await load()
      setReview(null)
      ctx.notify(
        decision === 'approved'
          ? 'رسید با تأیید مدیر ثبت شد؛ اعتبار یک بار اضافه شد.'
          : 'درخواست رد شد؛ اعتباری اضافه نشد.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <div className="reference-page credit-admin-page" inert={!!review}>
        <div className="reference-heading">
          <span className="feature-icon green">
            <ShieldCheck size={29} />
          </span>
          <div>
            <h1>پنل مدیر</h1>
            <p>بررسی رسیدهای واریز و تخصیص اعتبار به کاربران</p>
          </div>
        </div>
        {!allowed && (
          <InfoBanner tone="warning">
            <LockKeyhole size={18} />
            <strong>این بخش فقط برای مدیر احراز هویت‌شده است.</strong>{' '}
            {IS_STANDALONE
              ? 'در نسخه مستقل، مدیریت کاربران و تأیید واریز سروری فعال نیست؛ فرم‌ها فقط ساختار پنل را نشان می‌دهند.'
              : 'برای تغییر اطلاعات بانکی یا بررسی رسیدها با حساب مدیر وارد شوید.'}
            {!IS_STANDALONE && (
              <button className="text-button" onClick={ctx.openAuth}>
                ورود مدیر
              </button>
            )}
          </InfoBanner>
        )}
        <section className="reference-card admin-bank">
          <h2>
            <CreditCard size={22} />
            شماره کارت بانکی شما
          </h2>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              void saveBank()
            }}
          >
            <fieldset disabled={!allowed || busy}>
              <div className="bank-fields">
                <label>
                  شماره کارت ۱۶ رقمی *
                  <input
                    dir="ltr"
                    value={card}
                    inputMode="numeric"
                    minLength={16}
                    maxLength={19}
                    placeholder="بدون شماره کارت نمونه"
                    onChange={(e) => setCard(e.target.value)}
                    required
                  />
                </label>
                <label>
                  نام صاحب کارت
                  <input
                    value={holder}
                    maxLength={100}
                    placeholder="نام مالک حساب مقصد"
                    onChange={(e) => setHolder(e.target.value)}
                  />
                </label>
                <label>
                  نام بانک
                  <input
                    value={bank}
                    maxLength={80}
                    placeholder="بانک مقصد"
                    onChange={(e) => setBank(e.target.value)}
                  />
                </label>
              </div>
              <div className="end-actions">
                <button className="button primary" type="submit">
                  {busy ? (
                    <Spinner />
                  ) : (
                    <>
                      <Save size={18} />
                      ذخیره اطلاعات کارت
                    </>
                  )}
                </button>
              </div>
            </fieldset>
          </form>
          <p className="section-description">
            اطلاعات بانکی تصویر مرجع کپی نشده‌اند. دریافت وجه فقط با فعال‌سازی صریح مالک روی سرور و
            اتصال مدل فعال می‌شود؛ شماره کارت را قبل از نمایش عمومی کنترل کنید.
          </p>
        </section>
        <VisionActivation ctx={ctx} allowed={allowed} />
        <PricingAdmin ctx={ctx} allowed={allowed} reload={load} />
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        {loading && <Spinner />}
        <section className="reference-card admin-receipts">
          <header>
            <h2>
              <CreditCard size={22} />
              رسیدهای واریز کاربران
            </h2>
            <div className="category-filters">
              {[
                ['pending', 'در انتظار'],
                ['approved', 'تأییدشده'],
                ['rejected', 'ردشده'],
                ['all', 'همه'],
              ].map(([value, label]) => (
                <button
                  key={value}
                  className={status === value ? 'active' : ''}
                  onClick={() => setStatus(value)}
                >
                  {label}
                </button>
              ))}
            </div>
          </header>
          {!data.receipts.filter((r) => status === 'all' || r.status === status).length ? (
            <p className="empty-inline">در این بخش درخواستی وجود ندارد.</p>
          ) : (
            data.receipts
              .filter((r) => status === 'all' || r.status === status)
              .map((r) => (
                <div className="admin-receipt-row" key={r.id}>
                  <span>
                    <strong>
                      {r.name} · {r.user_name}
                    </strong>
                    <small>
                      {persianDate(r.created_at)} · پیگیری: {r.tracking}
                    </small>
                  </span>
                  <Badge
                    tone={
                      r.status === 'approved' ? 'green' : r.status === 'pending' ? 'amber' : 'red'
                    }
                  >
                    {receiptLabels[r.status]}
                  </Badge>
                  <button
                    className="button secondary small"
                    onClick={() => {
                      setReview(r)
                      setConfirmed(false)
                      setReason(r.reason)
                    }}
                  >
                    <Image size={16} />
                    بررسی رسید
                  </button>
                </div>
              ))
          )}
        </section>
        <section className="reference-card admin-credits">
          <h2>
            <Users size={23} />
            اعتبار کاربران
          </h2>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>کاربر</th>
                  <th>موجودی</th>
                  <th>خریداری‌شده</th>
                  <th>مصرف‌شده</th>
                </tr>
              </thead>
              <tbody>
                {data.accounts.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <strong>{u.name}</strong>
                      <small>{u.email}</small>
                    </td>
                    <td className="positive">{fa(u.balance)}</td>
                    <td>{fa(u.purchased)}</td>
                    <td>{fa(u.used)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!data.accounts.length && (
              <p className="empty-inline">
                اطلاعات کاربران واقعی فقط برای مدیر سروری نمایش داده می‌شود.
              </p>
            )}
          </div>
        </section>
      </div>
      {review && (
        <Modal
          title="بررسی رسید واریز"
          subtitle={`${review.name} · ${receiptLabels[review.status]}`}
          onClose={() => {
            if (!busy) setReview(null)
          }}
          wide
        >
          <img
            className="admin-receipt-image"
            src={review.image_url}
            alt="تصویر رسید خصوصی برای بررسی مدیر"
          />
          <p>
            کد پیگیری: {review.tracking} · بسته:{' '}
            {data.config.packages.find((p) => p.id === review.package_id)?.name ??
              review.package_id}
          </p>
          {review.price_toman !== undefined && (
            <p>
              مبلغ ثابت این رسید: <strong>{fa(review.price_toman)} تومان</strong> ·{' '}
              {fa(review.analyses ?? 0)} تحلیل
            </p>
          )}
          {review.price_snapshot?.mode === 'usd' && (
            <InfoBanner>
              پیشنهاد ثبت‌شده: {fa(Number(review.price_snapshot.price_usd), 2)} دلار × نرخ{' '}
              {fa(Number(review.price_snapshot.rate_toman_per_usd))} تومان · تاریخ:{' '}
              {review.price_snapshot.rate_date} · منبع: {review.price_snapshot.source}. مبلغ را با
              واریز واقعی تطبیق دهید؛ نرخ امروز روی این رسید اعمال نمی‌شود.
            </InfoBanner>
          )}
          {review.status !== 'pending' && review.reason && <p>یادداشت بررسی: {review.reason}</p>}
          {review.status === 'pending' && (
            <>
              <label className="full-label">
                یادداشت بررسی
                <textarea
                  value={reason}
                  maxLength={300}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
              <label className="consent-check">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                <span>
                  ورود مبلغ و کد پیگیری را در حساب بانکی واقعی با بسته انتخاب‌شده تطبیق داده‌ام؛ صرف
                  تصویر رسید کافی نیست.
                </span>
              </label>
              {error && (
                <div className="form-error" role="alert">
                  {error}
                </div>
              )}
              <div className="modal-actions">
                <button
                  className="button primary"
                  disabled={!confirmed || busy}
                  onClick={() => void decide('approved')}
                >
                  تأیید و تخصیص اعتبار
                </button>
                <button
                  className="button danger"
                  disabled={busy || !reason.trim()}
                  onClick={() => void decide('rejected')}
                >
                  رد درخواست با دلیل
                </button>
              </div>
            </>
          )}
        </Modal>
      )}
    </>
  )
}
