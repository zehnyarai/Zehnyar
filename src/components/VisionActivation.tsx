import { useRef, useState } from 'react'
import { Brain, Upload } from 'lucide-react'
import { api, checkImage, errorMessage } from '../api'
import type { AnalysisData, AppContext, Services } from '../types'
import { IS_STANDALONE } from '../config'
import { CheckList, InfoBanner, Spinner } from './ui'
import GeminiConfiguration from './GeminiConfiguration'

export default function VisionActivation({ ctx, allowed }: { ctx: AppContext; allowed: boolean }) {
  const input = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null),
    [part, setPart] = useState('برگ'),
    [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  const [response, setResponse] = useState<{
    image_response_received: boolean
    services: Services
    result: AnalysisData
    notice: string
  } | null>(null)
  const configured = !IS_STANDALONE && ctx.data.services.vision_configured
  async function test() {
    if (!allowed || !file || !configured) return
    if (!consent) {
      setError('ارسال تصویر و استفاده از سهمیه Google نیازمند تأیید شماست.')
      return
    }
    setBusy(true)
    setError('')
    setResponse(null)
    const body = new FormData()
    body.append('image', file)
    body.append('tree_part', part)
    body.append('consent', 'true')
    try {
      setResponse(await api('/admin/vision/test', { method: 'POST', body }))
      try {
        await ctx.refresh()
      } catch {
        ctx.notify('پاسخ آزمون دریافت شد؛ بازخوانی وضعیت سرور ممکن نشد.', 'error')
      }
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <GeminiConfiguration ctx={ctx} allowed={allowed} />
      <section className="reference-card vision-activation" aria-label="فعال‌سازی واقعی تحلیل عکس">
        <h2>
          <Brain size={22} /> فعال‌سازی واقعی تحلیل عکس
        </h2>
        <InfoBanner tone="warning">
          تنظیم کلید با پاسخ واقعی تصویر و اعتبار علمی فرق دارد. پایگاه دانش پسته، پشتوانه تفسیر مدل
          است؛ خودش عکس را تشخیص نمی‌دهد. در این پروژه مدل آفلاین آموزش‌دیده و اعتبارسنجی‌شده برای
          همه بخش‌های پسته وجود ندارد.
        </InfoBanner>
        <CheckList
          items={[
            IS_STANDALONE
              ? 'این نصب مستقل است؛ نشانی سرور تحلیل ندارد. اینترنت به‌تنهایی آن را وصل نمی‌کند.'
              : 'رابط آنلاین، عکس را به API همین سرور می‌فرستد؛ کلید در APK یا مرورگر کاربران قرار نمی‌گیرد.',
            configured
              ? 'تنظیم مدل و مجوز مصرف سهمیه موجود است؛ آزمون تصویر را انجام دهید.'
              : 'مدیر باید GEMINI_API_KEY و مدل مجاز را فقط در secret سرور قرار دهد و استفاده از سهمیه را تأیید کند. کلید را در چت نفرستید.',
            ctx.data.services.vision_verified
              ? 'یک پاسخ تصویری معتبر اخیر ثبت شده است؛ این نتیجه، دقت علمی اندازه‌گیری‌شده نیست.'
              : 'هنوز پاسخ تصویری معتبر اخیر برای تنظیمات فعلی تأیید نشده است.',
          ]}
        />
        <fieldset disabled={!allowed || busy || !configured}>
          <label>
            بخش درخت برای آزمون
            <select
              value={part}
              onChange={(e) => {
                setPart(e.target.value)
                setResponse(null)
              }}
            >
              {['برگ', 'میوه', 'شاخه و تنه', 'کل درخت', 'ریشه و طوقه', 'گل و جوانه'].map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <button className="button secondary" onClick={() => input.current?.click()}>
            <Upload size={17} />
            {file ? file.name : 'انتخاب عکس واقعی برای آزمون'}
          </button>
          <input
            ref={input}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0]
              e.target.value = ''
              if (!f) return
              const issue = checkImage(f)
              if (issue) {
                setError(issue)
                return
              }
              setFile(f)
              setResponse(null)
              setConsent(false)
              setError('')
            }}
          />
          <label className="consent-check">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            <span>
              با ارسال این تصویر به مدل و مصرف سهمیه بررسی‌شده حساب Google موافقم. رایگان بودن
              درخواست تضمین نمی‌شود. تصویر آزمون روی سرور ذخیره نمی‌شود و اعتبار کاربران کسر
              نمی‌شود.
            </span>
          </label>
          <button
            className="button primary"
            disabled={!file || !consent || busy}
            onClick={() => void test()}
          >
            {busy ? (
              <Spinner />
            ) : (
              <>
                <Brain size={18} /> اجرای آزمون واقعی تصویر
              </>
            )}
          </button>
        </fieldset>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        {response && (
          <div className="vision-test-result">
            <InfoBanner>{response.notice}</InfoBanner>
            <h3>{response.result.title}</h3>
            <p>{response.result.summary}</p>
            <h4>مشاهدات تصویر</h4>
            <CheckList items={response.result.observations} />
            <h4>حدود نتیجه</h4>
            <CheckList items={response.result.limitations ?? []} />
            <small>سرویس: {response.result.provider}؛ درصد دقت علمی اندازه‌گیری نشده است.</small>
          </div>
        )}
      </section>
    </>
  )
}
