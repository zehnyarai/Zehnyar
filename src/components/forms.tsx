import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  ArrowLeft,
  Eye,
  EyeOff,
  LockKeyhole,
  LogOut,
  Mail,
  MapPin,
  Plus,
  ShieldCheck,
  Trash2,
  UserRound,
} from 'lucide-react'
import type { AppContext, Orchard } from '../types'
import { api, errorMessage, fa, persianDate, today } from '../api'
import { Badge, InfoBanner, Logo, Modal, Spinner } from './ui'

export function AuthForm({ ctx, onClose }: { ctx: AppContext; onClose: () => void }) {
  const [mode, setMode] = useState('login')
  const [visible, setVisible] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    const form = new FormData(e.currentTarget)
    const payload = {
      email: form.get('email'),
      password: form.get('password'),
      ...(mode === 'register' ? { name: form.get('name') } : {}),
    }
    try {
      await api(`/auth/${mode}`, { method: 'POST', body: JSON.stringify(payload) })
      await ctx.refresh()
      onClose()
      ctx.notify(
        mode === 'register' ? 'حساب شما ساخته شد. باغ واقعی‌ات را ثبت کن.' : 'به پستینو خوش آمدی.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal
      title="به پستینو خوش آمدی"
      subtitle="همراهی از امروز، برای باغی پربارتر"
      onClose={onClose}
    >
      <div className="auth-brand">
        <Logo compact />
      </div>
      <div className="auth-tabs">
        <button
          className={mode === 'login' ? 'active' : ''}
          onClick={() => {
            setMode('login')
            setError('')
          }}
          disabled={busy}
        >
          ورود به حساب
        </button>
        <button
          className={mode === 'register' ? 'active' : ''}
          onClick={() => {
            setMode('register')
            setError('')
          }}
          disabled={busy}
        >
          ساخت حساب
        </button>
      </div>
      <form
        onSubmit={(e) => {
          void submit(e)
        }}
        key={mode}
        className="stack-form"
      >
        {mode === 'register' && (
          <label>
            نام و نام خانوادگی
            <div className="input-with-icon">
              <UserRound size={17} />
              <input
                name="name"
                placeholder="نام شما"
                minLength={2}
                maxLength={80}
                required
                autoComplete="name"
                disabled={busy}
              />
            </div>
          </label>
        )}
        <label>
          ایمیل
          <div className="input-with-icon">
            <Mail size={17} />
            <input
              type="email"
              name="email"
              placeholder="you@example.com"
              required
              autoComplete="email"
              dir="ltr"
              disabled={busy}
            />
          </div>
        </label>
        <label>
          رمز عبور
          <div className="input-with-icon">
            <LockKeyhole size={17} />
            <input
              type={visible ? 'text' : 'password'}
              name="password"
              placeholder="حداقل ۱۰ کاراکتر"
              minLength={10}
              maxLength={128}
              required
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              disabled={busy}
            />
            <button
              type="button"
              className="icon-button"
              aria-label={visible ? 'پنهان کردن رمز' : 'نمایش رمز'}
              onClick={() => setVisible(!visible)}
            >
              {visible ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button className="button primary" disabled={busy}>
          {busy ? (
            <Spinner label="در حال اتصال…" />
          ) : (
            <>
              {mode === 'register' ? 'ساخت حساب باغدار' : 'ورود به پستینو'}
              <ArrowLeft size={16} />
            </>
          )}
        </button>
      </form>
      <p className="auth-note">
        <ShieldCheck size={14} />
        ورود پیامکی و بازیابی رمز هنوز فعال نیست. در نسخه فعلی از ایمیل و رمز استفاده می‌شود.
      </p>
      {mode === 'register' && (
        <p className="auth-note">
          با ثبت‌نام، داده‌های نمونه حذف می‌شوند. باغ‌هایی که خودت ثبت کرده‌ای در حسابت باقی
          می‌مانند.
        </p>
      )}
    </Modal>
  )
}

export function OrchardForm({
  ctx,
  orchard,
  onClose,
}: {
  ctx: AppContext
  orchard?: Orchard
  onClose: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [confirm, setConfirm] = useState(false)
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    const form = new FormData(e.currentTarget)
    const payload: Record<string, FormDataEntryValue | number> = Object.fromEntries(form.entries())
    for (const key of ['area', 'trees', 'age']) payload[key] = Number(form.get(key))
    try {
      await api(orchard ? `/orchards/${orchard.id}` : '/orchards', {
        method: orchard ? 'PUT' : 'POST',
        body: JSON.stringify(payload),
      })
      await ctx.refresh()
      onClose()
      ctx.notify(orchard ? 'اطلاعات باغ به‌روز شد.' : 'باغ جدید ثبت شد.', 'success')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  async function remove() {
    if (!orchard || busy) return
    setBusy(true)
    try {
      await api(`/orchards/${orchard.id}`, { method: 'DELETE' })
      await ctx.refresh()
      onClose()
      ctx.notify('باغ حذف شد؛ گزارش‌های قبلی محفوظ‌اند.')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal
      title={orchard ? 'ویرایش اطلاعات باغ' : 'یک باغ تازه ثبت کن'}
      subtitle="اطلاعات دقیق‌تر، زمینه بهتر برای بررسی درخت‌ها"
      onClose={onClose}
    >
      <form
        className="stack-form"
        onSubmit={(e) => {
          void submit(e)
        }}
      >
        <label>
          نام باغ
          <input
            name="name"
            placeholder="مثلاً باغ سبز رفسنجان"
            defaultValue={orchard?.name}
            minLength={2}
            maxLength={80}
            required
            disabled={busy}
          />
        </label>
        <div className="form-grid">
          <label>
            استان
            <select name="province" defaultValue={orchard?.province ?? 'کرمان'} disabled={busy}>
              {[
                'آذربایجان شرقی',
                'آذربایجان غربی',
                'اردبیل',
                'اصفهان',
                'البرز',
                'ایلام',
                'بوشهر',
                'تهران',
                'چهارمحال و بختیاری',
                'خراسان جنوبی',
                'خراسان رضوی',
                'خراسان شمالی',
                'خوزستان',
                'زنجان',
                'سمنان',
                'سیستان و بلوچستان',
                'فارس',
                'قزوین',
                'قم',
                'کردستان',
                'کرمان',
                'کرمانشاه',
                'کهگیلویه و بویراحمد',
                'گلستان',
                'گیلان',
                'لرستان',
                'مازندران',
                'مرکزی',
                'هرمزگان',
                'همدان',
                'یزد',
              ].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <label>
            شهر
            <input
              name="city"
              placeholder="نام شهر"
              defaultValue={orchard?.city}
              minLength={2}
              maxLength={50}
              required
              disabled={busy}
            />
          </label>
        </div>
        <div className="form-grid">
          <label>
            رقم پسته
            <input
              name="cultivar"
              list="cultivars"
              defaultValue={orchard?.cultivar ?? 'اکبری'}
              minLength={2}
              maxLength={50}
              required
              disabled={busy}
            />
            <datalist id="cultivars">
              {['اکبری', 'احمدآقایی', 'کله‌قوچی', 'فندقی', 'بادامی', 'چند رقم / نامشخص'].map(
                (p) => (
                  <option key={p}>{p}</option>
                )
              )}
            </datalist>
          </label>
          <label>
            نوع آبیاری
            <select
              name="irrigation"
              defaultValue={orchard?.irrigation ?? 'قطره‌ای'}
              disabled={busy}
            >
              {['قطره‌ای', 'غرقابی', 'جوی و پشته', 'زیرسطحی', 'سایر'].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="form-grid three">
          <label>
            مساحت (هکتار)
            <input
              name="area"
              type="number"
              step="0.01"
              min="0.01"
              max="100000"
              defaultValue={orchard?.area}
              placeholder="۵٫۲"
              required
              disabled={busy}
            />
          </label>
          <label>
            تعداد درخت
            <input
              name="trees"
              type="number"
              step="1"
              min="1"
              max="10000000"
              defaultValue={orchard?.trees}
              placeholder="۸۴۰"
              required
              disabled={busy}
            />
          </label>
          <label>
            سن غالب (سال)
            <input
              name="age"
              type="number"
              step="1"
              min="0"
              max="150"
              defaultValue={orchard?.age ?? 10}
              required
              disabled={busy}
            />
          </label>
        </div>
        <p className="form-helper">
          <MapPin size={14} />
          برای این مرحله، موقعیت دقیق یا اجازه GPS لازم نیست.
        </p>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <div className="modal-actions">
          <button className="button primary" disabled={busy}>
            {busy ? (
              <Spinner label="در حال ذخیره…" />
            ) : (
              <>
                <Plus size={16} />
                {orchard ? 'ذخیره تغییرات' : 'ثبت باغ'}
              </>
            )}
          </button>
          <button className="button secondary" type="button" onClick={onClose} disabled={busy}>
            انصراف
          </button>
          {orchard && (
            <button
              className="button danger ghost"
              type="button"
              onClick={() => setConfirm(!confirm)}
              disabled={busy}
            >
              <Trash2 size={15} />
              حذف باغ
            </button>
          )}
        </div>
      </form>
      {confirm && (
        <div className="delete-confirm">
          <strong>این باغ حذف شود؟</strong>
          <p>یادآورهای مرتبط حذف می‌شوند؛ گزارش‌ها بدون نام باغ باقی می‌مانند.</p>
          <button
            className="button danger small"
            onClick={() => {
              void remove()
            }}
            disabled={busy}
          >
            تأیید حذف باغ
          </button>
          <button className="text-button" onClick={() => setConfirm(false)} disabled={busy}>
            انصراف
          </button>
        </div>
      )}
    </Modal>
  )
}

export function TaskForm({ ctx, onClose }: { ctx: AppContext; onClose: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [due, setDue] = useState(today())
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    const form = new FormData(e.currentTarget)
    const payload = {
      ...Object.fromEntries(form.entries()),
      orchard_id: form.get('orchard_id') || null,
    }
    try {
      await api('/tasks', { method: 'POST', body: JSON.stringify(payload) })
      await ctx.refresh()
      onClose()
      ctx.notify('یادآور به برنامه مراقبت اضافه شد.', 'success')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal
      title="یک قدم برای مراقبت بعدی"
      subtitle="یادآورها در تقویم داخل اپ نمایش داده می‌شوند."
      onClose={onClose}
    >
      <form
        className="stack-form"
        onSubmit={(e) => {
          void submit(e)
        }}
      >
        <label>
          عنوان یادآور
          <input
            name="title"
            placeholder="مثلاً بازدید پشت برگ‌ها"
            minLength={3}
            maxLength={160}
            required
            disabled={busy}
          />
        </label>
        <label>
          باغ
          <select name="orchard_id" disabled={busy}>
            <option value="">همه باغ‌ها / بدون باغ مشخص</option>
            {ctx.data.orchards.map((o) => (
              <option value={o.id} key={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </label>
        <div className="form-grid">
          <label>
            نوع فعالیت
            <select name="kind" disabled={busy}>
              <option value="monitoring">پایش و بازدید</option>
              <option value="irrigation">بررسی آبیاری</option>
              <option value="nutrition">آزمایش و تغذیه</option>
              <option value="general">سایر فعالیت‌ها</option>
            </select>
          </label>
          <label>
            تاریخ
            <input
              type="date"
              name="due_date"
              value={due}
              onChange={(e) => setDue(e.target.value)}
              required
              disabled={busy}
            />
            {due && <small className="muted">{persianDate(due, { year: 'numeric' })}</small>}
          </label>
        </div>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <div className="modal-actions">
          <button className="button primary" disabled={busy}>
            {busy ? (
              <Spinner />
            ) : (
              <>
                <Plus size={16} />
                ثبت یادآور
              </>
            )}
          </button>
          <button className="button secondary" type="button" onClick={onClose} disabled={busy}>
            انصراف
          </button>
        </div>
      </form>
    </Modal>
  )
}

export function ProfileModal({ ctx, onClose }: { ctx: AppContext; onClose: () => void }) {
  const [busy, setBusy] = useState(false)
  async function logout() {
    setBusy(true)
    try {
      await api('/auth/logout', { method: 'POST' })
      await ctx.refresh()
      onClose()
      ctx.navigate('dashboard')
      ctx.notify('از حساب خارج شدی.')
    } catch (e) {
      ctx.notify(errorMessage(e), 'error')
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal title="حساب من" onClose={onClose}>
      <div className="profile-modal-avatar">
        <UserRound size={32} />
      </div>
      <div className="detail-facts">
        <div>
          <span>نام باغدار</span>
          <strong>{ctx.data.user?.name}</strong>
        </div>
        <div>
          <span>ایمیل</span>
          <strong dir="ltr">{ctx.data.user?.email}</strong>
        </div>
        <div>
          <span>نوع حساب</span>
          <Badge>{ctx.data.user?.role === 'admin' ? 'مدیر سامانه' : 'باغدار'}</Badge>
        </div>
        <div>
          <span>اعتبار بررسی</span>
          <strong>{fa(Math.max(0, ctx.data.usage.limit - ctx.data.usage.used))} بررسی</strong>
        </div>
      </div>
      <InfoBanner>
        تأیید ایمیل، بازیابی رمز و مدیریت دستگاه‌های متصل باید پیش از عرضه عمومی تکمیل شوند.
      </InfoBanner>
      <button
        className="button danger"
        onClick={() => {
          void logout()
        }}
        disabled={busy}
      >
        {busy ? (
          <Spinner />
        ) : (
          <>
            <LogOut size={16} />
            خروج از حساب
          </>
        )}
      </button>
    </Modal>
  )
}
