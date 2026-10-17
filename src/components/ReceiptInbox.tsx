import { useState } from 'react'
import { CheckCheck, Download, FileUp, Copy, X } from 'lucide-react'
import { api, errorMessage, fa } from '../api'
import type { LocalReceipt } from '../localAdmin'
import { readReceiptPacket } from '../receiptTransfer'
import { saveTextFile } from '../files'
import { Spinner } from './ui'
import { analysesForPayment } from '../quota'
import type { AnalysisPackage } from '../quota'

/** Owner-only file inbox. It deliberately does not pretend local storage is a remote inbox. */
export default function ReceiptInbox({
  rows,
  refresh,
  analysisPackage,
}: {
  rows: LocalReceipt[]
  refresh: () => Promise<void>
  analysisPackage?: AnalysisPackage
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [review, setReview] = useState<LocalReceipt | null>(null)
  const [checked, setChecked] = useState(false)
  const [reason, setReason] = useState('')
  async function run(action: () => Promise<unknown>, message: string) {
    if (busy) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await action()
      await refresh()
      setNotice(message)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  const inbox = rows.filter((r) => r.imported)
  return (
    <section className="reference-card receipt-inbox" aria-label="فیش‌های ارسالی باغداران">
      <h2>فیش‌های ارسالی باغداران</h2>
      <p className="muted">
        فایل فیش را از پیام‌رسان ذخیره و اینجا باز کنید. واریز را در گردش حساب بانکی خودتان بررسی
        کنید؛ عکس فیش به‌تنهایی اثبات پرداخت نیست.
      </p>
      <label className="button secondary file-label">
        <FileUp size={18} /> ورود فایل فیش
        <input
          type="file"
          accept="application/json,.json"
          disabled={busy}
          aria-label="فایل فیش باغدار"
          onChange={(e) => {
            const file = e.target.files?.[0]
            e.target.value = ''
            if (file)
              void run(async () => {
                const content = await readReceiptPacket(file)
                await api('/local/billing/receipts/import', {
                  method: 'POST',
                  body: JSON.stringify({ content }),
                })
              }, 'فیش وارد شد؛ هنوز هیچ اعتباری اضافه نشده است.')
          }}
        />
      </label>
      {!inbox.length && (
        <p className="empty-receipts">فیش دریافتی ندارید. این نسخه صندوق آنلاین ندارد.</p>
      )}
      <div className="receipt-list">
        {inbox.map((row) => (
          <article className="receipt-row" key={row.id}>
            <div>
              <strong>{row.payer}</strong>
              <p>
                {fa(row.amount_toman)} تومان · پیگیری <bdi>{row.reference}</bdi>
              </p>
              <small>
                {row.confirmed_at
                  ? `تأییدشده · ${fa(row.granted_analyses ?? 0)} تحلیل`
                  : row.rejected_reason
                    ? `ردشده: ${row.rejected_reason}`
                    : 'در انتظار بررسی مدیر'}
              </small>
            </div>
            <button
              className="button secondary small"
              onClick={() => {
                setReview(row)
                setChecked(false)
                setReason('')
                setError('')
                setNotice('')
              }}
            >
              مشاهده و بررسی
            </button>
          </article>
        ))}
      </div>
      {review && (
        <div className="receipt-review" role="region" aria-label="بررسی فیش">
          <button className="text-button" onClick={() => setReview(null)}>
            <X size={16} /> بستن بررسی
          </button>
          <h3>
            {review.payer} · {fa(review.amount_toman)} تومان
          </h3>
          <p>
            تاریخ واریز: <bdi>{review.paid_at.slice(0, 10)}</bdi> · کد پیگیری:{' '}
            <bdi>{review.reference}</bdi>
          </p>
          <p className="muted">{review.note}</p>
          {review.image_data && (
            <img
              className="receipt-image"
              src={review.image_data}
              alt={`فیش واریزی ${review.payer}`}
            />
          )}
          {(() => {
            const row = rows.find((r) => r.id === review.id) ?? review
            if (row.activation_code)
              return (
                <div className="activation-code">
                  <label>
                    کد اعتبار برای ارسال به باغدار
                    <input
                      dir="ltr"
                      readOnly
                      value={row.activation_code}
                      onFocus={(e) => e.target.select()}
                    />
                  </label>
                  <p>{fa(row.granted_analyses ?? 0)} تحلیل؛ اعتبار به گوشی مدیر اضافه نشده است.</p>
                  <div className="local-settings-actions">
                    <button
                      className="button secondary"
                      onClick={() =>
                        void run(
                          () => navigator.clipboard.writeText(row.activation_code!),
                          'کد کپی شد؛ برای همان پرداخت‌کننده بفرستید.'
                        )
                      }
                    >
                      <Copy size={16} /> کپی کد
                    </button>
                    <button
                      className="button secondary"
                      onClick={() =>
                        void run(async () => {
                          const saved = await saveTextFile(
                            `pestino-credit-${row.id}.txt`,
                            `پستینو\nپرداخت‌کننده: ${row.payer}\nپیگیری: ${row.reference}\nتعداد تحلیل: ${row.granted_analyses}\nکد: ${row.activation_code}\nاین کد را در «اعتبار من» وارد کنید.`,
                            'text/plain'
                          )
                          if (!saved) throw new Error('ذخیره لغو شد؛ کد همچنان در دفتر موجود است.')
                        }, 'فایل کد ذخیره شد؛ آن را برای پرداخت‌کننده بفرستید.')
                      }
                    >
                      <Download size={16} /> ذخیرهٔ پاسخ مدیر
                    </button>
                  </div>
                </div>
              )
            if (row.rejected_reason)
              return (
                <p className="form-error">
                  دلیل رد: {row.rejected_reason} — این دلیل را برای باغدار بفرستید.
                </p>
              )
            return (
              <>
                <p className="approval-count">
                  اعتبار این واریز با قیمت فعلی:{' '}
                  <strong>
                    {fa(
                      analysisPackage ? analysesForPayment(row.amount_toman, analysisPackage) : 0
                    )}{' '}
                    تحلیل
                  </strong>
                </p>
                <label className="consent-check">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => setChecked(e.target.checked)}
                  />
                  مبلغ، تاریخ و کد پیگیری را در گردش حساب بانکی خودم تطبیق دادم.
                </label>
                <button
                  className="button primary"
                  disabled={
                    busy ||
                    !checked ||
                    !analysisPackage ||
                    analysesForPayment(row.amount_toman, analysisPackage) < 1
                  }
                  onClick={() =>
                    void run(
                      () => api(`/local/billing/receipts/${row.id}/confirm`, { method: 'POST' }),
                      'تأیید شد؛ کد زیر را برای باغدار بفرستید.'
                    )
                  }
                >
                  <CheckCheck size={18} /> تأیید و صدور اعتبار
                </button>
                <details className="quiet-details">
                  <summary>رد فیش</summary>
                  <label>
                    دلیل رد
                    <input
                      maxLength={300}
                      value={reason}
                      onChange={(e) => setReason(e.target.value)}
                    />
                  </label>
                  <button
                    className="button secondary"
                    disabled={busy || reason.trim().length < 3}
                    onClick={() =>
                      void run(
                        () =>
                          api(`/local/billing/receipts/${row.id}/reject`, {
                            method: 'POST',
                            body: JSON.stringify({ reason }),
                          }),
                        'فیش رد شد؛ دلیل را برای باغدار بفرستید.'
                      )
                    }
                  >
                    ثبت رد فیش
                  </button>
                </details>
              </>
            )
          })()}
        </div>
      )}
      {busy && <Spinner />}
      {notice && (
        <p className="paywall-done" role="status">
          {notice}
        </p>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </section>
  )
}
