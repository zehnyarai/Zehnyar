import { useEffect, useRef, useState } from 'react'
import { Gauge, KeyRound, ListChecks, PlugZap, Save, ShieldCheck, Trash2 } from 'lucide-react'
import { api, errorMessage, persianDate } from '../api'
import type { AppContext } from '../types'
import {
  DEFAULT_GROK_MODEL,
  freeModelsFor,
  providerKeyHint,
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
  providers?: Record<DirectProvider, ProviderState>
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
  const [status, setStatus] = useState<DirectStatus | null>(null)
  const [provider, setProvider] = useState<DirectProvider>('gemini')
  const [model, setModel] = useState('')
  const [probe, setProbe] = useState<ProbeResult[] | null>(null)
  const [listed, setListed] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [keyNote, setKeyNote] = useState('')

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
    setProvider(next)
    setProbe(null)
    setListed([])
    setError('')
    const saved = status?.providers?.[next]
    setModel(saved?.model || (next === 'grok' ? DEFAULT_GROK_MODEL : 'gemini-2.5-flash'))
    setKeyNote('')
    if (key.current) key.current.value = ''
  }

  async function call(path: string, options?: RequestInit) {
    setBusy(true)
    setError('')
    try {
      const next = await api<DirectStatus>(path, options)
      setStatus(next)
      setProvider(next.provider)
      setModel(next.model)
      await ctx.refresh()
      return true
    } catch (e) {
      setError(errorMessage(e))
      return false
    } finally {
      if (key.current) key.current.value = ''
      setKeyNote('')
      setBusy(false)
    }
  }

  async function save() {
    const value = key.current?.value.trim() ?? ''
    const ok = await call('/local/vision', {
      method: 'PUT',
      body: JSON.stringify({ provider, model, ...(value ? { key: value } : {}) }),
    })
    if (ok) ctx.notify('تنظیمات روی همین دستگاه ذخیره شد. حالا «آزمون اتصال» را بزنید.', 'success')
  }

  async function test() {
    const ok = await call('/local/vision/test', { method: 'POST' })
    ctx.notify(
      ok
        ? 'آزمون اتصال موفق شد؛ تحلیل روی این دستگاه کار می‌کند.'
        : 'آزمون اتصال انجام نشد؛ دلیل دقیق زیر دکمه‌ها نوشته شده است.',
      ok ? 'success' : 'error'
    )
  }

  async function fetchModels() {
    setBusy(true)
    setError('')
    try {
      const rows = await api<{ id: string }[]>('/local/vision/models')
      setListed(rows.map((r) => r.id))
      ctx.notify(`${rows.length} مدل برای این کلید پیدا شد.`, 'success')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  async function probeModels() {
    setBusy(true)
    setError('')
    setProbe(null)
    try {
      const response = await api<{ results: ProbeResult[] }>('/local/vision/probe', {
        method: 'POST',
        body: JSON.stringify({ models: suggestions(provider).map((m) => m.id) }),
      })
      setProbe(response.results)
      const first = response.results.find((r) => r.ok)
      ctx.notify(
        first ? `این مدل پاسخ داد؛ «${first.model}» انتخاب شد.` : 'هیچ‌کدام از مدل‌ها پاسخ نداد.',
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
    const ok = await call('/local/vision', { method: 'DELETE' })
    if (ok) ctx.notify('کلید از این دستگاه پاک شد.', 'success')
  }

  const saved = status?.providers?.[provider]
  const current = provider === status?.provider ? status : undefined
  return (
    <section className="card local-settings-card" aria-label="کلید مدل تحلیل">
      <h2>
        <KeyRound size={22} /> کلید سرویس تحلیل
        <Badge tone={current?.key_present ? 'green' : 'amber'}>
          {current?.key_present
            ? current.connection_ok
              ? 'اتصال آزموده شده'
              : 'ثبت شده؛ بدون آزمون'
            : 'ثبت نشده'}
        </Badge>
      </h2>
      <p>
        کلید را فقط اینجا ثبت کنید؛ کاربران در هیچ صفحه‌ای نام سرویس یا مدل را نمی‌بینند. کلید روی
        همین دستگاه می‌ماند و در فایل نصبی و پشتیبان قرار نمی‌گیرد.
      </p>
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
            onChange={(e) => setKeyNote(providerKeyHint(provider, e.target.value))}
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
            disabled={busy || !(current?.key_present ?? saved?.key_present)}
            onClick={() => void test()}
          >
            <PlugZap size={17} /> آزمون اتصال
          </button>
          <button
            className="button secondary"
            disabled={busy || !(current?.key_present ?? saved?.key_present)}
            onClick={() => void fetchModels()}
          >
            <ListChecks size={17} /> فهرست مدل‌های مجاز
          </button>
          <button
            className="button secondary"
            disabled={busy || !(current?.key_present ?? saved?.key_present)}
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
