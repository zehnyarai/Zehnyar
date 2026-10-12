import { useEffect, useRef, useState } from 'react'
import { KeyRound, Save, Trash2 } from 'lucide-react'
import { api, errorMessage } from '../api'
import type { AppContext } from '../types'
import { InfoBanner, Spinner } from './ui'

interface RuntimeConfiguration {
  provider: string
  model: string
  key_present: boolean
  requests_enabled: boolean
  storage: string
  notice: string
}

export default function GeminiConfiguration({
  ctx,
  allowed,
}: {
  ctx: AppContext
  allowed: boolean
}) {
  const key = useRef<HTMLInputElement>(null)
  const [model, setModel] = useState('gemini-3.1-pro-preview')
  const [enabled, setEnabled] = useState(false),
    [approved, setApproved] = useState(false)
  const [status, setStatus] = useState<RuntimeConfiguration | null>(null)
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  const secure = typeof window !== 'undefined' && window.location.protocol === 'https:'
  useEffect(() => {
    let active = true
    if (!allowed) return
    void api<RuntimeConfiguration>('/admin/vision/configuration')
      .then((s) => {
        if (active) {
          setStatus(s)
          setModel(s.model || 'gemini-3.1-pro-preview')
          setEnabled(s.requests_enabled)
        }
      })
      .catch((e) => {
        if (active) setError(errorMessage(e))
      })
    return () => {
      active = false
      if (key.current) key.current.value = ''
    }
  }, [allowed])
  async function save() {
    if (!allowed || !secure || busy) return
    if (enabled && !approved) {
      setError('قبل از فعال‌سازی، سهمیه و سیاست هزینه حساب Google را بررسی و تأیید کنید.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const replacement = key.current?.value.trim() || null
      const s = await api<RuntimeConfiguration>('/admin/vision/configuration', {
        method: 'PUT',
        body: JSON.stringify({
          model,
          replacement_key: replacement,
          requests_enabled: enabled,
          usage_approved: approved,
        }),
      })
      setStatus(s)
      ctx.notify(
        'تنظیمات موقت سرور ذخیره شد؛ اتصال و تحلیل واقعی هنوز نیازمند آزمون تصویر است.',
        'success'
      )
      try {
        await ctx.refresh()
      } catch {
        ctx.notify('تنظیمات ذخیره شد؛ بازخوانی وضعیت سرور ممکن نشد.', 'error')
      }
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      if (key.current) key.current.value = ''
      setApproved(false)
      setBusy(false)
    }
  }
  async function clear() {
    if (
      !allowed ||
      !secure ||
      busy ||
      !confirm('کلید موجود در حافظه این سرور حذف و فراخوانی‌ها خاموش شوند؟')
    )
      return
    setBusy(true)
    setError('')
    try {
      setStatus(
        await api<RuntimeConfiguration>('/admin/vision/configuration', { method: 'DELETE' })
      )
      setEnabled(false)
      setApproved(false)
      await ctx.refresh()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      if (key.current) key.current.value = ''
      setBusy(false)
    }
  }
  return (
    <section className="reference-card gemini-configuration" aria-label="تنظیم امن Gemini">
      <h2>
        <KeyRound size={22} /> تنظیم امن Gemini — فقط مدیر
      </h2>
      <InfoBanner tone="warning">
        کلیدی که در چت یا مخزن ارسال شده را باطل و تعویض کنید. کلید جایگزین فقط از این فرم مدیر روی
        HTTPS ارسال می‌شود؛ در چت، APK یا کد عمومی قرار نمی‌گیرد. این تنظیم فقط در حافظه سرور است و
        پس از راه‌اندازی دوباره از بین می‌رود؛ برای ماندگاری از Secret خصوصی میزبان استفاده کنید.
      </InfoBanner>
      {!secure && (
        <InfoBanner tone="warning">
          فرم محرمانه روی HTTP قابل استفاده نیست. ورود کلید فقط روی HTTPS مجاز است.
        </InfoBanner>
      )}
      {status && (
        <p className="section-description">
          کلید سرور: {status.key_present ? 'موجود؛ مقدار قابل مشاهده نیست' : 'ثبت نشده'} · مجوز
          فراخوانی: {status.requests_enabled ? 'روشن؛ اتصال باید آزمایش شود' : 'خاموش'}
        </p>
      )}
      <form
        autoComplete="off"
        onSubmit={(e) => {
          e.preventDefault()
          void save()
        }}
      >
        <fieldset disabled={!allowed || !secure || busy}>
          <div className="reference-form-grid">
            <label>
              مدل Gemini
              <input
                value={model}
                maxLength={100}
                dir="ltr"
                onChange={(e) => {
                  setModel(e.target.value)
                  setApproved(false)
                }}
                required
              />
            </label>
            <label>
              کلید جایگزین — محرمانه
              <input
                ref={key}
                type="password"
                autoComplete="new-password"
                maxLength={2048}
                dir="ltr"
                spellCheck={false}
                placeholder="برای حفظ کلید موجود، خالی بگذارید"
                onChange={() => setApproved(false)}
              />
            </label>
          </div>
          <label className="consent-check">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => {
                setEnabled(e.target.checked)
                setApproved(false)
              }}
            />
            <span>
              فراخوانی مدل را برای این سرور فعال کن؛ ذخیره کلید به‌تنهایی این گزینه را روشن نمی‌کند.
            </span>
          </label>
          <label className="consent-check">
            <input
              type="checkbox"
              checked={approved}
              onChange={(e) => setApproved(e.target.checked)}
            />
            <span>
              سهمیه/سیاست هزینه حساب Google را بررسی کرده‌ام و استفاده از آن را تأیید می‌کنم.
              رایگان‌بودن مدل و درخواست‌ها تضمین نمی‌شود؛ ثبت تنظیمات خودش درخواست تحلیل اجرا
              نمی‌کند.
            </span>
          </label>
          <div className="analysis-main-actions">
            <button className="button primary" type="submit">
              {busy ? (
                <Spinner />
              ) : (
                <>
                  <Save size={17} /> ذخیره امن تنظیمات موقت
                </>
              )}
            </button>
            <button className="button secondary" type="button" onClick={() => void clear()}>
              <Trash2 size={17} /> حذف کلید حافظه و خاموش‌کردن
            </button>
          </div>
        </fieldset>
      </form>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
    </section>
  )
}
