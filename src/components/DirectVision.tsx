import { useEffect, useRef, useState } from 'react'
import {
  Activity,
  Gauge,
  KeyRound,
  ListChecks,
  PlugZap,
  Save,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import { api, errorMessage, persianDate } from '../api'
import type { AppContext } from '../types'
import {
  DEFAULT_GROK_MODEL,
  freeModelsFor,
  providerKeyHint,
  cleanKey,
  type DirectProvider,
  type ProbeResult,
} from '../visionDirect'
import { Badge, InfoBanner, Spinner } from './ui'

interface ProviderState {
  key_present: boolean
  model: string
  checked_at: string | null
  ok: boolean
}

interface DirectStatus {
  provider: DirectProvider
  model: string
  key_present: boolean
  checked_at: string | null
  connection_ok: boolean
  note: string
  storage: string
  storage_warning?: string
  providers?: Record<DirectProvider, ProviderState>
  fallback?: boolean
}

interface DiagnosisRow {
  provider: DirectProvider
  key_present: boolean
  model: string
  ok: boolean
  status: number | null
  detail: string
  transport: string
}

const PROVIDERS: { id: DirectProvider; name: string; hint: string; key_help: string }[] = [
  {
    id: 'gemini',
    name: 'Gemini (Google)',
    hint: 'کلید رایگان از Google AI Studio',
    key_help: 'کلید Google با AIza شروع می‌شود. کلید را کامل و بدون فاصله بچسبانید.',
  },
  {
    id: 'grok',
    name: 'Grok (xAI)',
    hint: 'کلید از کنسول xAI',
    key_help:
      'کلید xAI با xai- شروع می‌شود. اگر آزمون شکست خورد، «فهرست مدل‌های مجاز» را بزنید؛ xAI مدل‌ها را بازنشسته می‌کند.',
  },
]

/** Suggestions shown under the model field, per provider. */
function suggestions(provider: DirectProvider) {
  return freeModelsFor(provider)
}

/**
 * Owner-only key panel for the offline edition. Both providers keep their own key on this
 * device; switching provider never deletes the other key. The panel never shows a stored
 * key again — only whether one exists.
 */
export default function DirectVision({ ctx }: { ctx: AppContext }) {
  const key = useRef<HTMLInputElement>(null)
  const drafts = useRef<Record<DirectProvider, string>>({ gemini: '', grok: '' })
  const [status, setStatus] = useState<DirectStatus | null>(null)
  const [provider, setProvider] = useState<DirectProvider>('gemini')
  const [model, setModel] = useState('')
  const [probe, setProbe] = useState<ProbeResult[] | null>(null)
  const [listed, setListed] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [keyNote, setKeyNote] = useState('')
  const [diagnosis, setDiagnosis] = useState<DiagnosisRow[] | null>(null)

  useEffect(() => {
    let active = true
    void api<DirectStatus>('/local/vision')
      .then((s) => {
        if (!active) return
        setStatus(s)
        setProvider(s.provider)
        setModel(s.model)
      })
      .catch((e) => active && setError(errorMessage(e)))
    return () => {
      active = false
      if (key.current) key.current.value = ''
    }
  }, [])

  function switchProvider(next: DirectProvider) {
    drafts.current[provider] = key.current?.value ?? ''
    setProvider(next)
    setProbe(null)
    setListed([])
    setError('')
    const saved = status?.providers?.[next]
    setModel(saved?.model || (next === 'grok' ? DEFAULT_GROK_MODEL : 'gemini-2.5-flash'))
    setKeyNote('')
    setDiagnosis(null)
    if (key.current) key.current.value = drafts.current[next]
    setKeyNote(drafts.current[next] ? 'کلید واردشده هنوز ذخیره نشده است.' : '')
  }

  async function call(path: string, options?: RequestInit) {
    setBusy(true)
    setError('')
    try {
      const next = await api<DirectStatus>(path, options)
      setStatus(next)
      setProvider(provider)
      setModel(next.providers?.[provider]?.model ?? next.model)
      await ctx.refresh()
      return true
    } catch (e) {
      // A network failure is not a key deletion; refresh the saved status independently.
      try {
        const latest = await api<DirectStatus>('/local/vision')
        setStatus(latest)
        if (path === '/local/vision/test') setModel(latest.providers?.[provider]?.model ?? model)
      } catch {
        /* Keep the useful original error and any pasted draft. */
      }
      setError(errorMessage(e))
      return false
    } finally {
      setBusy(false)
    }
  }

  async function persistCurrent(): Promise<boolean> {
    const value = key.current?.value.trim() ?? ''
    const ok = await call('/local/vision', {
      method: 'PUT',
      body: JSON.stringify({ provider, model, ...(value ? { key: value } : {}) }),
    })
    if (ok) {
      drafts.current[provider] = ''
      if (key.current) key.current.value = ''
      setKeyNote('')
    }
    // A failed write keeps the pasted key available; never make the owner paste it again.
    return ok
  }
  async function save() {
    if (await persistCurrent())
      ctx.notify(
        'کلید روی همین دستگاه ذخیره شد؛ بستن برنامه یا ناموفق بودن آزمون، آن را حذف نمی‌کند.',
        'success'
      )
  }
  async function ensureSaved(): Promise<boolean> {
    const value = key.current?.value.trim() ?? ''
    if (value || model !== status?.providers?.[provider]?.model) return persistCurrent()
    if (status?.providers?.[provider]?.key_present) return true
    setError('ابتدا کلید این سرویس را وارد و ذخیره کنید.')
    return false
  }

  /**
   * One button that tests both keys and says which one actually answered. This is the
   * shortest path out of "the connection test failed" for the owner.
   */
  async function diagnose() {
    if (key.current?.value.trim() && !(await ensureSaved())) return
    setBusy(true)
    setError('')
    setDiagnosis(null)
    try {
      const answer = await api<DirectStatus & { results: DiagnosisRow[] }>(
        '/local/vision/diagnose',
        { method: 'POST' }
      )
      setStatus(answer)
      setProvider(answer.provider)
      setModel(answer.model)
      setDiagnosis(answer.results)
      const working = answer.results.filter((r) => r.ok)
      await ctx.refresh()
      ctx.notify(
        working.length
          ? `آزمون انجام شد؛ ${working.map((r) => (r.provider === 'grok' ? 'Grok' : 'Gemini')).join(' و ')} پاسخ داد و تحلیل روی همان انجام می‌شود.`
          : 'هیچ‌کدام از دو سرویس پاسخ نداد؛ دلیل هر کدام در جدول پایین است.',
        working.length ? 'success' : 'error'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function toggleFallback(next: boolean) {
    setBusy(true)
    setError('')
    try {
      const answer = await api<DirectStatus>('/local/vision/fallback', {
        method: 'PUT',
        body: JSON.stringify({ fallback: next }),
      })
      setStatus(answer)
      await ctx.refresh()
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function test() {
    if (!(await ensureSaved())) return
    const ok = await call('/local/vision/test', {
      method: 'POST',
      body: JSON.stringify({ provider }),
    })
    ctx.notify(
      ok
        ? 'آزمون اتصال موفق شد؛ پاسخ متنی دریافت شد. قابلیت و کیفیت عکس با این آزمون تأیید نمی‌شود.'
        : 'آزمون اتصال انجام نشد؛ دلیل دقیق زیر دکمه‌ها نوشته شده است.',
      ok ? 'success' : 'error'
    )
  }

  async function fetchModels() {
    if (!(await ensureSaved())) return
    setBusy(true)
    setError('')
    try {
      const rows = await api<{ id: string }[]>(`/local/vision/models?provider=${provider}`)
      setListed(rows.map((r) => r.id))
      ctx.notify(`${rows.length} مدل برای این کلید پیدا شد.`, 'success')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function probeModels() {
    if (!(await ensureSaved())) return
    setBusy(true)
    setError('')
    setProbe(null)
    try {
      const response = await api<{ results: ProbeResult[] }>('/local/vision/probe', {
        method: 'POST',
        body: JSON.stringify({ provider, models: suggestions(provider).map((m) => m.id) }),
      })
      setProbe(response.results)
      const first = response.results.find((r) => r.ok)
      ctx.notify(
        first
          ? `این مدل پاسخ داد: «${first.model}». برای انتخاب، نامش را در فیلد مدل ذخیره کنید؛ کلید قبلی می‌ماند.`
          : 'هیچ‌کدام از مدل‌ها پاسخ نداد.',
        first ? 'success' : 'error'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    if (!confirm(`کلید ${provider === 'grok' ? 'Grok' : 'Gemini'} از این دستگاه پاک شود؟`)) return
    const ok = await call('/local/vision', { method: 'DELETE', body: JSON.stringify({ provider }) })
    if (ok) ctx.notify('کلید از این دستگاه پاک شد.', 'success')
  }

  const saved = status?.providers?.[provider]
  const current = saved ? { key_present: saved.key_present, connection_ok: saved.ok } : undefined
  return (
    <section className="card local-settings-card" aria-label="کلید مدل تحلیل">
      <h2>
        <KeyRound size={22} /> کلید سرویس تحلیل
        <Badge tone={current?.key_present ? 'green' : 'amber'}>
          {current?.key_present
            ? current.connection_ok
              ? 'اتصال آزموده شده'
              : saved?.checked_at
                ? 'کلید ذخیره است؛ آزمون ناموفق'
                : 'ثبت شده؛ بدون آزمون'
            : 'ثبت نشده'}
        </Badge>
      </h2>
      <p>
        هر دو کلید را می‌توانید ثبت کنید؛ تحلیل با هر سرویسی که جواب بدهد انجام می‌شود و اگر یکی قطع
        شد، برنامه خودکار سرویس دیگر را امتحان می‌کند. کلیدها فقط روی همین دستگاه می‌مانند و کاربران
        در هیچ صفحه‌ای نام سرویس یا مدل را نمی‌بینند.
      </p>
      <p className="key-persistence-note">
        کلید هر سرویس فقط یک‌بار ذخیره می‌شود. خالی بودن کادر رمز پس از ذخیره برای امنیت است و به
        معنی حذف کلید نیست. حذف برنامه/داده‌ها یا ابطال کلید در حساب سرویس استثناست؛ به وارد کردن
        دوباره در هر بار استفاده نیازی نیست.
      </p>
      {status?.storage_warning && <InfoBanner tone="warning">{status.storage_warning}</InfoBanner>}
      <label className="fallback-switch">
        <input
          type="checkbox"
          checked={status?.fallback !== false}
          disabled={busy}
          onChange={(e) => void toggleFallback(e.target.checked)}
        />
        <span>
          اگر سرویس فعال پاسخ نداد، خودکار سرویس دیگر امتحان شود
          {status ? ` — الان: ${status.provider === 'grok' ? 'Grok' : 'Gemini'}` : ''}
        </span>
      </label>
      <div className="provider-switch" role="tablist" aria-label="سرویس تحلیل">
        {PROVIDERS.map((p) => (
          <button
            key={p.id}
            type="button"
            role="tab"
            aria-selected={provider === p.id}
            className={provider === p.id ? 'active' : ''}
            disabled={busy}
            onClick={() => switchProvider(p.id)}
          >
            <strong>{p.name}</strong>
            <span>{status?.providers?.[p.id]?.key_present ? 'کلید ثبت شده' : p.hint}</span>
          </button>
        ))}
      </div>
      <fieldset disabled={busy}>
        <label>
          نام مدل
          <input
            list="pestino-direct-models"
            dir="ltr"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={provider === 'grok' ? DEFAULT_GROK_MODEL : 'gemini-2.5-flash'}
          />
        </label>
        <datalist id="pestino-direct-models">
          {[...new Set([...suggestions(provider).map((m) => m.id), ...listed])].map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
        <ul className="free-model-notes">
          {suggestions(provider)
            .slice(0, 3)
            .map((m) => (
              <li key={m.id}>
                <button type="button" className="text-button" onClick={() => setModel(m.id)}>
                  <span dir="ltr">{m.id}</span>
                </button>{' '}
                — {m.note}
              </li>
            ))}
        </ul>
        <label>
          کلید API {provider === 'grok' ? 'xAI' : 'Google'} (فقط روی همین دستگاه)
          <input
            ref={key}
            type="password"
            dir="ltr"
            autoComplete="off"
            spellCheck={false}
            onChange={(e) => {
              drafts.current[provider] = e.target.value
              const clean = cleanKey(e.target.value)
              const hint = providerKeyHint(provider, clean)
              setKeyNote(
                !clean
                  ? ''
                  : hint ||
                      `${clean.length} نویسه دریافت شد${clean.startsWith('xai-') || clean.startsWith('AIza') ? '؛ شروع کلید درست است' : '؛ شروع کلید ناشناس است'}`
              )
            }}
            placeholder={
              saved?.key_present
                ? 'ذخیره شده؛ برای تغییر مقدار تازه بگذارید'
                : provider === 'grok'
                  ? 'xai-…'
                  : 'AIza…'
            }
          />
          <small className="muted">
            {keyNote || PROVIDERS.find((p) => p.id === provider)?.key_help}
          </small>
        </label>
        <div className="local-settings-actions">
          <button className="button primary" disabled={busy} onClick={() => void save()}>
            <Save size={17} /> ذخیره
          </button>
          <button
            className="button secondary"
            disabled={busy || (!saved?.key_present && !keyNote)}
            onClick={() => void test()}
          >
            <PlugZap size={17} /> آزمون اتصال
          </button>
          <button className="button secondary" disabled={busy} onClick={() => void diagnose()}>
            <Activity size={17} /> آزمون هر دو سرویس
          </button>
          <button
            className="button secondary"
            disabled={busy || (!saved?.key_present && !keyNote)}
            onClick={() => void fetchModels()}
          >
            <ListChecks size={17} /> فهرست مدل‌های مجاز
          </button>
          <button
            className="button secondary"
            disabled={busy || (!saved?.key_present && !keyNote)}
            onClick={() => void probeModels()}
          >
            <Gauge size={17} /> آزمون مدل‌های پیشنهادی
          </button>
          <button
            className="button danger ghost"
            disabled={busy || !saved?.key_present}
            onClick={() => void remove()}
          >
            <Trash2 size={16} /> پاک‌کردن کلید
          </button>
          {busy && <Spinner />}
        </div>
      </fieldset>
      {error && (
        <div className="form-error" role="alert">
          <strong>دلیل:</strong> {error}
        </div>
      )}
      {probe && (
        <div className="table-scroll">
          <table className="probe-table">
            <thead>
              <tr>
                <th>مدل</th>
                <th>نتیجه</th>
                <th>دلیل</th>
              </tr>
            </thead>
            <tbody>
              {probe.map((row) => (
                <tr key={row.model} className={row.ok ? 'ok' : 'failed'}>
                  <td dir="ltr">
                    {row.model}{' '}
                    {row.ok && (
                      <button
                        type="button"
                        className="text-button"
                        onClick={() => {
                          setModel(row.model)
                          ctx.notify(`مدل «${row.model}» انتخاب شد؛ حالا ذخیره کنید.`, 'info')
                        }}
                      >
                        انتخاب
                      </button>
                    )}
                  </td>
                  <td>{row.ok ? 'کار کرد' : 'کار نکرد'}</td>
                  <td>{row.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {diagnosis && (
        <div className="table-scroll">
          <table className="probe-table" aria-label="نتیجهٔ آزمون هر دو سرویس">
            <thead>
              <tr>
                <th>سرویس</th>
                <th>کلید</th>
                <th>نتیجه</th>
                <th>دلیل دقیق</th>
              </tr>
            </thead>
            <tbody>
              {diagnosis.map((row) => (
                <tr key={row.provider} className={row.ok ? 'ok' : 'failed'}>
                  <td dir="ltr">{row.provider === 'grok' ? 'Grok (xAI)' : 'Gemini (Google)'}</td>
                  <td>{row.key_present ? 'ثبت شده' : 'ثبت نشده'}</td>
                  <td>
                    {row.ok ? 'کار کرد' : 'کار نکرد'}
                    {row.status ? ` · ${row.status}` : ''}
                  </td>
                  <td>{row.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">
            مسیر درخواست روی این دستگاه:{' '}
            {diagnosis[0]?.transport === 'native' ? 'HTTP بومی اندروید' : 'مرورگر'}
          </p>
        </div>
      )}
      {status && (
        <p className="muted">
          وضعیت: کلید {status.key_present ? 'ثبت شده' : 'ثبت نشده'} · مدل{' '}
          <span dir="ltr">{status.model || '—'}</span> · آزمون:{' '}
          {status.checked_at ? `${persianDate(status.checked_at)}` : 'انجام نشده'} · محل نگهداری:{' '}
          {status.storage}
          {status.note ? ` — ${status.note}` : ''}
        </p>
      )}
      <InfoBanner tone="warning">
        <ShieldCheck size={18} /> نتیجهٔ مدل، غربالگری احتمالی است؛ نه تشخیص قطعی و نه دوز. هیچ درصد
        دقت اندازه‌گیری‌شده‌ای برای آن ادعا نمی‌شود.
      </InfoBanner>
    </section>
  )
}
