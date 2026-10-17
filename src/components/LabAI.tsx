import { useCallback, useEffect, useState } from 'react'
import { Brain, Download, History, KeyRound, Trash2, Wallet } from 'lucide-react'
import { api, downloadText, errorMessage, fa, persianDate } from '../api'
import { IS_STANDALONE } from '../config'
import Paywall, { isQuotaError } from './Paywall'
import type { QuotaPayload } from '../quota'
import { validateField } from '../fieldwork'
import type { LabInput } from '../fieldwork'
import type { AppContext } from '../types'
import { Badge, CheckList, InfoBanner, Spinner } from './ui'

interface LabAssessment {
  id: string
  created_at: string
  input: LabInput
  units: Record<string, string>
  calculations: { key: string; label: string; value: number; formula: string }[]
  result: {
    title: string
    summary: string
    provider: string
    model: string
    disclaimer: string
    findings: string[]
    nutrition_considerations: string[]
    irrigation_considerations: string[]
    care_plan: string[]
    yield_quality_plan: string[]
    needed_tests: string[]
    limitations: string[]
    follow_up_questions: string[]
    knowledge_ids: string[]
  }
}
const SECTIONS = [
  ['findings', 'برداشت احتمالی از آزمایش'],
  ['nutrition_considerations', 'تغذیه و بررسی‌های لازم'],
  ['irrigation_considerations', 'آبیاری، شوری و زهکشی'],
  ['care_plan', 'مراقبت و پایش کم‌خطر'],
  ['yield_quality_plan', 'مدیریت شرطی عملکرد و کیفیت'],
  ['needed_tests', 'آزمایش‌های تکمیلی'],
  ['follow_up_questions', 'پرسش‌های تکمیلی'],
] as const

export default function LabAI({
  ctx,
  readSample,
  busy,
  setBusy,
  revision,
}: {
  ctx: AppContext
  readSample: () => LabInput
  busy: boolean
  setBusy: (busy: boolean) => void
  revision: string
}) {
  // Offline edition: enabled by the owner's own on-device Google key.
  const enabled = !!ctx.data.services.lab_ai_configured
  const base = IS_STANDALONE ? '/local/lab-analyses' : '/lab-analyses'
  const [consent, setConsent] = useState(false),
    [error, setError] = useState('')
  const [result, setResult] = useState<LabAssessment | null>(null)
  const [history, setHistory] = useState<LabAssessment[]>([])
  const [quota, setQuota] = useState<QuotaPayload | null>(null)
  const loadQuota = useCallback(async () => {
    if (!IS_STANDALONE) return
    try {
      setQuota(await api<QuotaPayload>('/local/quota'))
    } catch {
      /* the interpretation call enforces the quota even if this read fails */
    }
  }, [])
  useEffect(() => {
    void loadQuota()
  }, [loadQuota])
  const blocked = IS_STANDALONE && quota?.blocked === true
  useEffect(() => {
    setResult(null)
    setError('')
    setConsent(false)
  }, [revision])
  useEffect(() => {
    let active = true
    if (!ctx.data.user && !IS_STANDALONE) return
    void api<LabAssessment[]>(IS_STANDALONE ? '/local/lab-analyses' : '/lab-analyses')
      .then((rows) => {
        if (active) setHistory(rows)
      })
      .catch((e) => {
        if (active) setError(errorMessage(e))
      })
    return () => {
      active = false
    }
  }, [ctx.data.user?.id])
  async function analyze() {
    setError('')
    if (!enabled) {
      setError(
        IS_STANDALONE
          ? 'تفسیر هوشمند آزمایش روی این دستگاه فعال نیست؛ در «داده‌ها و پشتیبان» کلید شخصی Google خود را ثبت کنید. محاسبات آموزشی بالا بدون آن هم کار می‌کنند.'
          : 'Gemini هنوز در این نصب فعال نیست. کلید به‌صورت امن روی سرور تنظیم می‌شود، نه داخل APK یا چت.'
      )
      return
    }
    // Same as the photo scan: offline there is no account to sign in to.
    if (!IS_STANDALONE && (!ctx.data.user || ctx.data.user.is_demo)) {
      ctx.openAuth()
      return
    }
    if (!consent) {
      setError('برای ارسال آزمایش و زمینه باغ به Google، رضایت آگاهانه را تأیید کنید.')
      return
    }
    let sample: LabInput
    try {
      sample = validateField('labs', readSample())
    } catch (e) {
      setError(errorMessage(e))
      return
    }
    setBusy(true)
    setResult(null)
    try {
      const response = await api<LabAssessment>(base, {
        method: 'POST',
        body: JSON.stringify({ sample, consent: true }),
      })
      setResult(response)
      setHistory((rows) => [response, ...rows])
      try {
        await ctx.refresh()
      } catch {
        ctx.notify('گزارش دریافت شد؛ خواندن دوباره موجودی حساب ممکن نشد.', 'error')
      }
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
      void loadQuota()
    }
  }
  async function remove(row: LabAssessment) {
    if (!confirm('گزارش Gemini حذف شود؟ اعتبار تحلیل موفق بازگردانده نمی‌شود.')) return
    setBusy(true)
    try {
      await api(`${base}/${row.id}`, { method: 'DELETE' })
      setHistory((rows) => rows.filter((r) => r.id !== row.id))
      if (result?.id === row.id) setResult(null)
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <section className="reference-card lab-ai-card" aria-label="تفسیر آزمایش با Gemini">
      <h2>
        <Brain size={23} /> تفسیر آزمایش با Gemini
      </h2>
      <p className="section-description">
        این بخش جدا از محاسبات آموزشی است: نتایج واقعی واردشده، واحد، روش، تاریخ و زمینه باغ را به
        مدل می‌فرستد. هیچ تصویری در این بخش تحلیل نمی‌شود.{' '}
        {IS_STANDALONE &&
          'در نسخه مستقل، این فراخوانی از خودِ همین دستگاه و با کلید شخصی شما انجام می‌شود.'}
      </p>
      {!enabled && (
        <InfoBanner tone="warning">
          {IS_STANDALONE
            ? 'کلید شخصی Google روی این دستگاه ثبت نشده است. محاسبات SAR/RSC و تفسیر آموزشی بالا مستقل از مدل کار می‌کنند؛ برای تفسیر مدل، کلید را در «داده‌ها و پشتیبان» ثبت کنید.'
            : 'اتصال Gemini هنوز فعال نیست. محاسبات SAR/RSC و تفسیر آموزشی بالا مستقل از مدل کار می‌کنند. APK مستقل کلید یا اتصال Google ندارد.'}
        </InfoBanner>
      )}
      {enabled && (
        <InfoBanner>
          مدل تنظیم‌شده: <strong dir="ltr">{ctx.data.services.vision_model || 'Gemini'}</strong>؛
          تنظیم مدل به‌معنی اثبات اتصال یا اعتبار علمی آن نیست.{' '}
          {IS_STANDALONE
            ? 'سهمیهٔ رایگان Google از حساب شخصی خودتان مصرف می‌شود؛ پستینو فقط شمارش تحلیل‌های خودش را نگه می‌دارد و سهمیهٔ گوگل را نمی‌فروشد.'
            : 'هر تفسیر موفق یک نوبت از سهمیه مشترک عکس و آزمایش مصرف می‌کند.'}
        </InfoBanner>
      )}
      {IS_STANDALONE && quota && (
        <p className={blocked ? 'quota-chip blocked' : 'quota-chip'}>
          <Wallet size={15} />
          {blocked
            ? 'تحلیل‌های رایگان تمام شده؛ محاسبات و راهنماها بدون محدودیت کار می‌کنند.'
            : `تحلیل رایگان باقی‌مانده: ${fa(quota.free_left)} از ${fa(quota.free_limit)}`}
          {quota.credits > 0 && ` · بستهٔ خریداری‌شده: ${fa(quota.credits)}`}
        </p>
      )}
      {blocked && quota && <Paywall ctx={ctx} quota={quota} onUnlocked={loadQuota} />}
      <label className="consent-check">
        <input
          type="checkbox"
          checked={consent}
          disabled={!enabled || busy}
          onChange={(e) => setConsent(e.target.checked)}
        />
        <span>
          با ارسال مقادیر و یادداشت آزمایش و مشخصات مرتبط باغ به Google موافقم. نتیجه احتمالی و
          تأییدنشدهٔ محلی است؛ مصرف سهمیه یا هزینه API Google تابع حساب مالک است و رایگان‌بودن آن
          تضمین نمی‌شود.
        </span>
      </label>
      <button
        className="button primary"
        disabled={busy || blocked}
        onClick={() => {
          // A disabled button was the whole reason this card looked dead. Without a key the
          // button now stays alive and leads straight to the one-place setup.
          if (!enabled) {
            ctx.navigate('settings')
            return
          }
          void analyze()
        }}
      >
        {busy ? (
          <Spinner />
        ) : !enabled ? (
          <>
            <KeyRound size={18} /> ثبت کلید رایگان برای تفسیر
          </>
        ) : (
          <>
            <Brain size={18} /> دریافت تفسیر Gemini
          </>
        )}
      </button>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {result && (
        <article className="lab-ai-result">
          <header>
            <h3>{result.result.title}</h3>
            <Badge tone="amber">
              {IS_STANDALONE ? 'کلید شخصی شما' : 'Gemini'} · تفسیر احتمالی آزمایش
            </Badge>
          </header>
          <p>{result.result.summary}</p>
          <InfoBanner tone="warning">{result.result.disclaimer}</InfoBanner>
          <details>
            <summary>مقادیر اصلی این درخواست — ثبت‌شده توسط شما</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>پارامتر</th>
                    <th>مقدار</th>
                    <th>واحد</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.input.values).map(([key, value]) => (
                    <tr key={key}>
                      <td dir="ltr">{key}</td>
                      <td>{fa(value, 3)}</td>
                      <td dir="ltr">{result.units[key]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p>
              روش: {result.input.method} · تاریخ نمونه:{' '}
              {persianDate(result.input.sample_date, { year: 'numeric' })}
            </p>
          </details>
          {!!result.calculations.length && (
            <div className="calculation-grid">
              {result.calculations.map((c) => (
                <div key={c.key}>
                  <span>{c.label}</span>
                  <strong>{fa(c.value, 3)}</strong>
                  <p dir="ltr">{c.formula}</p>
                  <small>محاسبه سرور از اعداد واردشده؛ نه عدد ساخته‌شده توسط مدل</small>
                </div>
              ))}
            </div>
          )}
          <div className="care-columns">
            {SECTIONS.map(
              ([key, title]) =>
                result.result[key].length > 0 && (
                  <section key={key}>
                    <h3>{title}</h3>
                    <CheckList items={result.result[key]} />
                  </section>
                )
            )}
          </div>
          <h3>حدود نتیجه</h3>
          <CheckList items={result.result.limitations} />
          <div className="guide-chips">
            {ctx.knowledge.articles
              .filter((a) => result.result.knowledge_ids.includes(a.id))
              .map((a) => (
                <button key={a.id} onClick={() => ctx.openArticle(a)}>
                  {a.title}
                </button>
              ))}
          </div>
          <button
            className="button secondary"
            onClick={() =>
              void downloadText(
                `pestino-gemini-lab-${result.input.sample_date}.txt`,
                [
                  'پستینو — تفسیر احتمالی Gemini از آزمایش',
                  result.result.disclaimer,
                  JSON.stringify(result, null, 2),
                ].join('\n\n')
              ).catch((e) => ctx.notify(errorMessage(e), 'error'))
            }
          >
            <Download size={17} /> دریافت گزارش Gemini
          </button>
        </article>
      )}
      {!!history.length && (
        <div className="lab-ai-history">
          <h3>
            <History size={18} /> گزارش‌های Gemini قبلی
          </h3>
          {history.map((row) => (
            <div className="field-record-row" key={row.id}>
              <button disabled={busy} onClick={() => setResult(row)}>
                <span>
                  <strong>{row.result.title}</strong>
                  <small>
                    {persianDate(row.created_at)} · {row.result.model}
                  </small>
                </span>
              </button>
              <button
                className="icon-button"
                aria-label="حذف گزارش Gemini آزمایش"
                disabled={busy}
                onClick={() => void remove(row)}
              >
                <Trash2 size={17} />
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
