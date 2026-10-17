import { useCallback, useEffect, useRef, useState } from 'react'
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
  Wallet,
} from 'lucide-react'
import type { AppContext, Report } from '../types'
import { IS_STANDALONE } from '../config'
import { api, checkImage, errorMessage, fa, takePhoto, persianDate } from '../api'
import { Badge, InfoBanner, Spinner } from '../components/ui'
import Paywall, { isQuotaError } from '../components/Paywall'
import type { QuotaPayload } from '../quota'
import { ScientificPlan } from '../components/scientific'
import { KeyRound } from 'lucide-react'
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
  const [needConsent, setNeedConsent] = useState(false)
  const [quota, setQuota] = useState<QuotaPayload | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [drag, setDrag] = useState(false)
  const upload = useRef<HTMLInputElement>(null),
    camera = useRef<HTMLInputElement>(null),
    consentBox = useRef<HTMLInputElement>(null)
  // In the offline edition this reflects the owner's own on-device key.
  const configured = ctx.data.services.vision_configured
  const verified = configured && !!ctx.data.services.vision_verified
  // Two free analyses, then the paid package; the counter lives on this device.
  const loadQuota = useCallback(async () => {
    if (!IS_STANDALONE) return
    try {
      setQuota(await api<QuotaPayload>('/local/quota'))
    } catch {
      /* keep the last known view; the analysis call itself enforces the quota */
    }
  }, [])
  useEffect(() => {
    void loadQuota()
  }, [loadQuota])
  const blocked = IS_STANDALONE && quota?.blocked === true
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
        IS_STANDALONE
          ? 'تحلیل عکس روی این دستگاه فعال نیست. در «داده‌ها و پشتیبان» کلید شخصی Google خود را ثبت کنید یا پرونده را بدون تحلیل ذخیره کنید.'
          : 'مدل بینایی واقعی هنوز متصل نیست؛ تحلیل عکس انجام نمی‌شود. پرونده را می‌توانید ذخیره کنید و برنامه بررسیِ اطلاعات خودتان را ببینید.'
      )
      return
    }
    if (mode === 'analyze' && !consent) {
      // The consent box used to be hidden in the offline edition, so this dead end was the
      // only thing a farmer could reach. Now the box is always on screen and we take the
      // owner straight to it instead of only printing an error.
      setNeedConsent(true)
      if (IS_STANDALONE)
        setError(
          'برای شروع، کادر «رضایت آگاهانه» را در همین صفحه تیک بزنید؛ بدون آن هیچ عکسی به Google فرستاده نمی‌شود.'
        )
      else setError('ارسال تصاویر و اطلاعات باغ به سرویس تحلیل نیاز به تأیید آگاهانه شما دارد.')
      // jsdom has no scrollIntoView; the focus hint is what the tests assert.
      consentBox.current?.scrollIntoView?.({ block: 'center', behavior: 'smooth' })
      consentBox.current?.focus()
      return
    }
    // The offline edition has no server account: the photos stay on this phone, so a
    // login prompt here used to swallow the tap and make «تحلیل عکس» look dead.
    if (mode === 'analyze' && !IS_STANDALONE && (!ctx.data.user || ctx.data.user.is_demo)) {
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
      // Offline edition: the photo set is stored on the device first, then screened with
      // the owner's own key. A failed screening never destroys the saved photos.
      const saved = await api<Report>(
        IS_STANDALONE ? '/local/photos' : mode === 'analyze' ? '/analyses' : '/photos',
        { method: 'POST', body }
      )
      const report =
        IS_STANDALONE && mode === 'analyze'
          ? await api<Report>('/local/analyses', {
              method: 'POST',
              body: JSON.stringify({ report_id: saved.id, consent }),
            })
          : saved
      ctx.openReport(report)
      try {
        await ctx.refresh()
      } catch {
        ctx.notify(
          'گزارش دریافت شد؛ بازخوانی موجودی/تاریخچه ممکن نشد. دوباره تحلیل ارسال نکنید.',
          'error'
        )
      }
      ctx.notify(
        mode === 'analyze'
          ? 'گزارش غربالگری احتمالی ساخته شد؛ عکس‌ها هم روی دستگاه ذخیره شدند. نتیجه نیاز به تأیید کارشناس دارد.'
          : 'پرونده عکس و اطلاعات ذخیره شد؛ تصویر تحلیل نشده است.',
        'success'
      )
    } catch (e) {
      if (isQuotaError(e)) {
        await loadQuota()
        setError('')
        ctx.notify('تحلیل‌های رایگان این دستگاه تمام شده؛ برای ادامه یک بسته تهیه کنید.', 'info')
      } else {
        setError(errorMessage(e))
      }
    } finally {
      setBusy(false)
      if (mode === 'analyze') void loadQuota()
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
        <Badge tone={verified ? 'green' : 'amber'}>
          {verified
            ? IS_STANDALONE
              ? 'کلید شما آزموده شده است'
              : 'مدل پاسخ تصویری داده است'
            : configured
              ? 'تنظیم شده؛ آزمون اتصال را بزنید'
              : IS_STANDALONE
                ? 'آمادهٔ راه‌اندازی با کلید رایگان'
                : 'مدل واقعی متصل نیست'}
        </Badge>
      </div>
      {IS_STANDALONE && !configured && (
        <div className="reference-alert activation-alert">
          <Info size={18} />
          <div>
            <strong>این بخش کار می‌کند؛ فقط کلید رایگان Google را یک بار ثبت کنید.</strong>
            <ol className="activation-steps">
              <li>در «داده‌ها و پشتیبان» یک کلید رایگان از Google AI Studio بسازید.</li>
              <li>کلید را همان‌جا وارد کنید و «آزمون اتصال» را بزنید.</li>
              <li>به همین صفحه برگردید؛ عکس بگیرید و تحلیل را شروع کنید.</li>
            </ol>
            <small>
              بدون کلید هم می‌توانید عکس‌ها را ذخیره کنید و «برنامه بررسی و مراقبت» را بگیرید.
            </small>
          </div>
          <button
            className="button primary small"
            onClick={() => ctx.navigate('settings')}
            type="button"
          >
            <KeyRound size={16} /> ثبت کلید رایگان
          </button>
        </div>
      )}
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
          <LeafIcon /> چند نکتهٔ کوتاه
        </h2>
        <p className="section-description">
          باغ و بخش درخت را انتخاب کنید، نشانه‌ها را تیک بزنید و بقیه را در بخش اختیاری بگذارید.
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
        <details className="advanced-fields">
          <summary>زمینهٔ باغ و جزئیات بیشتر (اختیاری) — دقت بررسی را بالا می‌برد</summary>
          <p className="muted">
            خالی گذاشتن اشکالی ندارد؛ نتیجه فقط کلی‌تر می‌شود. هیچ فیلدی اجباری نیست.
          </p>
          <div className="reference-form-grid">
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
                {[
                  'یک شاخه',
                  'یک درخت',
                  'چند درخت پراکنده',
                  'یک ردیف یا لکه باغ',
                  'بخش عمده باغ',
                ].map((s) => (
                  <option key={s}>{s}</option>
                ))}
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
        </details>
        <label className={needConsent && !consent ? 'consent-check attention' : 'consent-check'}>
          <input
            ref={consentBox}
            type="checkbox"
            checked={consent}
            onChange={(e) => {
              setConsent(e.target.checked)
              if (e.target.checked) {
                setNeedConsent(false)
                setError('')
              }
            }}
            disabled={busy}
          />
          <span>
            {IS_STANDALONE ? (
              <>
                با تیک‌زدن این کادر اجازه می‌دهم تصویر بدون EXIF/GPS و اطلاعات باغ و آزمایش‌های
                مرتبط، با کلید شخصی خودم مستقیماً به سرویس Google ارسال شود. روی طرح رایگان Google،
                محتوای درخواست‌ها برای بهبود محصولات گوگل استفاده می‌شود. نتیجه احتمالی است و دقت
                علمی محلی آن تأیید نشده است.
              </>
            ) : (
              <>
                اجازه می‌دهم تصاویرِ بازتولیدشده بدون EXIF/GPS و اطلاعات باغ و آزمایش‌های مرتبط به
                سرویس بینایی ارسال شوند. نتیجه احتمالی و دقت علمی محلی آن تأیید نشده است.
              </>
            )}
          </span>
        </label>
        {configured && (
          <InfoBanner tone={verified ? 'info' : 'warning'}>
            مدل تنظیم‌شده:{' '}
            <strong dir="ltr">
              {ctx.data.services.vision_model || ctx.data.services.vision_provider}
            </strong>
            .
            {verified ? (
              <>
                {' '}
                آخرین پاسخ معتبر تصویری: {persianDate(ctx.data.services.vision_checked_at!)}. این
                وضعیت اثبات دقت علمی یا تشخیص قطعی نیست.
              </>
            ) : (
              <>
                {' '}
                هنوز پاسخ واقعی اخیر برای این تنظیمات تأیید نشده است؛ کلید یا روشن‌کردن گزینه
                به‌تنهایی اثبات اتصال نیست. هر درخواست فقط با رضایت شما ارسال می‌شود.
              </>
            )}
          </InfoBanner>
        )}
        {!configured && (
          <InfoBanner tone="warning">
            <strong>تحلیل واقعی هنوز فعال نیست.</strong> مدل بینایی در این نصب تنظیم نشده؛ ذخیره عکس
            یا برنامه آموزشی را به جای تحلیل علمی تصویر معرفی نمی‌کنیم.
            {IS_STANDALONE ? (
              <p>
                این APK نشانی سرویس آنلاین ندارد. اینترنت به‌تنهایی آن را به Gemini متصل نمی‌کند؛
                نسخه آنلاین باید به سرور واقعی و دارای کلید امن متصل شود.
              </p>
            ) : (
              <p>
                مدیر باید کلید Gemini و مدل مجاز را در تنظیمات امن سرور فعال کند؛ کلید به کاربران
                داده نمی‌شود.
              </p>
            )}
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
        {IS_STANDALONE && quota && (
          <p className={blocked ? 'quota-chip blocked' : 'quota-chip'}>
            <Wallet size={15} />
            {blocked
              ? 'تحلیل‌های رایگان تمام شده؛ پرونده‌ها و عکس‌ها بدون محدودیت کار می‌کنند.'
              : `تحلیل رایگان باقی‌مانده: ${fa(quota.free_left)} از ${fa(quota.free_limit)}`}
            {quota.credits > 0 && ` · بستهٔ خریداری‌شده: ${fa(quota.credits)}`}
          </p>
        )}
        {blocked && quota && <Paywall ctx={ctx} quota={quota} onUnlocked={loadQuota} />}
        <div className="analysis-main-actions">
          <button
            className="button primary"
            disabled={busy || !files.length || blocked}
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
