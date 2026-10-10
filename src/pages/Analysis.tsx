import { IS_STANDALONE, assetUrl } from '../config'
import { useEffect, useRef, useState } from 'react'
import {
  ArrowLeft,
  Camera,
  Check,
  CircleHelp,
  FileImage,
  Leaf,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
  ZoomIn,
} from 'lucide-react'
import type { AnalysisData, AppContext, Report } from '../types'
import { api, checkImage, errorMessage, fa, takePhoto } from '../api'
import { Badge, CheckList, InfoBanner, PageTitle, Spinner } from '../components/ui'

export default function Analysis({
  ctx,
  initialFile,
  initialOrchard,
}: {
  ctx: AppContext
  initialFile?: File
  initialOrchard?: string
}) {
  const [file, setFile] = useState<File | undefined>(initialFile)
  const [preview, setPreview] = useState('')
  const [orchard, setOrchard] = useState(initialOrchard ?? ctx.data.orchards[0]?.id ?? '')
  const [part, setPart] = useState('برگ')
  const [notes, setNotes] = useState('')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [sampleBusy, setSampleBusy] = useState(false)
  const [error, setError] = useState('')
  const [drag, setDrag] = useState(false)
  const upload = useRef<HTMLInputElement>(null)
  const camera = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (!file) {
      setPreview('')
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])
  function select(next?: File) {
    if (!next) return
    const err = checkImage(next)
    if (err) {
      setError(err)
      return
    }
    setFile(next)
    setError('')
  }
  async function analyze() {
    if (!file || busy) return
    setError('')
    if (!consent && !IS_STANDALONE) {
      setError('لطفاً ارسال تصویر به سرویس تحلیل و محدودیت‌های بررسی را تأیید کنید.')
      return
    }
    setBusy(true)
    const body = new FormData()
    body.append('image', file)
    body.append('orchard_id', orchard)
    body.append('tree_part', part)
    body.append('notes', notes)
    body.append('consent', 'true')
    try {
      const report = await api<Report>(IS_STANDALONE ? '/local/photos' : '/analyses', {
        method: 'POST',
        body,
      })
      await ctx.refresh()
      ctx.openReport(report)
      ctx.notify(
        IS_STANDALONE
          ? 'عکس و یادداشت روی دستگاه ذخیره شدند؛ تحلیلی انجام نشده.'
          : 'گزارش بررسی ذخیره شد.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  async function sample() {
    setSampleBusy(true)
    try {
      const result = await api<{ data: AnalysisData }>('/sample-report')
      ctx.openReport({
        id: 'example',
        is_sample: 1,
        data: result.data,
        orchard_id: null,
        orchard_name: 'نمونه آموزشی، نه باغ شما',
        tree_part: 'برگ',
        notes: '',
        image_url: assetUrl('/images/pistachio-leaves.jpg'),
        created_at: new Date().toISOString(),
      })
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setSampleBusy(false)
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ببین، بشناس، آگاهانه اقدام کن"
        title={IS_STANDALONE ? 'ثبت عکس و یادداشت درخت' : 'بررسی هوشمند درخت پسته'}
        subtitle="عکس روشن و اطلاعات باغ، شروع یک بررسی بهتر است."
        action={
          <Badge tone={ctx.data.services.vision_configured ? 'green' : 'amber'}>
            <span className="status-dot" />
            {IS_STANDALONE
              ? 'محلی · رایگان'
              : ctx.data.services.vision_configured
                ? 'سرویس تنظیم شده'
                : 'آماده اتصال به سرویس'}
          </Badge>
        }
      />
      <div className="analysis-stepper">
        {['انتخاب تصویر', 'اطلاعات درخت', IS_STANDALONE ? 'ثبت روی دستگاه' : 'بررسی و اقدام'].map(
          (s, i) => (
            <div className={i === 0 && file ? 'step complete' : 'step'} key={s}>
              <span>{i === 0 && file ? <Check size={15} /> : fa(i + 1)}</span>
              <strong>{s}</strong>
              {i < 2 && <div className="step-line" />}
            </div>
          )
        )}
      </div>
      {IS_STANDALONE && (
        <InfoBanner>
          <strong>ثبت عکس، نه تشخیص هوشمند.</strong> عکس و یادداشت فقط روی همین دستگاه نگهداری
          می‌شوند. هیچ تصویر یا اطلاعاتی برای تحلیل به سرور ارسال نمی‌شود.
        </InfoBanner>
      )}
      {!IS_STANDALONE && !ctx.data.services.vision_configured && (
        <InfoBanner tone="warning">
          <strong>تحلیل واقعی هنوز فعال نشده است.</strong> کلید و مدل بینایی باید توسط مدیر روی سرور
          تنظیم شوند. نمونه گزارش فقط شکل نتیجه را نشان می‌دهد و عکس انتخابی شما را تحلیل نمی‌کند.
        </InfoBanner>
      )}
      <div className="analysis-layout">
        <div className="card analysis-form">
          <div className="form-section-title">
            <span>۱</span>
            <div>
              <h2>تصویر درخت</h2>
              <p>بخشی را که می‌خواهی بررسی شود، واضح نشان بده.</p>
            </div>
          </div>
          <div
            className={`analysis-dropzone ${drag ? 'is-dragging' : ''} ${preview ? 'has-image' : ''}`}
            onDragOver={(e) => {
              e.preventDefault()
              setDrag(true)
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDrag(false)
              if (!busy) select(e.dataTransfer.files[0])
            }}
          >
            {preview ? (
              <>
                <img src={preview} alt="تصویر انتخاب‌شده برای بررسی" />
                <div className="preview-overlay">
                  <span>
                    <FileImage size={15} />
                    {file?.name}
                  </span>
                  <button
                    className="icon-button"
                    aria-label="حذف تصویر انتخابی"
                    onClick={() => setFile(undefined)}
                    disabled={busy}
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="large-upload-icon">
                  <Leaf size={34} strokeWidth={1.4} />
                  <ScanLine size={68} className="upload-scan" strokeWidth={1} />
                </div>
                <h3>یک تصویر واضح از درخت انتخاب کن</h3>
                <p>عکس را اینجا بکش یا از گالری انتخاب کن.</p>
                <span>JPG، PNG یا WebP · حداکثر ۸ مگابایت</span>
              </>
            )}
          </div>
          <div className="upload-actions">
            <button
              className="button secondary"
              onClick={() => upload.current?.click()}
              disabled={busy}
            >
              <Upload size={16} />
              {file ? 'انتخاب عکس دیگر' : 'انتخاب از گالری'}
            </button>
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => {
                void takePhoto(() => camera.current?.click(), select).catch(() =>
                  ctx.notify('عکس دریافت نشد؛ می‌توانید از گالری انتخاب کنید.')
                )
              }}
            >
              <Camera size={16} />
              گرفتن عکس
            </button>
          </div>
          <input
            ref={upload}
            type="file"
            hidden
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => {
              select(e.target.files?.[0])
              e.target.value = ''
            }}
          />
          <input
            ref={camera}
            type="file"
            hidden
            accept="image/*"
            capture="environment"
            onChange={(e) => {
              select(e.target.files?.[0])
              e.target.value = ''
            }}
          />
          <div className="form-divider" />
          <div className="form-section-title">
            <span>۲</span>
            <div>
              <h2>کمی بیشتر از درخت بگو</h2>
              <p>این اطلاعات، زمینه بررسی هستند؛ نه جایگزین آزمایش.</p>
            </div>
          </div>
          <div className="form-grid">
            <label>
              باغ
              <select value={orchard} onChange={(e) => setOrchard(e.target.value)} disabled={busy}>
                <option value="">بدون باغ مشخص</option>
                {ctx.data.orchards.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                    {o.is_sample ? ' (نمونه)' : ''}
                  </option>
                ))}
              </select>
            </label>
            <label>
              بخش درخت
              <select value={part} onChange={(e) => setPart(e.target.value)} disabled={busy}>
                {['برگ', 'میوه', 'شاخه و تنه', 'کل درخت', 'ریشه و طوقه'].map((p) => (
                  <option key={p}>{p}</option>
                ))}
              </select>
            </label>
          </div>
          <label className="full-label">
            توضیحات اختیاری
            <textarea
              placeholder="علائم از چه زمانی شروع شده؟ آخرین آبیاری، کود یا سم‌پاشی چه زمانی بوده؟"
              value={notes}
              maxLength={1000}
              rows={3}
              disabled={busy}
              onChange={(e) => setNotes(e.target.value)}
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
                می‌پذیرم تصویر پس از حذف اطلاعات مکانی فایل، برای سرویس تحلیل ارسال شود. نتیجه
                احتمالی است و جای تشخیص کارشناس را نمی‌گیرد.
              </span>
            </label>
          )}
          {error && (
            <div className="form-error" role="alert">
              {error}
              {error.includes('وارد حساب') && (
                <button className="text-button" onClick={ctx.openAuth}>
                  ورود به حساب
                  <ArrowLeft size={14} />
                </button>
              )}
            </div>
          )}
          <button
            className="button primary analysis-submit"
            disabled={!file || busy}
            onClick={() => {
              void analyze()
            }}
          >
            {busy ? (
              <Spinner
                label={IS_STANDALONE ? 'در حال ذخیره عکس…' : 'در حال ارسال و بررسی تصویر…'}
              />
            ) : (
              <>
                <Sparkles size={18} />
                {IS_STANDALONE ? 'ذخیره عکس و یادداشت' : 'بررسی تصویر'}
                <ArrowLeft size={17} />
              </>
            )}
          </button>
          {!IS_STANDALONE && (
            <div className="analysis-credit">
              <ShieldCheck size={13} />
              اعتبار باقی‌مانده: {fa(Math.max(0, ctx.data.usage.limit - ctx.data.usage.used))} بررسی
              · خطای سرویس اعتبار را کسر نمی‌کند.
            </div>
          )}
        </div>
        <aside className="analysis-sidebar">
          <section className="card photo-tips">
            <div className="tip-icon">
              <ZoomIn size={24} />
            </div>
            <h2>یک عکس بهتر، یک بررسی بهتر</h2>
            <CheckList
              items={[
                'در نور طبیعی و بدون فیلتر عکس بگیر.',
                'بخش آسیب‌دیده را از نزدیک و بدون تاری ثبت کن.',
                'برای برگ، پشت و روی آن را در بررسی‌های جدا بفرست.',
                'برای زمینه بیشتر، عکس کل درخت را هم نگه دار.',
              ]}
            />
            <button
              className="text-button"
              onClick={() => {
                const a = ctx.knowledge.articles.find((a) => a.id === 'sampling')
                if (a) ctx.openArticle(a)
              }}
            >
              راهنمای عکس و نمونه
              <ArrowLeft size={15} />
            </button>
          </section>
          {!IS_STANDALONE && (
            <section className="sample-report-card">
              <span className="tip-icon">
                <FileImage size={22} />
              </span>
              <h3>نتیجه چه شکلی است؟</h3>
              <p>
                مشاهدات، فرضیه‌های محتمل، بررسی‌های تکمیلی و قدم‌های کم‌خطر را در نمونه گزارش ببین.
              </p>
              <button
                className="button secondary"
                onClick={() => {
                  void sample()
                }}
                disabled={sampleBusy}
              >
                {sampleBusy ? (
                  <Spinner />
                ) : (
                  <>
                    مشاهده گزارش نمونه
                    <ArrowLeft size={15} />
                  </>
                )}
              </button>
              <small>نمونه نمایشی؛ بدون تحلیل عکس شما</small>
            </section>
          )}
          <div className="limitations">
            <CircleHelp size={18} />
            <div>
              <strong>از عکس چه چیزی نمی‌فهمیم؟</strong>
              <p>
                مقدار دقیق عناصر، شوری، سلامت ریشه پنهان و عامل قطعی بیماری نیاز به اندازه‌گیری یا
                آزمایش دارند.
              </p>
            </div>
          </div>
        </aside>
      </div>
    </>
  )
}
