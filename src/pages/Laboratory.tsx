import { useState } from 'react'
import {
  ArrowLeft,
  ChevronDown,
  Download,
  Droplets,
  FlaskConical,
  History,
  Save,
  Sprout,
  Trash2,
} from 'lucide-react'
import { errorMessage, fa, persianDate, downloadText, today } from '../api'
import type { AppContext } from '../types'
import type { LabInterpretation, LabKind, LabValues } from '../scientific'
import { interpretLab, parseLabValues, SOIL_FIELDS, WATER_FIELDS } from '../scientific'
import type { LabInput } from '../fieldwork'
import { useFieldRecords } from '../useFieldRecords'
import { Badge, CheckList, InfoBanner, Spinner } from '../components/ui'
import { SourceLinks } from '../components/scientific'
import LabAI from '../components/LabAI'
import { IS_STANDALONE } from '../config'

export default function Laboratory({ ctx }: { ctx: AppContext }) {
  const [kind, setKind] = useState<LabKind>('soil'),
    [inputs, setInputs] = useState<Record<string, string>>({})
  const [method, setMethod] = useState('unknown'),
    [date, setDate] = useState(today()),
    [depth, setDepth] = useState(''),
    [orchard, setOrchard] = useState(''),
    [notes, setNotes] = useState('')
  const [result, setResult] = useState<{ values: LabValues; report: LabInterpretation } | null>(
      null
    ),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [saved, setSaved] = useState(false)
  const [aiBusy, setAiBusy] = useState(false)
  const records = useFieldRecords('labs')
  function changeKind(next: LabKind) {
    setKind(next)
    setInputs({})
    setResult(null)
    setError('')
    setSaved(false)
    setMethod(next === 'water' ? 'water' : 'unknown')
  }
  function interpret() {
    try {
      const values = parseLabValues(kind, inputs)
      setResult({ values, report: interpretLab(kind, values, method) })
      setSaved(false)
      setError('')
    } catch (e) {
      setError(errorMessage(e))
      setResult(null)
    }
  }
  function invalidate() {
    setResult(null)
    setSaved(false)
  }
  async function save() {
    if (!result || busy) return
    setBusy(true)
    try {
      await records.save({
        kind,
        values: result.values,
        method,
        sample_date: date,
        depth,
        orchard_id: orchard || null,
        notes,
      })
      setSaved(true)
      ctx.notify(
        'پرونده آزمایش ذخیره شد؛ داده‌ها و روش سنجش را با آزمایشگاه کنترل کنید.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  function open(input: LabInput) {
    setKind(input.kind)
    setInputs(Object.fromEntries(Object.entries(input.values).map(([k, v]) => [k, String(v)])))
    setMethod(input.method)
    setDate(input.sample_date)
    setDepth(input.depth)
    setOrchard(input.orchard_id ?? '')
    setNotes(input.notes)
    setResult({
      values: input.values,
      report: interpretLab(input.kind, input.values, input.method),
    })
    setSaved(true)
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  return (
    <div className="reference-page laboratory-page">
      <div className="reference-heading">
        <span className="feature-icon amber">
          <FlaskConical size={28} />
        </span>
        <div>
          <h1>تحلیل خاک و آب</h1>
          <p>تفسیر آموزشی نتایج آزمایشگاه؛ برنامهٔ دقیق تغذیه را با کارشناس محلی مرور کنید</p>
        </div>
      </div>
      <div className="reference-tabs" role="tablist" aria-label="نوع آزمایش">
        <button
          role="tab"
          aria-selected={kind === 'soil'}
          className={kind === 'soil' ? 'active' : ''}
          onClick={() => changeKind('soil')}
        >
          <Sprout size={19} />
          آزمایش خاک
        </button>
        <button
          role="tab"
          aria-selected={kind === 'water'}
          className={kind === 'water' ? 'active' : ''}
          onClick={() => changeKind('water')}
        >
          <Droplets size={19} />
          آزمایش آب
        </button>
      </div>
      <section className="reference-card lab-input-card">
        <h2>ورود اطلاعات آزمایش {kind === 'soil' ? 'خاک' : 'آب'}</h2>
        <p className="section-description">
          خانهٔ خالی یعنی اندازه‌گیری نشده، نه صفر. اعداد را با واحد نمایش‌داده‌شده وارد کنید.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            interpret()
          }}
        >
          <fieldset disabled={busy || aiBusy}>
            <div className="lab-grid">
              {(kind === 'soil' ? SOIL_FIELDS : WATER_FIELDS).map((f) => (
                <label key={`${kind}-${f.key}`}>
                  {f.label}
                  {f.unit && <span dir="ltr"> ({f.unit})</span>}
                  <input
                    type="number"
                    step="any"
                    min={0}
                    max={f.max}
                    value={inputs[f.key] ?? ''}
                    placeholder="—"
                    onChange={(e) => {
                      setInputs((old) => ({ ...old, [f.key]: e.target.value }))
                      invalidate()
                    }}
                  />
                </label>
              ))}
            </div>
            <details
              className="sampling-details"
              open={method === 'unknown' && inputs.ec !== undefined}
            >
              <summary>
                <ChevronDown size={17} />
                روش آزمایش و اطلاعات نمونه — برای تفسیر معتبر مهم است
              </summary>
              <div className="reference-form-grid">
                <label>
                  روش اندازه‌گیری EC
                  <select
                    value={method}
                    onChange={(e) => {
                      setMethod(e.target.value)
                      invalidate()
                    }}
                  >
                    {kind === 'soil' ? (
                      <>
                        <option value="unknown">نامشخص؛ طبقه‌بندی ECe انجام نشود</option>
                        <option value="saturated">عصاره اشباع (ECe)</option>
                        <option value="1:5">عصاره ۱:۵</option>
                        <option value="1:2.5">عصاره ۱:۲٫۵</option>
                      </>
                    ) : (
                      <option value="water">آب — ECw بر حسب dS/m</option>
                    )}
                  </select>
                </label>
                <label>
                  تاریخ نمونه‌برداری
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => {
                      setDate(e.target.value)
                      setSaved(false)
                    }}
                    required
                  />
                </label>
                <label>
                  باغ
                  <select
                    value={orchard}
                    onChange={(e) => {
                      setOrchard(e.target.value)
                      setSaved(false)
                    }}
                  >
                    <option value="">بدون باغ مشخص</option>
                    {ctx.data.orchards.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  {kind === 'soil' ? 'عمق و محل نمونه (cm)' : 'محل نمونه آب'}
                  <input
                    value={depth}
                    maxLength={80}
                    placeholder={
                      kind === 'soil'
                        ? 'مثلاً ۰ تا ۳۰؛ طبق دستور آزمایشگاه'
                        : 'چاه / استخر / خروجی آبیاری'
                    }
                    onChange={(e) => {
                      setDepth(e.target.value)
                      setSaved(false)
                    }}
                  />
                </label>
              </div>
              <label className="full-label">
                روش استخراج عناصر / توضیحات آزمایشگاه
                <textarea
                  value={notes}
                  maxLength={1000}
                  rows={2}
                  placeholder="مثلاً فسفر Olsen، آهن و روی DTPA؛ روش نیتروژن، بافت، پایه و سابقه باغ"
                  onChange={(e) => {
                    setNotes(e.target.value)
                    setSaved(false)
                  }}
                />
              </label>
            </details>
            {error && (
              <div className="form-error" role="alert">
                {error}
              </div>
            )}
            <div className="center-actions">
              <button className="button primary" type="submit">
                <FlaskConical size={19} />
                تحلیل و توصیه
              </button>
            </div>
          </fieldset>
        </form>
      </section>
      {result && (
        <section className="reference-card lab-result" aria-label="نتیجه بررسی آزمایش">
          <header>
            <span className="feature-icon amber">
              <FlaskConical size={25} />
            </span>
            <div>
              <h2>نتیجه بررسی {kind === 'soil' ? 'خاک' : 'آب'}</h2>
              <p>براساس مقادیر واردشده — بدون اندازه‌گیری مستقل</p>
            </div>
            <Badge tone="amber">تفسیر آموزشی، نه نسخه</Badge>
          </header>
          {!!result.report.calculations.length && (
            <div className="calculation-grid">
              {result.report.calculations.map((c) => (
                <div key={c.label}>
                  <span>{c.label}</span>
                  <strong>{fa(c.value, 3)}</strong>
                  <p>{c.formula}</p>
                </div>
              ))}
            </div>
          )}
          {result.report.findings.map((f, i) => (
            <article className={`lab-finding ${f.tone}`} key={i}>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
              <small>مبنای بررسی: {f.basis}</small>
            </article>
          ))}
          <h3>قدم‌های بعدی</h3>
          <CheckList items={result.report.next} />
          <InfoBanner tone="warning">{result.report.limitations.join(' ')}</InfoBanner>
          <SourceLinks />
          <div className="analysis-main-actions">
            <button
              className="button primary"
              disabled={busy || aiBusy || saved}
              onClick={() => void save()}
            >
              {busy ? (
                <Spinner />
              ) : (
                <>
                  <Save size={17} />
                  {saved ? 'پرونده ذخیره شده' : 'ذخیره پرونده آزمایش'}
                </>
              )}
            </button>
            <button
              className="button secondary"
              onClick={() =>
                void downloadText(
                  `pestino-lab-${date}.txt`,
                  [
                    'پستینو — تفسیر آموزشی، نه نسخه',
                    JSON.stringify(result.values, null, 2),
                    ...result.report.findings.map((f) => `${f.title}\n${f.text}\n${f.basis}`),
                    ...result.report.calculations.map(
                      (c) => `${c.label}: ${c.value}\n${c.formula}`
                    ),
                    ...result.report.limitations,
                  ].join('\n\n')
                )
                  .then((saved) => ctx.notify(saved ? 'گزارش متنی آماده شد.' : 'ذخیره لغو شد.'))
                  .catch((e) => ctx.notify(errorMessage(e), 'error'))
              }
            >
              <Download size={17} />
              دریافت گزارش
            </button>
          </div>
        </section>
      )}
      <LabAI
        ctx={ctx}
        busy={aiBusy || busy}
        setBusy={setAiBusy}
        readSample={() => ({
          kind,
          values: parseLabValues(kind, inputs),
          method,
          sample_date: date,
          depth,
          orchard_id: orchard || null,
          notes,
        })}
        revision={JSON.stringify({ kind, inputs, method, date, depth, orchard, notes })}
      />
      <section className="reference-card lab-history">
        <h2>
          <History size={21} />
          پرونده‌های آزمایش قبلی
        </h2>
        <p className="section-description">
          {IS_STANDALONE
            ? 'فقط روی همین دستگاه؛ در فایل پشتیبان هم قرار می‌گیرند.'
            : 'پرونده‌های خصوصی حساب شما؛ برای دیگران نمایش داده نمی‌شوند.'}
        </p>
        {records.error && <InfoBanner tone="warning">{records.error}</InfoBanner>}
        {records.loading ? (
          <Spinner />
        ) : !records.records.length ? (
          <p className="empty-inline">هنوز آزمایشی ذخیره نشده است.</p>
        ) : (
          records.records.map((r) => (
            <div className="field-record-row" key={r.id}>
              <button onClick={() => open(r.data)}>
                <FlaskConical size={18} />
                <span>
                  <strong>آزمایش {r.data.kind === 'soil' ? 'خاک' : 'آب'}</strong>
                  <small>
                    {persianDate(r.data.sample_date, { year: 'numeric' })} ·{' '}
                    {fa(Object.keys(r.data.values).length)} مقدار
                  </small>
                </span>
                <ArrowLeft size={16} />
              </button>
              <button
                className="icon-button"
                aria-label="حذف پرونده آزمایش"
                onClick={() => {
                  if (confirm('پرونده آزمایش حذف شود؟'))
                    void records.remove(r.id).catch((e) => ctx.notify(errorMessage(e), 'error'))
                }}
              >
                <Trash2 size={17} />
              </button>
            </div>
          ))
        )}
      </section>
    </div>
  )
}
