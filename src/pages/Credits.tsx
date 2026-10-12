import { useEffect, useRef, useState } from 'react'
import { Copy, CreditCard, History, ShieldCheck, Upload, Wallet } from 'lucide-react'
import type { AppContext } from '../types'
import type { BillingConfig, CreditAccount } from '../fieldwork'
import { EMPTY_BILLING } from '../fieldwork'
import { api, checkImage, errorMessage, fa, persianDate } from '../api'
import { Badge, InfoBanner, Spinner } from '../components/ui'
import { IS_STANDALONE } from '../config'

export const receiptLabels = { pending: 'در انتظار تأیید', approved: 'تأییدشده', rejected: 'ردشده' }
export default function Credits({ ctx }: { ctx: AppContext }) {
  const [config, setConfig] = useState<BillingConfig>(EMPTY_BILLING),
    [account, setAccount] = useState<CreditAccount>({
      balance: 0,
      purchased: 0,
      used: 0,
      receipts: [],
      history: [],
    })
  const [selected, setSelected] = useState('season'),
    [name, setName] = useState(ctx.data.user?.is_demo ? '' : (ctx.data.user?.name ?? '')),
    [phone, setPhone] = useState(''),
    [tracking, setTracking] = useState(''),
    [receipt, setReceipt] = useState<File | null>(null),
    [preview, setPreview] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true)
  const input = useRef<HTMLInputElement>(null)
  async function reload() {
    const [c, a] = await Promise.all([
      api<BillingConfig>('/billing/config'),
      api<CreditAccount>('/billing/my'),
    ])
    setConfig(c)
    setAccount(a)
  }
  useEffect(() => {
    let active = true
    void Promise.all([api<BillingConfig>('/billing/config'), api<CreditAccount>('/billing/my')])
      .then(([c, a]) => {
        if (active) {
          setConfig(c)
          setAccount(a)
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
  }, [])
  useEffect(() => {
    const expires = config.pricing?.expires_at
    if (!expires || !config.pricing?.ready) return
    const delay = Date.parse(expires) - Date.now()
    if (!Number.isFinite(delay)) return
    const timer = window.setTimeout(
      () => {
        setConfig((c) => ({
          ...c,
          enabled: false,
          notice: 'اعتبار نرخ روز تمام شده؛ تا تأیید نرخ جدید، واریز نکنید.',
        }))
        void reload().catch((e) => setError(errorMessage(e)))
      },
      Math.max(0, delay)
    )
    return () => window.clearTimeout(timer)
  }, [config.pricing?.expires_at, config.pricing?.ready])
  useEffect(() => {
    if (!receipt) {
      setPreview('')
      return
    }
    const url = URL.createObjectURL(receipt)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [receipt])
  function select(file?: File) {
    if (!file) return
    const issue = checkImage(file)
    if (issue || file.size > 6 * 1024 * 1024) {
      setError(issue ?? 'تصویر رسید باید کمتر از ۶ مگابایت باشد.')
      return
    }
    setReceipt(file)
    setError('')
  }
  async function submit() {
    if (!config.enabled) {
      setError('دریافت وجه فعال نیست؛ واریزی انجام ندهید.')
      return
    }
    if (!receipt) {
      setError('تصویر رسید را انتخاب کنید.')
      return
    }
    setBusy(true)
    setError('')
    const body = new FormData()
    body.append('image', receipt)
    body.append('name', name)
    body.append('phone', phone)
    body.append('tracking', tracking)
    body.append('package_id', selected)
    body.append('quote_id', config.pricing?.quote_id ?? '')
    try {
      await api('/billing/receipts', { method: 'POST', body })
      await reload()
      setReceipt(null)
      setTracking('')
      ctx.notify(
        'رسید در انتظار بررسی مدیر ثبت شد؛ تا تأیید واقعی، اعتبار اضافه نمی‌شود.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="reference-page credits-page">
      <section className="credit-balance">
        <span className="wallet-block">
          <Wallet size={28} />
        </span>
        <div>
          <h1>اعتبار قابل استفاده</h1>
          <strong>
            {fa(account.balance)} <small>تحلیل</small>
          </strong>
        </div>
        <div className="credit-counters">
          <span>
            خریداری‌شده<strong>{fa(account.purchased)}</strong>
          </span>
          <span>
            مصرف‌شده<strong>{fa(account.used)}</strong>
          </span>
        </div>
        <button className="button secondary" onClick={() => ctx.navigate('admin')}>
          <ShieldCheck size={18} />
          پنل مدیر
        </button>
      </section>
      {!config.enabled && (
        <InfoBanner tone="warning">
          <strong>دریافت وجه غیرفعال است.</strong> {config.notice} ثبت باغ، آزمایش، تجربه و راهنماها
          در نسخه مستقل رایگان‌اند.
        </InfoBanner>
      )}
      {IS_STANDALONE && config.enabled && (
        <InfoBanner>
          <strong>حالت دریافت دستی (بدون درگاه بانکی):</strong> این کارت را مالک همین دستگاه ثبت
          کرده است. واریز فقط با هماهنگی خودش انجام می‌شود و تأیید آن دستی است؛ برنامه هیچ وجهی
          نمی‌گیرد و هیچ تأیید خودکاری از بانک نمی‌گیرد.
        </InfoBanner>
      )}
      {loading && <Spinner label="خواندن وضعیت اعتبار…" />}
      <section className="reference-card transfer-card">
        <h2>
          <CreditCard size={22} />
          مرحله ۱ — واریز کارت‌به‌کارت
        </h2>
        <div className="bank-card-display">
          <div>
            <strong dir="ltr">
              {config.card_number
                ? config.card_number.match(/.{1,4}/g)?.join('-')
                : 'شماره کارت تنظیم نشده'}
            </strong>
            <p>به نام: {config.holder || '—'}</p>
            <p>بانک: {config.bank || '—'}</p>
          </div>
          <button
            className="button secondary small"
            disabled={!config.enabled || !config.card_number}
            onClick={() =>
              void navigator.clipboard
                .writeText(config.card_number)
                .then(() => ctx.notify('شماره کارت کپی شد.'))
                .catch(() => ctx.notify('کپی ممکن نشد؛ شماره را از همین صفحه بخوانید.'))
            }
          >
            <Copy size={17} />
            کپی
          </button>
        </div>
        <p className="section-description">
          {IS_STANDALONE
            ? config.enabled
              ? 'مبلغ را کارت‌به‌کارت واریز کنید و کد پیگیری را برای مالک دستگاه بفرستید؛ ثبت دریافتی در پنل مدیر (دفتر دستی) انجام می‌شود.'
              : 'کارت مقصد در پنل مدیر ← «کارت مقصد واریز» ثبت می‌شود. تا آن زمان واریزی انجام ندهید.'
            : config.enabled
              ? 'پس از واریز، تصویر رسید و کد پیگیری را ارسال کنید. اعتبار فقط پس از بررسی واقعی مدیر اضافه می‌شود.'
              : 'شماره کارت نمونه یا اطلاعات بانکی شما از تصاویر کپی نشده است. تا فعال‌سازی صریح مالک، هیچ وجهی واریز نکنید.'}
        </p>
      </section>
      <section className="reference-card package-selection">
        <h2>مرحله ۲ — انتخاب بسته اعتبار</h2>
        <p className="section-description">
          {config.enabled
            ? 'بسته انتخاب‌شده باید با مبلغ واریزی شما تطبیق داشته باشد.'
            : 'قیمت‌های زیر صرفاً ساختار نمونه مطابق تصویرند؛ خرید و فروش فعال نشده است.'}
        </p>
        {config.pricing?.mode === 'usd' && (
          <InfoBanner tone="warning">
            قیمت‌ها بر مبنای دلار و نرخ ثبت‌شده مدیر محاسبه می‌شوند؛ فید خودکار دلار فعال نیست.{' '}
            {config.pricing.ready ? (
              <>
                نرخ: {fa(Number(config.pricing.rate_toman_per_usd))} تومان برای هر دلار ·{' '}
                {persianDate(config.pricing.rate_date!)} · منبع: {config.pricing.source}
              </>
            ) : (
              <>مبلغ بسته‌ها یا نرخ معتبر امروز هنوز تأیید نشده؛ واریز نکنید.</>
            )}{' '}
            گرد کردن رو به بالا تا هزار تومان است.
          </InfoBanner>
        )}
        <div className="credit-packages">
          {config.packages.map((p, i) => (
            <label className={selected === p.id ? 'selected' : ''} key={p.id}>
              <input
                type="radio"
                name="credit-package"
                value={p.id}
                checked={selected === p.id}
                onChange={() => setSelected(p.id)}
              />
              <strong>{p.name}</strong>
              {i > 0 && <span className="orange-tag">{i === 1 ? 'بسته فصلی' : 'باغ بزرگ'}</span>}
              <div>
                <b>{p.price_toman === null ? 'تعیین نشده' : fa(p.price_toman)}</b>
                <small>تومان</small>
              </div>
              <p>
                {fa(p.analyses)} تحلیل — {p.description}
              </p>
              {p.price_toman !== null && (
                <small>({fa(p.price_toman / p.analyses, 0)} تومان هر تحلیل)</small>
              )}
              {p.price_usd && (
                <small>{fa(Number(p.price_usd), 2)} دلار برای بسته؛ پرداخت به تومان</small>
              )}
            </label>
          ))}
        </div>
      </section>
      {IS_STANDALONE && (
        <section className="reference-card receipt-form-card">
          <h2>مرحله ۳ — ثبت دریافتی (دفتر دستی)</h2>
          <p className="section-description">
            در نسخه مستقل، سرور و حسابرسی وجود ندارد؛ دریافتی‌های واقعی را مالک دستگاه در «پنل مدیر
            ← دفتر دریافت» ثبت می‌کند. این ثبت، سند بانکی یا تأیید خودکار نیست.
          </p>
          <button className="button secondary" type="button" onClick={() => ctx.navigate('admin')}>
            <Wallet size={17} /> رفتن به دفتر دریافت در پنل مدیر
          </button>
        </section>
      )}
      <section className="reference-card receipt-form-card" hidden={IS_STANDALONE}>
        <h2>مرحله ۳ — ارسال رسید واریز</h2>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            void submit()
          }}
        >
          <fieldset disabled={!config.enabled || busy}>
            <div className="reference-form-grid">
              <label>
                نام واریزکننده *
                <input
                  value={name}
                  minLength={2}
                  maxLength={80}
                  required
                  onChange={(e) => setName(e.target.value)}
                />
              </label>
              <label>
                شماره تماس
                <input
                  value={phone}
                  type="tel"
                  maxLength={20}
                  placeholder="اختیاری؛ فقط برای پیگیری رسید"
                  onChange={(e) => setPhone(e.target.value)}
                />
              </label>
              <label className="span-all">
                کد پیگیری واریز *
                <input
                  value={tracking}
                  minLength={4}
                  maxLength={100}
                  required
                  placeholder="شماره پیگیری یا مرجع تراکنش"
                  onChange={(e) => setTracking(e.target.value)}
                />
              </label>
            </div>
            <label className="receipt-image-label">تصویر رسید</label>
            <button className="receipt-upload" type="button" onClick={() => input.current?.click()}>
              {preview ? (
                <>
                  <img src={preview} alt="پیش‌نمایش رسید انتخاب‌شده" />
                  <span>{receipt?.name} — تغییر تصویر</span>
                </>
              ) : (
                <>
                  <Upload size={29} />
                  <span>تصویر رسید بانکی را انتخاب کنید (حداکثر ۶ مگابایت)</span>
                  <small>JPG، PNG یا WebP؛ اطلاعات حساس اضافی را بپوشانید.</small>
                </>
              )}
            </button>
            <input
              ref={input}
              type="file"
              hidden
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => {
                select(e.target.files?.[0])
                e.target.value = ''
              }}
            />
            <button className="button primary full-width" type="submit" disabled={!receipt || busy}>
              {busy ? <Spinner /> : 'ثبت رسید و درخواست اعتبار'}
            </button>
          </fieldset>
          <p className="receipt-caption">
            پس از تأیید واقعی مدیر، اعتبار به حساب اضافه می‌شود؛ صرف تصویر رسید اثبات واریز نیست.
          </p>
        </form>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
      </section>
      <section className="reference-card receipt-status" hidden={IS_STANDALONE}>
        <h2>
          <History size={22} />
          وضعیت درخواست‌های من
        </h2>
        {!account.receipts.length ? (
          <p className="empty-inline">هنوز درخواست واریزی ثبت نکرده‌اید.</p>
        ) : (
          account.receipts.map((r) => (
            <div className="receipt-status-row" key={r.id}>
              <span>
                <strong>
                  درخواست {config.packages.find((p) => p.id === r.package_id)?.name ?? r.package_id}
                </strong>
                <small>
                  {persianDate(r.created_at)} · کد: {r.tracking}
                </small>
                {r.reason && <small className="receipt-reason">یادداشت مدیر: {r.reason}</small>}
              </span>
              <Badge
                tone={r.status === 'approved' ? 'green' : r.status === 'pending' ? 'amber' : 'red'}
              >
                {receiptLabels[r.status]}
              </Badge>
            </div>
          ))
        )}
      </section>
      <section className="reference-card credit-history" hidden={IS_STANDALONE}>
        <h2>
          <History size={22} />
          تاریخچه اعتبار
        </h2>
        {!account.history.length ? (
          <p className="empty-inline">هنوز تراکنش اعتباری ثبت نشده است.</p>
        ) : (
          account.history.map((r) => (
            <div className="credit-history-row" key={r.id}>
              <span>
                <strong>{r.reason}</strong>
                <small>{persianDate(r.created_at)}</small>
              </span>
              <b className={r.delta > 0 ? 'positive' : 'negative'}>
                {r.delta > 0 ? '+' : '−'}
                {fa(Math.abs(r.delta))}
              </b>
            </div>
          ))
        )}
      </section>
    </div>
  )
}
