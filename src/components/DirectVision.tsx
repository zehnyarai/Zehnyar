import { useEffect, useRef, useState } from 'react'
import { KeyRound, PlugZap, Save, ShieldCheck, Trash2 } from 'lucide-react'
import { api, errorMessage, persianDate } from '../api'
import type { AppContext } from '../types'
import { Badge, CheckList, InfoBanner, Spinner } from './ui'

interface DirectStatus {
  model: string
  key_present: boolean
  checked_at: string | null
  connection_ok: boolean
  note: string
  storage: string
}
const MODELS = ['gemini-3.1-pro-preview', 'gemini-3.1-flash', 'gemini-2.5-pro', 'gemini-2.5-flash']

/**
 * On-device activation for the offline edition: the owner's own Google key lives only
 * on this phone, never in the APK, the repository or the backup file.
 */
export default function DirectVision({ ctx }: { ctx: AppContext }) {
  const key = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState<DirectStatus | null>(null)
  const [model, setModel] = useState(MODELS[0])
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  useEffect(() => {
    let active = true
    void api<DirectStatus>('/local/vision')
      .then((s) => {
        if (!active) return
        setStatus(s)
        if (s.model) setModel(s.model)
      })
      .catch((e) => active && setError(errorMessage(e)))
    return () => {
      active = false
      if (key.current) key.current.value = ''
    }
  }, [])
  async function call(path: string, options?: RequestInit) {
    setBusy(true)
    setError('')
    try {
      const next = await api<DirectStatus>(path, options)
      setStatus(next)
      if (next.model) setModel(next.model)
      await ctx.refresh()
      return true
    } catch (e) {
      setError(errorMessage(e))
      return false
    } finally {
      if (key.current) key.current.value = ''
      setBusy(false)
    }
  }
  async function save() {
    const value = key.current?.value.trim() ?? ''
    const ok = await call('/local/vision', {
      method: 'PUT',
      // Sending an empty field keeps the key already stored on this device.
      body: JSON.stringify(value ? { model, key: value } : { model }),
    })
    if (ok) ctx.notify('تنظیمات روی همین دستگاه ذخیره شد. حالا آزمون اتصال بزنید.', 'success')
  }
  async function test() {
    const ok = await call('/local/vision/test', { method: 'POST' })
    ctx.notify(
      ok
        ? 'آزمون اتصال موفق شد؛ تحلیل عکس روی این دستگاه کار می‌کند.'
        : 'آزمون اتصال انجام نشد؛ پیام خطا را ببینید.',
      ok ? 'success' : 'error'
    )
  }
  async function remove() {
    if (!confirm('کلید ذخیره‌شده روی این دستگاه پاک شود؟ تا ثبت دوباره، تحلیل غیرفعال می‌ماند.'))
      return
    const ok = await call('/local/vision', { method: 'DELETE' })
    if (ok) ctx.notify('کلید از این دستگاه پاک شد.', 'success')
  }
  return (
    <section className="card local-settings-card" aria-label="تحلیل هوشمند با کلید شخصی">
      <h2>
        <KeyRound size={22} /> تحلیل هوشمند عکس و آزمایش با کلید شخصی شما
        <Badge tone={status?.key_present ? (status.connection_ok ? 'green' : 'amber') : 'amber'}>
          {status?.key_present
            ? status.connection_ok
              ? 'اتصال آزموده شده'
              : 'ثبت شده؛ بدون آزمون'
            : 'غیرفعال'}
        </Badge>
      </h2>
      <p>
        در این نسخه مستقل، تحلیل عکس درخت و تفسیر آزمایش خاک/آب از خودِ همین گوشی و با کلید شخصی
        Google انجام می‌شود. برای این کار به سرور و هزینه میزبانی نیازی نیست؛ فقط اینترنت خودِ گوشی
        و یک کلید رایگان از Google لازم است.
      </p>
      <CheckList
        items={[
          'کلید فقط در همین مرورگر/گوشی ذخیره می‌شود؛ داخل فایل نصب (APK)، مخزن کد و فایل پشتیبان قرار نمی‌گیرد.',
          'عکسی که برای تحلیل می‌فرستید و اطلاعات باغ به Google ارسال می‌شود؛ بقیهٔ پرونده‌ها روی دستگاه می‌مانند.',
          'سهمیه و شرایط رایگان حساب شما تابع سیاست Google است؛ این برنامه هزینه‌ای از شما نمی‌گیرد و هزینه‌ای را تضمین نمی‌کند.',
          'کلید را در چت، شبکه اجتماعی یا عکس صفحه پخش نکنید. اگر لو رفت، در پنل Google آن را باطل کنید.',
        ]}
      />
      <InfoBanner tone="warning">
        <ShieldCheck size={18} /> نتیجهٔ مدل «غربالگری احتمالی» است، نه تشخیص قطعی و نه دوز سم/کود.
        هیچ درصد دقت علمی برای این خروجی اندازه‌گیری نشده است. تصمیم نهایی با کارشناس و آزمایش محلی
        است.
      </InfoBanner>
      <fieldset disabled={busy}>
        <label>
          مدل
          <input
            list="pestino-direct-models"
            dir="ltr"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="gemini-3.1-pro-preview"
          />
        </label>
        <datalist id="pestino-direct-models">
          {MODELS.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
        <label>
          کلید API شخصی Google (فقط روی همین دستگاه)
          <input
            ref={key}
            type="password"
            dir="ltr"
            autoComplete="off"
            spellCheck={false}
            placeholder={
              status?.key_present
                ? 'ذخیره شده است؛ برای تغییر مقدار تازه بگذارید'
                : 'AIza… یا کلید تازه Google AI Studio'
            }
          />
        </label>
        <p className="muted">
          کلید را از <span dir="ltr">Google AI Studio → Get API key</span> بسازید (نشانی:{' '}
          <span dir="ltr">aistudio.google.com/apikey</span>) و همان‌جا کپی کنید. این برنامه کلید را
          جایی جز حافظهٔ همین دستگاه نمی‌فرستد.
        </p>
        <div className="local-settings-actions">
          <button className="button primary" disabled={busy} onClick={() => void save()}>
            <Save size={17} /> ذخیره روی این دستگاه
          </button>
          <button
            className="button secondary"
            disabled={busy || !status?.key_present}
            onClick={() => void test()}
          >
            <PlugZap size={17} /> آزمون اتصال
          </button>
          <button
            className="button danger ghost"
            disabled={busy || !status?.key_present}
            onClick={() => void remove()}
          >
            <Trash2 size={16} /> پاک‌کردن کلید
          </button>
          {busy && <Spinner />}
        </div>
      </fieldset>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {status && (
        <p className="muted">
          وضعیت: کلید {status.key_present ? 'ثبت شده' : 'ثبت نشده'} · مدل{' '}
          <span dir="ltr">{status.model || '—'}</span> · آزمون اتصال:{' '}
          {status.checked_at ? `${persianDate(status.checked_at)} (${status.note})` : 'انجام نشده'}{' '}
          · محل نگهداری: {status.storage}
        </p>
      )}
    </section>
  )
}
