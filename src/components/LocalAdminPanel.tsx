import { useEffect, useState } from 'react'
import {
  BadgeCheck,
  CreditCard,
  Database,
  RefreshCw,
  Save,
  ShieldCheck,
  Trash2,
  Wallet,
} from 'lucide-react'
import { api, errorMessage, fa, today } from '../api'
import type { AppContext } from '../types'
import type { QuotaPayload } from '../quota'
import type { LocalCard, LocalReceipt } from '../localAdmin'
import { grouped } from '../localAdmin'
import { Badge, InfoBanner, Spinner } from './ui'
import DirectVision from './DirectVision'
import SalesPanel from './SalesPanel'
import ReceiptInbox from './ReceiptInbox'

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

/**
 * Owner panel of the offline edition. Everything a farmer must never see lives here:
 * the two provider keys, the day rate, the activation codes and the receipt ledger.
 */
export default function LocalAdminPanel({ ctx }: { ctx: AppContext }) {
  const [tab, setTab] = useState('connection')
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
  const [quota, setQuota] = useState<QuotaPayload | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    const [billing, quota] = await Promise.all([
      api<BillingView>('/local/billing'),
      api<QuotaPayload>('/local/quota'),
    ])
    setView(billing)
    setQuota(quota)
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
    void api<QuotaPayload>('/local/quota')
      .then((payload) => active && setQuota(payload))
      .catch(() => active && setQuota(null))
    return () => {
      active = false
    }
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

  return (
    <div className="reference-page local-admin-page">
      <div className="reference-heading">
        <span className="feature-icon green">
          <ShieldCheck size={28} />
        </span>
        <div>
          <h1>پنل مدیر</h1>
          <p>کلید سرویس‌ها، قیمت‌ها و دفتر دریافت وجه — فقط برای مالک.</p>
        </div>
        <Badge tone="green">فقط مالک</Badge>
      </div>

      <div className="quiet-tabs" role="tablist" aria-label="بخش‌های مدیریت">
        {[
          ['connection', 'اتصال تحلیل'],
          ['receipts', 'فیش‌های واریزی'],
          ['pricing', 'قیمت و اعتبار'],
          ['data', 'کارت و پشتیبان'],
        ].map(([id, label]) => (
          <button
            key={id}
            role="tab"
            aria-selected={tab === id}
            aria-controls={`admin-${id}`}
            id={`tab-${id}`}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <div
        id="admin-connection"
        role="tabpanel"
        aria-labelledby="tab-connection"
        hidden={tab !== 'connection'}
      >
        <DirectVision ctx={ctx} />
      </div>
      <div
        id="admin-receipts"
        role="tabpanel"
        aria-labelledby="tab-receipts"
        hidden={tab !== 'receipts'}
      >
        <ReceiptInbox rows={view.receipts} refresh={load} analysisPackage={quota?.package} />
      </div>
      <div
        id="admin-pricing"
        role="tabpanel"
        aria-labelledby="tab-pricing"
        hidden={tab !== 'pricing'}
      >
        <SalesPanel ctx={ctx} />
      </div>
      <div id="admin-data" role="tabpanel" aria-labelledby="tab-data" hidden={tab !== 'data'}>
        <section className="reference-card" aria-label="کارت مقصد و دفتر دریافت">
          <h2>
            <CreditCard size={21} /> کارت واریز و دفتر دریافت
          </h2>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              void run(
                () =>
                  api('/local/billing', {
                    method: 'PUT',
                    body: JSON.stringify({ ...card, confirmed }),
                  }),
                'کارت ذخیره شد؛ صفحهٔ اعتبار همین شماره را نشان می‌دهد.'
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
                    placeholder="۱۶ رقم؛ با فاصله هم می‌پذیرد"
                    required
                  />
                </label>
                <label>
                  نام صاحب کارت
                  <input
                    value={card.holder}
                    maxLength={100}
                    onChange={(e) => setCard((old) => ({ ...old, holder: e.target.value }))}
                    required
                  />
                </label>
                <label>
                  نام بانک (اختیاری)
                  <input
                    value={card.bank}
                    maxLength={80}
                    onChange={(e) => setCard((old) => ({ ...old, bank: e.target.value }))}
                  />
                </label>
              </div>
              <label className="consent-check">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                <span>تأیید می‌کنم شماره کارت را با کارت واقعی خودم حرف‌به‌حرف تطبیق دادم.</span>
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
                        'کارت حذف شد.'
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
              <BadgeCheck size={16} /> <span dir="ltr">{grouped(view.card.card_number)}</span> ·{' '}
              {view.card.holder}
              {view.card.bank ? ` — ${view.card.bank}` : ''}
            </p>
          )}

          <h3>
            <Wallet size={18} /> ثبت دریافتی دستی
          </h3>
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
                'دریافتی ثبت شد.'
              ).then(() =>
                setReceipt((old) => ({ ...old, payer: '', amount_toman: '', reference: '' }))
              )
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
                    onChange={(e) =>
                      setReceipt((old) => ({ ...old, amount_toman: e.target.value }))
                    }
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
              <button className="button secondary" disabled={busy} type="submit">
                <Wallet size={17} /> ثبت در دفتر دریافتی‌ها
              </button>
            </fieldset>
          </form>
          <p className="muted">این دفتر ثبت دستی است، نه تأیید بانکی خودکار.</p>
          {!!view.receipts.filter((r) => !r.imported).length && (
            <div className="table-scroll">
              <table className="receipt-ledger">
                <thead>
                  <tr>
                    <th>پرداخت‌کننده</th>
                    <th>مبلغ</th>
                    <th>تاریخ</th>
                    <th>کد</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {view.receipts
                    .filter((r) => !r.imported)
                    .map((row) => (
                      <tr key={row.id}>
                        <td>{row.payer}</td>
                        <td dir="ltr">{fa(row.amount_toman)}</td>
                        <td dir="ltr">{row.paid_at.slice(0, 10)}</td>
                        <td dir="ltr">{row.reference || '—'}</td>
                        <td>
                          {row.confirmed_at ? (
                            <span className="receipt-ok">
                              <BadgeCheck size={15} /> تأییدشده
                              {row.granted_analyses ? ` · ${fa(row.granted_analyses)} تحلیل` : ''}
                            </span>
                          ) : (
                            <button
                              className="text-button"
                              disabled={busy}
                              onClick={() =>
                                void run(
                                  () =>
                                    api(`/local/billing/receipts/${row.id}/confirm`, {
                                      method: 'POST',
                                    }),
                                  'واریز تأیید و تحلیل اضافه شد.'
                                )
                              }
                            >
                              <BadgeCheck size={16} /> تأیید واریز
                            </button>
                          )}
                          <button
                            className="icon-button"
                            aria-label={`حذف دریافت ${row.payer}`}
                            disabled={busy}
                            onClick={() =>
                              void run(
                                () =>
                                  api(`/local/billing/receipts/${row.id}`, { method: 'DELETE' }),
                                'دریافتی حذف شد.'
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
            </div>
          )}
        </section>

        <section className="reference-card admin-links-card">
          <h2>
            <Database size={20} /> داده و پشتیبان
          </h2>
          <p className="muted">
            {fa(ctx.data.orchards.length)} باغ · {fa(ctx.data.reports.length)} پرونده ·{' '}
            {fa(quota?.used ?? 0)} تحلیل مصرف‌شده · {fa(view.receipts.length)} دریافتی
          </p>
          <div className="local-settings-actions">
            <button className="button secondary" onClick={() => ctx.navigate('settings')}>
              <Database size={17} /> پشتیبان و بازگردانی
            </button>
            <button className="button secondary" onClick={() => void ctx.navigate('subscription')}>
              <CreditCard size={17} /> اعتبار من
            </button>
            <button className="button ghost" onClick={() => window.location.reload()}>
              <RefreshCw size={16} /> بازخوانی
            </button>
          </div>
          <p className="muted">
            کلیدها در فایل پشتیبان نیستند؛ کارت و دفتر دریافتی در پشتیبان هستند.
          </p>
        </section>
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      <InfoBanner>
        <ShieldCheck size={17} /> کاربران در هیچ صفحه‌ای نام سرویس یا مدل را نمی‌بینند؛ فقط پاسخ
        علمی و قیمت تومانی.
      </InfoBanner>
    </div>
  )
}
