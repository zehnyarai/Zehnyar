import { useEffect, useMemo, useState } from 'react'
import {
  BadgeCheck,
  Ban,
  CircleCheck,
  CreditCard,
  Database,
  ListChecks,
  RefreshCw,
  Save,
  Settings2,
  ShieldCheck,
  Trash2,
  Wallet,
} from 'lucide-react'
import { api, errorMessage, fa, persianDate, today } from '../api'
import type { AppContext } from '../types'
import { capabilities } from '../localAdmin'
import type { Capability, LocalCard, LocalReceipt } from '../localAdmin'
import { grouped } from '../localAdmin'
import { Badge, CheckList, InfoBanner, Spinner } from '../components/ui'
import DirectVision from './DirectVision'

interface BillingView {
  mode: 'manual'
  enabled: boolean
  card: LocalCard | null
  receipts: LocalReceipt[]
  total_toman: number
  notice: string
}
const EMPTY_VIEW: BillingView = {
  mode: 'manual',
  enabled: false,
  card: null,
  receipts: [],
  total_toman: 0,
  notice: '',
}
const TONE: Record<Capability['state'], { tone: 'green' | 'amber' | 'red'; label: string }> = {
  active: { tone: 'green', label: 'فعال' },
  setup: { tone: 'amber', label: 'نیازمند تنظیم' },
  'offline-blocked': { tone: 'red', label: 'در این نسخه ممکن نیست' },
}

/**
 * Admin panel of the offline edition. The owner connects the Gemini model with their own
 * key, sees the real state of every capability, and keeps the manual receipt ledger.
 */
export default function LocalAdminPanel({ ctx }: { ctx: AppContext }) {
  const [view, setView] = useState<BillingView>(EMPTY_VIEW)
  const [card, setCard] = useState({ card_number: '', holder: '', bank: '' })
  const [confirmed, setConfirmed] = useState(false)
  const [receipt, setReceipt] = useState({
    payer: '',
    amount_toman: '',
    paid_at: today(),
    reference: '',
    note: '',
  })
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  async function load() {
    setView(await api<BillingView>('/local/billing'))
  }
  useEffect(() => {
    let active = true
    void api<BillingView>('/local/billing')
      .then((result) => {
        if (!active) return
        setView(result)
        if (result.card)
          setCard({
            card_number: result.card.card_number,
            holder: result.card.holder,
            bank: result.card.bank,
          })
      })
      .catch((e) => active && setError(errorMessage(e)))
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  async function run(action: () => Promise<unknown>, message: string) {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      await action()
      await load()
      await ctx.refresh()
      ctx.notify(message, 'success')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  const state = ctx.data.services
  // Field records are read through the same local API the laboratory page uses.
  const [labCount, setLabCount] = useState(0)
  useEffect(() => {
    let active = true
    void api<unknown[]>('/field-records/labs')
      .then((rows) => active && setLabCount(rows.length))
      .catch(() => active && setLabCount(0))
    return () => {
      active = false
    }
  }, [view])
  const rows = useMemo(
    () =>
      capabilities({
        keyPresent: !!state.vision_configured,
        keyVerified: !!state.vision_verified,
        model: state.vision_model ?? '',
        cardSaved: !!view.card,
        receipts: view.receipts.length,
        orchards: ctx.data.orchards.length,
        reports: ctx.data.reports.length,
        analyzed: ctx.data.reports.filter((r) => r.data.provider === 'gemini-direct-byo-key')
          .length,
        labs: labCount,
      }),
    [state, view, ctx.data]
  )
  const groups: Capability['group'][] = ['تحلیل', 'داده و محتوا', 'سرویس‌های سروری', 'انتشار']
  return (
    <div className="reference-page local-admin-page">
      <div className="reference-heading">
        <span className="feature-icon green">
          <ShieldCheck size={29} />
        </span>
        <div>
          <h1>پنل مدیر (نسخه مستقل)</h1>
          <p>
            اتصال مدل Gemini با کلید شخصی شما، وضعیت واقعی همه بخش‌ها و دفتر دریافت وجه روی همین
            دستگاه.
          </p>
        </div>
        <Badge tone="amber">بدون سرور · بدون هزینه</Badge>
      </div>
      <InfoBanner>
        این پنل روی خودِ گوشی/مرورگر شما کار می‌کند. کلید API فقط در حافظه همین دستگاه می‌ماند، داخل
        فایل نصبی و فایل پشتیبان نیست، و همه تحلیل‌های عکس و آزمایش از همین اتصال استفاده می‌کنند.
      </InfoBanner>

      <DirectVision ctx={ctx} />

      <section className="reference-card" aria-label="وضعیت همه بخش‌ها">
        <h2>
          <ListChecks size={22} /> وضعیت کامل بخش‌های برنامه
        </h2>
        <p className="section-description">
          «فعال» یعنی همین حالا روی این دستگاه کار می‌کند. «نیازمند تنظیم» یعنی با یک کار مشخص (ثبت
          کلید یا ثبت کارت) فعال می‌شود. «در این نسخه ممکن نیست» یعنی به سرور، حساب یا امضای اپل
          نیاز دارد و تا آن زمان هیچ نتیجه‌ای از آن ساخته نمی‌شود.
        </p>
        {groups.map((group) => {
          const items = rows.filter((r) => r.group === group)
          if (!items.length) return null
          return (
            <div key={group} className="capability-group">
              <h3>{group}</h3>
              <ul className="capability-list">
                {items.map((item) => (
                  <li key={item.key} className={`capability-item ${item.state}`}>
                    <span className="capability-icon">
                      {item.state === 'active' ? (
                        <CircleCheck size={18} />
                      ) : item.state === 'setup' ? (
                        <Settings2 size={18} />
                      ) : (
                        <Ban size={18} />
                      )}
                    </span>
                    <div>
                      <strong>{item.title}</strong>{' '}
                      <Badge tone={TONE[item.state].tone}>{TONE[item.state].label}</Badge>
                      <p>{item.detail}</p>
                      {item.how && <small>راه فعال‌سازی: {item.how}</small>}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </section>

      <section className="reference-card" aria-label="کارت مقصد و دفتر دریافت">
        <h2>
          <CreditCard size={22} /> کارت مقصد واریز و دفتر دریافت
        </h2>
        <InfoBanner tone="warning">
          این نسخه درگاه بانکی ندارد. کارتی که اینجا ثبت می‌کنید فقط برای راهنمایی واریز
          کارت‌به‌کارت و ثبت دستی دریافتی‌هاست؛ هیچ تأیید خودکاری از بانک انجام نمی‌شود. اگر
          نمی‌خواهید شماره کارت روی این دستگاه بماند، این بخش را خالی بگذارید.
        </InfoBanner>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            void run(
              () =>
                api('/local/billing', {
                  method: 'PUT',
                  body: JSON.stringify({ ...card, confirmed }),
                }),
              'کارت مقصد ذخیره شد؛ راهنمای واریز در صفحه اعتبار نمایش داده می‌شود.'
            )
          }}
        >
          <fieldset disabled={busy}>
            <div className="bank-fields">
              <label>
                شماره کارت ۱۶ رقمی
                <input
                  dir="ltr"
                  inputMode="numeric"
                  value={card.card_number}
                  maxLength={25}
                  onChange={(e) => setCard((old) => ({ ...old, card_number: e.target.value }))}
                  placeholder="۱۶ رقم؛ با خط تیره یا فاصله هم می‌پذیرد"
                  required
                />
              </label>
              <label>
                نام صاحب کارت
                <input
                  value={card.holder}
                  maxLength={100}
                  onChange={(e) => setCard((old) => ({ ...old, holder: e.target.value }))}
                  placeholder="نام مالک حساب مقصد"
                  required
                />
              </label>
              <label>
                نام بانک
                <input
                  value={card.bank}
                  maxLength={80}
                  onChange={(e) => setCard((old) => ({ ...old, bank: e.target.value }))}
                  placeholder="نام بانک"
                  required
                />
              </label>
            </div>
            <label className="consent-check">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              <span>
                تأیید می‌کنم شماره کارت بالا را با کارت واقعی خودم حرف‌به‌حرف تطبیق دادم. (ترتیب
                گروه‌های رقم‌ها را نمی‌توان با محاسبه تشخیص داد؛ فقط تطبیق چشمی معتبر است.)
              </span>
            </label>
            <div className="local-settings-actions">
              <button className="button primary" disabled={busy} type="submit">
                <Save size={17} /> ذخیره کارت مقصد
              </button>
              {view.card && (
                <button
                  className="button danger ghost"
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void run(
                      () => api('/local/billing/card', { method: 'DELETE' }),
                      'کارت مقصد حذف شد.'
                    )
                  }
                >
                  <Trash2 size={16} /> حذف کارت
                </button>
              )}
              {busy && <Spinner />}
            </div>
          </fieldset>
        </form>
        {view.card && (
          <p className="muted">
            <BadgeCheck size={16} /> کارت ثبت‌شده:{' '}
            <span dir="ltr">{grouped(view.card.card_number)}</span> به نام {view.card.holder} —{' '}
            {view.card.bank} · تأییدشده در {persianDate(view.card.confirmed_at)}
          </p>
        )}

        <h3>
          <Wallet size={19} /> ثبت دریافتی دستی
        </h3>
        <p className="section-description">
          هر واریزی که واقعاً دیدید اینجا ثبت کنید تا دفتر شما کامل بماند. این ثبت، تأیید بانکی نیست
          و سند رسمی نمی‌سازد.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            void run(
              () =>
                api('/local/billing/receipts', {
                  method: 'POST',
                  body: JSON.stringify({
                    ...receipt,
                    amount_toman: Number(receipt.amount_toman.replace(/[,،\s]/g, '')),
                  }),
                }),
              'دریافتی در دفتر دستگاه ثبت شد.'
            ).then(() => {
              setReceipt((old) => ({
                ...old,
                payer: '',
                amount_toman: '',
                reference: '',
                note: '',
              }))
            })
          }}
        >
          <fieldset disabled={busy}>
            <div className="bank-fields">
              <label>
                نام پرداخت‌کننده
                <input
                  value={receipt.payer}
                  maxLength={80}
                  onChange={(e) => setReceipt((old) => ({ ...old, payer: e.target.value }))}
                  required
                />
              </label>
              <label>
                مبلغ (تومان)
                <input
                  dir="ltr"
                  inputMode="numeric"
                  value={receipt.amount_toman}
                  onChange={(e) => setReceipt((old) => ({ ...old, amount_toman: e.target.value }))}
                  required
                />
              </label>
              <label>
                تاریخ واریز
                <input
                  dir="ltr"
                  value={receipt.paid_at}
                  onChange={(e) => setReceipt((old) => ({ ...old, paid_at: e.target.value }))}
                  required
                />
              </label>
              <label>
                کد پیگیری (اختیاری)
                <input
                  dir="ltr"
                  value={receipt.reference}
                  maxLength={60}
                  onChange={(e) => setReceipt((old) => ({ ...old, reference: e.target.value }))}
                />
              </label>
            </div>
            <label>
              توضیح (اختیاری)
              <input
                value={receipt.note}
                maxLength={300}
                onChange={(e) => setReceipt((old) => ({ ...old, note: e.target.value }))}
              />
            </label>
            <button className="button secondary" disabled={busy} type="submit">
              <Wallet size={17} /> ثبت در دفتر دریافتی‌ها
            </button>
          </fieldset>
        </form>
        {!!view.receipts.length && (
          <div className="table-scroll">
            <table className="receipt-ledger">
              <thead>
                <tr>
                  <th>پرداخت‌کننده</th>
                  <th>مبلغ (تومان)</th>
                  <th>تاریخ</th>
                  <th>کد پیگیری</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {view.receipts.map((row) => (
                  <tr key={row.id}>
                    <td>{row.payer}</td>
                    <td dir="ltr">{fa(row.amount_toman)}</td>
                    <td dir="ltr">{row.paid_at.slice(0, 10)}</td>
                    <td dir="ltr">{row.reference || '—'}</td>
                    <td>
                      <button
                        className="icon-button"
                        aria-label={`حذف دریافت ${row.payer}`}
                        disabled={busy}
                        onClick={() =>
                          void run(
                            () => api(`/local/billing/receipts/${row.id}`, { method: 'DELETE' }),
                            'دریافتی از دفتر حذف شد.'
                          )
                        }
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted">
              جمع ثبت‌شده: <span dir="ltr">{fa(view.total_toman)}</span> تومان در{' '}
              {fa(view.receipts.length)} دریافت — ثبت دستی، نه تأیید بانکی.
            </p>
          </div>
        )}
      </section>

      <section className="reference-card" aria-label="داده دستگاه و پشتیبان">
        <h2>
          <Database size={22} /> داده‌های همین دستگاه
        </h2>
        <CheckList
          items={[
            `${fa(ctx.data.orchards.length)} باغ · ${fa(ctx.data.reports.length)} پرونده عکس · ${fa(ctx.data.tasks.length)} یادآور`,
            `${fa(labCount)} آزمایش خاک/آب · ${fa(ctx.data.reports.filter((r) => r.data.provider === 'gemini-direct-byo-key').length)} گزارش تحلیل‌شده با کلید شما`,
            `دفتر دریافتی: ${fa(view.receipts.length)} مورد · کتابخانه پژوهش: ${state.knowledge_version}`,
          ]}
        />
        <p className="section-description">
          پشتیبان‌گیری، بازگردانی و پاک‌سازی در صفحه «داده‌ها و پشتیبان» است. کلید API در پشتیبان
          نیست، اما کارت مقصد و دفتر دریافتی‌ها در پشتیبان هستند؛ فایل پشتیبان را جای امن نگه دارید.
        </p>
        <div className="local-settings-actions">
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => void run(() => load(), 'وضعیت پنل بازخوانی شد.')}
          >
            <RefreshCw size={17} /> بازخوانی وضعیت
          </button>
          <button className="button secondary" onClick={() => ctx.navigate('settings')}>
            <Database size={17} /> پشتیبان و بازگردانی
          </button>
          <button className="button secondary" onClick={() => ctx.navigate('subscription')}>
            <CreditCard size={17} /> صفحه اعتبار و راهنمای واریز
          </button>
        </div>
      </section>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}
