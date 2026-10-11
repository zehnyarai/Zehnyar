import { useEffect, useRef, useState } from 'react'
import {
  ArrowLeft,
  Bug,
  Camera,
  FileImage,
  Info,
  ScanLine,
  ShieldCheck,
  Trash2,
  Upload,
} from 'lucide-react'
import type { AppContext, Report } from '../types'
import { IS_STANDALONE } from '../config'
import { api, checkImage, errorMessage, fa, takePhoto } from '../api'
import { Badge, InfoBanner, Spinner } from '../components/ui'
import { ScientificPlan } from '../components/scientific'
import { EMPTY_CONTEXT, SYMPTOMS, validateContext } from '../scientific'
import type { DiagnosticContext } from '../scientific'

const PARTS = ['برگ', 'میوه', 'شاخه و تنه', 'کل درخت', 'ریشه و طوقه', 'گل و جوانه']
const STAGES = [
  'خواب زمستانی',
  'تورم جوانه',
  'گل‌دهی',
  'تشکیل میوه',
  'رشد مغز',
  'رسیدگی و برداشت',
  'پس از برداشت',
]
export default function Analysis({
  ctx,
  initialFile,
  initialOrchard,
}: {
  ctx: AppContext
  initialFile?: File
  initialOrchard?: string
}) {
  const [files, setFiles] = useState<File[]>(initialFile ? [initialFile] : [])
  const [previews, setPreviews] = useState<string[]>([])
  const [orchard, setOrchard] = useState(initialOrchard ?? '')
  const [part, setPart] = useState('برگ')
  const [notes, setNotes] = useState('')
  const [context, setContext] = useState<DiagnosticContext>({ ...EMPTY_CONTEXT, symptoms: [] })
  const [plan, setPlan] = useState<DiagnosticContext | null>(null)
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [drag, setDrag] = useState(false)
  const upload = useRef<HTMLInputElement>(null),
    camera = useRef<HTMLInputElement>(null)
  const configured = !IS_STANDALONE && ctx.data.services.vision_configured
  useEffect(() => {
    const urls = files.map((file) => URL.createObjectURL(file))
    setPreviews(urls)
    return () => urls.forEach((url) => URL.revokeObjectURL(url))
  }, [files])
  function select(incoming: File[]) {
    const invalid = incoming.map(checkImage).find(Boolean)
    if (invalid) {
      setError(invalid)
      return
    }
    if (files.length + incoming.length > 4) {
      setError('حداکثر چهار تصویر: علامت نزدیک، پشت برگ، نمای تاج و بخش مرتبط.')
      return
    }
    setFiles((old) => [...old, ...incoming])
    setError('')
  }
  function update<K extends keyof DiagnosticContext>(key: K, value: DiagnosticContext[K]) {
    setContext((old) => ({ ...old, [key]: value }))
    setPlan(null)
  }
  function chooseOrchard(value: string) {
    setOrchard(value)
    const o = ctx.data.orchards.find((o) => o.id === value)
    if (o)
      setContext((old) => ({
        ...old,
        province: o.province,
        cultivar: o.cultivar,
        age: String(o.age),
        irrigation: o.irrigation,
      }))
    setPlan(null)
  }
  async function submit(mode: 'analyze' | 'save') {
    if (busy || !files.length) return
    setError('')
    if (mode === 'analyze' && !configured) {
      setError(
        'مدل بینایی واقعی هنوز متصل نیست؛ تحلیل عکس انجام نمی‌شود. پرونده را می‌توانید ذخیره کنید و برنامه بررسیِ اطلاعات خودتان را ببینید.'
      )
      return
    }
    if (mode === 'analyze' && !consent) {
      setError('ارسال تصاویر و اطلاعات باغ به سرویس تحلیل نیاز به تأیید آگاهانه شما دارد.')
      return
    }
    if (mode === 'analyze' && (!ctx.data.user || ctx.data.user.is_demo)) {
      ctx.openAuth()
      return
    }
    let checked: DiagnosticContext
    try {
      checked = validateContext(context)
    } catch (e) {
      setError(errorMessage(e))
      return
    }
    setBusy(true)
    const body = new FormData()
    body.append('image', files[0])
    files.slice(1).forEach((file) => body.append('additional_images', file))
    body.append('orchard_id', orchard)
    body.append('tree_part', part)
    body.append('notes', notes)
    body.append('context', JSON.stringify(checked))
    body.append('consent', String(consent))
    try {
      const report = await api<Report>(
        mode === 'analyze' ? '/analyses' : IS_STANDALONE ? '/local/photos' : '/photos',
        { method: 'POST', body }
      )
      await ctx.refresh()
      ctx.openReport(report)
      ctx.notify(
        mode === 'analyze'
          ? 'گزارش غربالگری احتمالی ذخیره شد؛ نتیجه نیاز به تأیید دارد.'
          : 'پرونده عکس و اطلاعات ذخیره شد؛ تصویر تحلیل نشده است.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="reference-page scan-page">
      <div className="reference-heading">
        <span className="feature-icon red">
          <Bug size={28} />
        </span>
        <div>
          <h1>اسکن و تشخیص احتمال آفت</h1>
          <p>عکس برگ، میوه، شاخه، تنه یا هر بخش درخت پسته را همراه اطلاعات باغ ثبت کنید.</p>
        </div>
        <Badge tone={configured ? 'green' : 'amber'}>
          {configured ? 'مدل بینایی تنظیم شده' : 'مدل واقعی متصل نیست'}
        </Badge>
      </div>
      <div className="reference-alert">
        <Info size={18} />
        <p>
          بررسی علمی باید مشاهدات تصویر، فرضیه‌ها و آزمایش لازم را جدا کند. از عکس تنها نمی‌توان
          نیاز غذایی، نوع عامل بیماری یا دوز درمان را قطعی تعیین کرد.
        </p>
      </div>
      <section className="reference-card scan-card">
        <div
          className={`reference-dropzone ${drag ? 'is-dragging' : ''} ${files.length ? 'with-previews' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDrag(true)
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDrag(false)
            if (!busy) select(Array.from(e.dataTransfer.files))
          }}
        >
          {files.length ? (
            <div className="photo-grid">
              {files.map((file, i) => (
                <figure key={`${file.name}-${i}`}>
                  <img src={previews[i]} alt={`تصویر انتخاب‌شده ${fa(i + 1)} برای بررسی`} />
                  <figcaption>
                    <FileImage size={14} />
                    <span>
                      {i === 0 ? 'تصویر اصلی' : 'زاویه تکمیلی'} · {file.name}
                    </span>
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={`حذف تصویر ${i + 1}`}
                      disabled={busy}
                      onClick={() => setFiles((old) => old.filter((_, j) => j !== i))}
                    >
                      <Trash2 size={16} />
                    </button>
                  </figcaption>
                </figure>
              ))}
            </div>
          ) : (
            <>
              <span className="camera-circle">
                <Camera size={34} />
              </span>
              <h2>عکس برگ یا هر قسمت درخت را اینجا بارگذاری کنید</h2>
              <p>JPG، PNG یا WebP — هر تصویر حداکثر ۶ مگابایت</p>
              <p className="muted">تا ۴ زاویه از یک مسئله؛ نمای نزدیک، پشت برگ و نمای کامل درخت</p>
            </>
          )}
          <div className="upload-actions">
            <button
              className="button secondary"
              disabled={busy || files.length >= 4}
              onClick={() => upload.current?.click()}
            >
              <Upload size={18} />
              {files.length ? 'افزودن زاویه دیگر' : 'انتخاب فایل'}
            </button>
            <button
              className="button secondary"
              disabled={busy || files.length >= 4}
              onClick={() =>
                void takePhoto(
                  () => camera.current?.click(),
                  (file) => select([file])
                ).catch((e) => setError(errorMessage(e)))
              }
            >
              <Camera size={18} />
              گرفتن عکس
            </button>
          </div>
        </div>
        <input
          ref={upload}
          type="file"
          hidden
          multiple
          accept="image/jpeg,image/png,image/webp"
          aria-label="انتخاب تصاویر درخت"
          onChange={(e) => {
            select(Array.from(e.target.files ?? []))
            e.target.value = ''
          }}
        />
        <input
          ref={camera}
          type="file"
          hidden
          accept="image/*"
          capture="environment"
          aria-label="دوربین درخت"
          onChange={(e) => {
            select(Array.from(e.target.files ?? []))
            e.target.value = ''
          }}
        />
        <div className="photo-guidance">
          <ScanLine size={21} />
          <p>
            در نور طبیعی و بدون فیلتر عکس بگیرید. یک بخش سالم را هم برای مقایسه نشان دهید. برای عکس
            ریشه، به درخت آسیب نزنید؛ نمونه‌برداری تخصصی لازم است.
          </p>
        </div>
      </section>
      <section className="reference-card diagnostic-form">
        <h2>
          <LeafIcon /> اطلاعات لازم برای بررسی علمی
        </h2>
        <p className="section-description">
          زمینهٔ باغ، خطای بررسی را کمتر می‌کند؛ جای آزمایش و بازدید حضوری نیست.
        </p>
        <div className="reference-form-grid">
          <label>
            باغ
            <select value={orchard} onChange={(e) => chooseOrchard(e.target.value)} disabled={busy}>
              <option value="">بدون باغ مشخص</option>
              {ctx.data.orchards.map((o) => (
                <option value={o.id} key={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            بخش درخت
            <select value={part} onChange={(e) => setPart(e.target.value)} disabled={busy}>
              {PARTS.map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <label>
            استان / منطقه
            <input
              value={context.province}
              maxLength={160}
              onChange={(e) => update('province', e.target.value)}
              placeholder="مثلاً کرمان، رفسنجان"
              disabled={busy}
            />
          </label>
          <label>
            رقم و پایه (اگر می‌دانید)
            <input
              value={context.cultivar}
              maxLength={160}
              onChange={(e) => update('cultivar', e.target.value)}
              placeholder="مثلاً احمدآقایی؛ پایه نامشخص"
              disabled={busy}
            />
          </label>
          <label>
            سن درخت (سال)
            <input
              type="number"
              min="0"
              max="150"
              value={context.age}
              onChange={(e) => update('age', e.target.value)}
              placeholder="نامشخص"
              disabled={busy}
            />
          </label>
          <label>
            مرحله رشد
            <select
              value={context.stage}
              onChange={(e) => update('stage', e.target.value)}
              disabled={busy}
            >
              <option value="">نامشخص</option>
              {STAGES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            مدت شروع علائم (روز)
            <input
              type="number"
              min="0"
              max="3650"
              value={context.duration}
              onChange={(e) => update('duration', e.target.value)}
              placeholder="نامشخص"
              disabled={busy}
            />
          </label>
          <label>
            درگیری تقریبی باغ (%)
            <input
              type="number"
              min="0"
              max="100"
              value={context.affected_percent}
              onChange={(e) => update('affected_percent', e.target.value)}
              placeholder="مشاهده شما، نه محاسبه تصویر"
              disabled={busy}
            />
          </label>
          <label>
            پراکندگی علائم
            <select
              value={context.distribution}
              onChange={(e) => update('distribution', e.target.value)}
              disabled={busy}
            >
              <option value="">نامشخص</option>
              {['یک شاخه', 'یک درخت', 'چند درخت پراکنده', 'یک ردیف یا لکه باغ', 'بخش عمده باغ'].map(
                (s) => (
                  <option key={s}>{s}</option>
                )
              )}
            </select>
          </label>
          <label>
            روش / آخرین آبیاری
            <input
              value={context.irrigation}
              maxLength={160}
              onChange={(e) => update('irrigation', e.target.value)}
              placeholder="روش، تاریخ و مشکل احتمالی"
              disabled={busy}
            />
          </label>
        </div>
        <fieldset className="symptoms-fieldset" disabled={busy}>
          <legend>چه نشانه‌هایی خودتان مشاهده کرده‌اید؟</legend>
          <div className="symptom-options">
            {SYMPTOMS.map((s) => (
              <label key={s.id}>
                <input
                  type="checkbox"
                  checked={context.symptoms.includes(s.id)}
                  onChange={(e) =>
                    update(
                      'symptoms',
                      e.target.checked
                        ? [...context.symptoms, s.id]
                        : context.symptoms.filter((id) => id !== s.id)
                    )
                  }
                />
                {s.label}
              </label>
            ))}
          </div>
        </fieldset>
        <label className="full-label">
          سابقه کود، سم، تنش هوا یا آزمایش اخیر
          <textarea
            value={context.recent_inputs}
            maxLength={1000}
            rows={3}
            onChange={(e) => update('recent_inputs', e.target.value)}
            placeholder="نام و تاریخ مصرف، تنش اخیر و نتیجه آزمایش در صورت وجود؛ بدون اطلاعات شخصی"
            disabled={busy}
          />
        </label>
        <label className="full-label">
          توضیحات اختیاری
          <textarea
            value={notes}
            maxLength={1000}
            rows={3}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="روند علائم، هدف شما و اطلاعاتی که در عکس معلوم نیست…"
            disabled={busy}
          />
          <span className="character-count">{fa(notes.length)} / ۱٬۰۰۰</span>
        </label>
        {!IS_STANDALONE && (
          <label className="consent-check">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              disabled={busy}
            />
            <span>
              اجازه می‌دهم تصاویرِ بازتولیدشده بدون EXIF/GPS و اطلاعات باغ و آزمایش‌های مرتبط به
              سرویس بینایی ارسال شوند. نتیجه احتمالی و دقت علمی محلی آن تأیید نشده است.
            </span>
          </label>
        )}
        {!configured && (
          <InfoBanner tone="warning">
            <strong>تحلیل واقعی هنوز فعال نیست.</strong> مدل بینایی در این نصب تنظیم نشده؛ ذخیره عکس
            یا برنامه آموزشی را به جای تحلیل علمی تصویر معرفی نمی‌کنیم.
          </InfoBanner>
        )}
        {error && (
          <div className="form-error" role="alert">
            {error}
            {error.includes('وارد حساب') && (
              <button className="text-button" onClick={ctx.openAuth}>
                ورود به حساب
                <ArrowLeft size={15} />
              </button>
            )}
          </div>
        )}
        <div className="analysis-main-actions">
          <button
            className="button primary"
            disabled={busy || !files.length}
            onClick={() => void submit('analyze')}
          >
            {busy ? (
              <Spinner />
            ) : (
              <>
                <Bug size={19} />
                تحلیل تصویر و بررسی احتمال آفت
              </>
            )}
          </button>
          <button
            className="button secondary"
            disabled={busy || !files.length}
            onClick={() => void submit('save')}
          >
            <Upload size={18} />
            ذخیره پرونده بدون تحلیل
          </button>
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => {
              try {
                setPlan(validateContext(context))
                setError('')
              } catch (e) {
                setError(errorMessage(e))
              }
            }}
          >
            <ShieldCheck size={18} />
            نمایش برنامه بررسی و مراقبت
          </button>
        </div>
      </section>
      {plan && <ScientificPlan context={plan} ctx={ctx} />}
    </div>
  )
}
function LeafIcon() {
  return <ShieldCheck size={22} />
}
