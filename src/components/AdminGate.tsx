import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { KeyRound, Lock, LockOpen, ShieldCheck, Trash2 } from 'lucide-react'
import {
  AccessError,
  failedAttempts,
  hasAdminLock,
  ensureDefaultAdminLock,
  isUnlocked,
  lockNow,
  lockoutSeconds,
  removeAdminLock,
  setAdminPassword,
  verifyAdminPassword,
  weakAdminLock,
  FORGOT_TEXT,
  MIN_PASSWORD,
  REQUIREMENT_TEXT,
} from '../localAccess'
import { errorMessage, fa } from '../api'
import type { AppContext } from '../types'
import { Badge, InfoBanner, Spinner } from './ui'

const FORGOT_PHRASE = 'حذف رمز مدیر'

/**
 * Protects the owner panel with a password the owner defines here. When no password is
 * set the panel stays open, so nobody can ever be locked out by a password they never
 * chose; the gate simply asks them to define one.
 */
export default function AdminGate({ ctx, children }: { ctx: AppContext; children: ReactNode }) {
  const [locked, setLocked] = useState(hasAdminLock() && !isUnlocked())
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  const [left, setLeft] = useState(lockoutSeconds())
  const [forgot, setForgot] = useState(false),
    [phrase, setPhrase] = useState('')
  const [checking, setChecking] = useState(!hasAdminLock())
  const [showSetup, setShowSetup] = useState(false)
  const [showChange, setShowChange] = useState(false)
  const password = useRef<HTMLInputElement>(null)
  // The owner asked for a password to exist from the first launch. Seed one once per
  // device (and lock immediately) so the panel is never silently open.
  useEffect(() => {
    if (hasAdminLock()) {
      setChecking(false)
      return
    }
    let active = true
    void ensureDefaultAdminLock().finally(() => {
      if (!active) return
      setLocked(hasAdminLock() && !isUnlocked())
      setChecking(false)
    })
    return () => {
      active = false
    }
  }, [])
  useEffect(() => {
    if (!left) return
    const timer = setInterval(() => setLeft(lockoutSeconds()), 1000)
    return () => clearInterval(timer)
  }, [left])
  useEffect(() => {
    if (password.current) password.current.value = ''
  }, [locked])
  async function unlockPanel(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    try {
      if (await verifyAdminPassword(password.current?.value ?? '')) {
        setLocked(false)
        setForgot(false)
        ctx.notify('پنل مدیر باز شد؛ تا بستن برنامه باز می‌ماند.', 'success')
      } else {
        setError(
          `رمز درست نیست. ${fa(failedAttempts())} تلاش ناموفق از ${fa(5)}؛ پس از ۵ تلاش، ۶۰ ثانیه صبر لازم است.`
        )
      }
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      if (password.current) password.current.value = ''
      setLeft(lockoutSeconds())
      setBusy(false)
    }
  }
  async function saveSetup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    const form = new FormData(event.currentTarget)
    setBusy(true)
    setError('')
    try {
      await setAdminPassword(
        form.get('password'),
        String(form.get('hint') ?? ''),
        form.get('repeat')
      )
      setShowSetup(false)
      setLocked(false)
      setShowChange(false)
      ctx.notify('رمز مدیر تعریف شد؛ از این پس برای ورود به پنل لازم است.', 'success')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  function dropLock() {
    if (phrase.trim() !== FORGOT_PHRASE) {
      setError(`برای تأیید، عبارت «${FORGOT_PHRASE}» را دقیقاً بنویسید.`)
      return
    }
    removeAdminLock()
    setForgot(false)
    setPhrase('')
    setLocked(false)
    setShowSetup(true)
    setError('')
    ctx.notify('قفل پنل مدیر برداشته شد؛ داده‌ها و کارت دست‌نخورده‌اند.', 'info')
  }
  if (checking)
    return (
      <div className="reference-page">
        <div className="reference-card loading-inline">
          <Spinner label="آماده‌سازی رمز مدیر…" />
        </div>
      </div>
    )
  if (locked)
    return (
      <div className="reference-page admin-gate-page">
        <div className="reference-heading">
          <span className="feature-icon green">
            <Lock size={28} />
          </span>
          <div>
            <h1>ورود به پنل مدیر</h1>
            <p>
              رمز مدیر روی همین دستگاه نگه داشته می‌شود. اگر رمز را عوض نکرده‌اید، رمز پیش‌فرض مالک
              معتبر است و از «تغییر یا حذف رمز» می‌توانید عوضش کنید.
            </p>
          </div>
          <Badge tone="amber">قفل روی این دستگاه</Badge>
        </div>
        <section className="reference-card admin-gate-card">
          {!forgot ? (
            <form onSubmit={unlockPanel}>
              <label>
                رمز مدیر
                <input
                  ref={password}
                  type="password"
                  name="password"
                  dir="ltr"
                  autoComplete="current-password"
                  required
                  disabled={busy || left > 0}
                />
              </label>
              {hasAdminLock() && (
                <p className="muted">
                  {(() => {
                    const hint = adminHint()
                    return hint ? `راهنمای خودتان: ${hint}` : 'راهنمایی ثبت نشده است.'
                  })()}
                </p>
              )}
              {left > 0 && (
                <InfoBanner tone="warning">
                  چند تلاش ناموفق پشت‌سرهم بود؛ {fa(left)} ثانیه دیگر دوباره تلاش کنید.
                </InfoBanner>
              )}
              <div className="local-settings-actions">
                <button className="button primary" disabled={busy || left > 0}>
                  {busy ? (
                    <Spinner />
                  ) : (
                    <>
                      <LockOpen size={17} /> باز کردن پنل مدیر
                    </>
                  )}
                </button>
                <button
                  className="button secondary"
                  type="button"
                  onClick={() => {
                    setForgot(true)
                    setError('')
                  }}
                >
                  رمز را فراموش کرده‌ام
                </button>
              </div>
            </form>
          ) : (
            <div className="admin-forgot">
              <InfoBanner tone="warning">{FORGOT_TEXT}</InfoBanner>
              <label>
                برای تأیید، عبارت «{FORGOT_PHRASE}» را بنویسید
                <input value={phrase} onChange={(e) => setPhrase(e.target.value)} />
              </label>
              <div className="local-settings-actions">
                <button className="button danger" type="button" onClick={dropLock}>
                  <Trash2 size={16} /> برداشتن قفل و ساختن رمز تازه
                </button>
                <button
                  className="button secondary"
                  type="button"
                  onClick={() => {
                    setForgot(false)
                    setError('')
                  }}
                >
                  بازگشت
                </button>
              </div>
            </div>
          )}
          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}
        </section>
      </div>
    )
  return (
    <>
      {showSetup && (
        <section className="reference-card admin-gate-card" aria-label="تعریف رمز مدیر">
          <h2>
            <KeyRound size={22} /> رمز مدیر را خودتان تعریف کنید
          </h2>
          <InfoBanner>
            رمز تازه فقط روی همین دستگاه ذخیره می‌شود؛ شماره کارت، دفتر دریافتی و کلید سرویس با آن
            از دسترس دیگران دور می‌مانند. رمز فعلی را می‌توانید همین‌جا عوض کنید.
          </InfoBanner>
          <p className="muted">{REQUIREMENT_TEXT}</p>
          <form onSubmit={saveSetup}>
            <fieldset disabled={busy}>
              <div className="bank-fields">
                <label>
                  رمز مدیر (حداقل {MIN_PASSWORD} کاراکتر)
                  <input
                    type="password"
                    name="password"
                    dir="ltr"
                    autoComplete="new-password"
                    minLength={MIN_PASSWORD}
                    maxLength={128}
                    required
                  />
                </label>
                <label>
                  تکرار رمز
                  <input
                    type="password"
                    name="repeat"
                    dir="ltr"
                    autoComplete="new-password"
                    minLength={MIN_PASSWORD}
                    maxLength={128}
                    required
                  />
                </label>
                <label>
                  راهنمای رمز (اختیاری)
                  <input name="hint" maxLength={80} placeholder="مثلاً: سال تولد باغ" />
                </label>
              </div>
              <div className="local-settings-actions">
                <button className="button primary" disabled={busy}>
                  <KeyRound size={17} /> ذخیره رمز مدیر
                </button>
                <button
                  className="button secondary"
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    setShowSetup(false)
                    setError('')
                  }}
                >
                  بعداً
                </button>
                {busy && <Spinner />}
              </div>
            </fieldset>
          </form>
          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}
        </section>
      )}
      <section className="reference-card admin-gate-bar" aria-label="وضعیت قفل پنل مدیر">
        <h2>
          <ShieldCheck size={20} /> قفل پنل مدیر: {hasAdminLock() ? 'فعال' : 'تعریف نشده'}
        </h2>
        {weakAdminLock() && (
          <InfoBanner tone="warning">
            این مرورگر WebCrypto ندارد؛ رمز با روش سازگاری قدیمی (ضعیف‌تر از PBKDF2) ذخیره شد.
          </InfoBanner>
        )}
        <div className="local-settings-actions">
          {hasAdminLock() ? (
            <>
              <button
                className="button secondary"
                type="button"
                onClick={() => {
                  lockNow()
                  setLocked(true)
                }}
              >
                <Lock size={16} /> قفل کردن الان
              </button>
              <button
                className="button secondary"
                type="button"
                onClick={() => {
                  setShowChange(!showChange)
                  setShowSetup(false)
                }}
              >
                <KeyRound size={16} /> تغییر یا حذف رمز
              </button>
            </>
          ) : (
            <button className="button secondary" type="button" onClick={() => setShowSetup(true)}>
              <KeyRound size={16} /> تعریف رمز مدیر
            </button>
          )}
        </div>
        {showChange && (
          <div className="admin-forgot">
            <form onSubmit={saveSetup}>
              <fieldset disabled={busy}>
                <div className="bank-fields">
                  <label>
                    رمز تازه
                    <input
                      type="password"
                      name="password"
                      dir="ltr"
                      autoComplete="new-password"
                      minLength={MIN_PASSWORD}
                      required
                    />
                  </label>
                  <label>
                    تکرار رمز تازه
                    <input
                      type="password"
                      name="repeat"
                      dir="ltr"
                      autoComplete="new-password"
                      minLength={MIN_PASSWORD}
                      required
                    />
                  </label>
                  <label>
                    راهنمای رمز (اختیاری)
                    <input name="hint" maxLength={80} defaultValue={adminHint()} />
                  </label>
                </div>
                <button className="button primary" disabled={busy}>
                  <KeyRound size={17} /> جایگزینی رمز
                </button>
              </fieldset>
            </form>
            <button
              className="button danger ghost"
              type="button"
              onClick={() => {
                setShowChange(false)
                setShowSetup(false)
                setForgot(true)
                setLocked(true)
                lockNow()
              }}
            >
              <Trash2 size={16} /> حذف رمز (نیازمند تأیید عبارت)
            </button>
          </div>
        )}
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
      </section>
      {children}
    </>
  )
}
export function adminHint(): string {
  try {
    return (
      (JSON.parse(localStorage.getItem('pestino-admin-lock') ?? '{}') as { hint?: string }).hint ??
      ''
    )
  } catch {
    return ''
  }
}
export { AccessError }
