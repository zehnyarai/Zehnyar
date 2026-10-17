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
import { api, errorMessage, fa, persianDate, today } from '../api'
import type { AppContext } from '../types'
import type { QuotaPayload } from '../quota'
import { Spinner } from '../components/ui'
import type { LocalReceipt } from '../localAdmin'
import { normaliseDigits } from '../quota'
import { prepareReceiptImage } from '../receiptTransfer'
import { shareReceiptFile, saveTextFile } from '../files'

const digits = (value: string) => normaliseDigits(value).replace(/\D/g, '')
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
  const [receipt, setReceipt] = useState({
    payer: '',
    amount_toman: '',
    reference: '',
    paid_at: today(),
  })
  const [showReceipt, setShowReceipt] = useState(false)
  const [image, setImage] = useState('')
  const [reading, setReading] = useState(false)
  const [mine, setMine] = useState<LocalReceipt[]>([])
  const [selectedPlan, setSelectedPlan] = useState('single')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState('')
  const [copied, setCopied] = useState(false)
  async function loadMine() {
    setMine(await api<LocalReceipt[]>('/local/billing/receipts/mine'))
  }
  useEffect(() => {
    void loadMine().catch((e) => setError(errorMessage(e)))
  }, [])
  async function exportReceipt(row: LocalReceipt, save = false) {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      const packet = await api<{ content: string }>(`/local/billing/receipts/${row.id}/export`)
      const name = `pestino-receipt-${row.id}.json`
      const result = save
        ? (await saveTextFile(name, packet.content))
          ? 'saved'
          : 'cancelled'
        : await shareReceiptFile(name, packet.content)
      if (result !== 'cancelled')
        setDone(
          result === 'saved'
            ? 'فایل فیش ذخیره شد؛ آن را با پیام‌رسان برای مدیر بفرستید. هنوز رسیدن آن تأیید نشده است.'
            : 'در پنجرهٔ اشتراک‌گذاری، گفت‌وگوی مدیر را انتخاب و فایل را ارسال کنید؛ برنامه رسیدن آن را تأیید نمی‌کند.'
        )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

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
    if (busy || reading || !image) return
    setBusy(true)
    setError('')
    try {
      await api('/local/billing/receipts', {
        method: 'POST',
        body: JSON.stringify({
          payer: receipt.payer,
          amount_toman: Number(digits(receipt.amount_toman)),
          paid_at: receipt.paid_at,
          reference: normaliseDigits(receipt.reference).trim(),
          image_data: image,
          note: `بستهٔ درخواستی: ${quota?.plans.find((p) => p.id === selectedPlan)?.name ?? ''}`,
        }),
      })
      const message =
        'فیش فقط روی این گوشی ذخیره شد؛ حالا «ارسال فایل فیش» را بزنید. پس از بررسی، کد اعتبار را از مدیر بگیرید.'
      setDone(message)
      ctx.notify(message, 'success')
      setReceipt({ payer: '', amount_toman: '', reference: '', paid_at: today() })
      setShowReceipt(false)
      setImage('')
      await loadMine()
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
              <button
                className={
                  selectedPlan === p.id ? 'button primary small' : 'button secondary small'
                }
                aria-pressed={selectedPlan === p.id}
                onClick={() => {
                  setSelectedPlan(p.id)
                  setReceipt((r) => ({ ...r, amount_toman: String(p.price_toman) }))
                  setShowReceipt(true)
                }}
              >
                {selectedPlan === p.id ? 'بستهٔ انتخاب‌شده' : 'انتخاب بسته'}
              </button>
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
          ۱. بسته را انتخاب و مبلغ همان بسته را واریز کنید. ۲. عکس فیش و کد پیگیری را ثبت و فایلش را
          برای مدیر بفرستید. ۳. کد تأیید مدیر را در این صفحه وارد کنید. این برنامه درگاه بانکی
          ندارد؛ صندوق آنلاین هم در این نسخه وجود ندارد.
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
        <button
          className="text-button"
          onClick={() => {
            setShowReceipt(!showReceipt)
            if (!receipt.amount_toman)
              setReceipt((r) => ({
                ...r,
                amount_toman: String(quota?.plans[0]?.price_toman ?? 350000),
              }))
          }}
        >
          <Send size={15} /> {showReceipt ? 'بستن فرم رسید' : 'واریز کرده‌ام؛ رسید را ثبت کن'}
        </button>
        {showReceipt && (
          <div className="receipt-form">
            <h3>عکس فیش واریزی</h3>
            <label className="receipt-upload">
              {reading
                ? 'در حال آماده‌کردن عکس…'
                : image
                  ? 'تغییر عکس فیش'
                  : 'انتخاب عکس فیش (JPG، PNG یا WebP)'}
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                disabled={reading || busy}
                aria-label="عکس فیش واریزی"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  e.target.value = ''
                  if (!file) return
                  setReading(true)
                  setError('')
                  setImage('')
                  void prepareReceiptImage(file)
                    .then(setImage)
                    .catch((e) => setError(errorMessage(e)))
                    .finally(() => setReading(false))
                }}
              />
            </label>
            {image && <img className="receipt-image" src={image} alt="پیش‌نمایش فیش واریزی" />}
            <p className="muted">
              فیش و مشخصات پرداخت فقط با ارسال فایل از گوشی خارج می‌شود. اطلاعات غیرضروری حساب خود
              را پیش از انتخاب عکس بپوشانید.
            </p>
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
                تاریخ واریز
                <input
                  type="date"
                  dir="ltr"
                  value={receipt.paid_at}
                  onChange={(e) => setReceipt({ ...receipt, paid_at: e.target.value })}
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
              disabled={
                busy ||
                reading ||
                !image ||
                !receipt.payer.trim() ||
                digits(receipt.amount_toman).length < 4 ||
                receipt.reference.trim().length < 4
              }
              onClick={() => void submitReceipt()}
            >
              <Send size={16} /> ذخیره فیش و آماده‌سازی ارسال
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

      <details className="reference-card quiet-details" open={mine.length > 0}>
        <summary>فیش‌های من ({fa(mine.length)})</summary>
        {!mine.length && <p className="muted">هنوز فیشی روی این گوشی ثبت نکرده‌اید.</p>}
        {mine.map((row) => (
          <article className="receipt-row" key={row.id}>
            <div>
              <strong>
                {row.payer} · {fa(row.amount_toman)} تومان
              </strong>
              <p>
                پیگیری: <bdi>{row.reference}</bdi>
              </p>
              <small>ثبت محلی؛ وضعیت دریافت مدیر از این گوشی قابل پیگیری نیست.</small>
            </div>
            <div className="local-settings-actions">
              <button
                className="button primary small"
                disabled={busy || !row.image_data}
                onClick={() => void exportReceipt(row)}
              >
                <Send size={16} /> ارسال فایل فیش
              </button>
              <button
                className="button secondary small"
                disabled={busy || !row.image_data}
                onClick={() => void exportReceipt(row, true)}
              >
                ذخیره فایل
              </button>
            </div>
          </article>
        ))}
      </details>
      <button className="button secondary admin-link" onClick={() => ctx.navigate('admin')}>
        <ShieldCheck size={18} /> پنل مدیر
      </button>
    </div>
  )
}
