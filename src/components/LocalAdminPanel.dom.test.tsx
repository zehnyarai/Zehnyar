// @vitest-environment jsdom
import 'fake-indexeddb/auto'
import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import LocalAdminPanel from './LocalAdminPanel'
import Credits from '../pages/Credits'
import { eraseLocalData } from '../standalone'
import type { AppContext } from '../types'

const ctx = {
  data: {
    user: {
      id: 'local-device',
      name: 'باغدار پستینو',
      email: null,
      role: 'user',
      is_demo: 0,
      subscription_until: null,
    },
    orchards: [],
    reports: [],
    tasks: [],
    usage: { used: 0, limit: 0, premium: false },
    services: {
      vision_configured: false,
      vision_provider: 'none',
      vision_model: '',
      vision_verified: false,
      lab_ai_configured: false,
      payment_configured: false,
      payment_sandbox: true,
      knowledge_version: '2026-10-12.1',
      knowledge_reviewed: false,
      weather_configured: false,
    },
    plans: [],
  },
  knowledge: { version: 'test', reviewed: false, articles: [] },
  refresh: vi.fn(async () => {}),
  navigate: vi.fn(),
  notify: vi.fn(),
  openArticle: vi.fn(),
  openReport: vi.fn(),
  openAuth: vi.fn(),
  openOrchard: vi.fn(),
  openTask: vi.fn(),
  startAnalysis: vi.fn(),
} as unknown as AppContext

const calls: { url: string; method: string }[] = []
// Components must see the standalone flag and the device API, exactly like the APK build.
vi.mock('../config', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../config')>()),
  IS_STANDALONE: true,
}))
vi.mock('../api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api')>()
  return {
    ...actual,
    api: async (path: string, options: RequestInit = {}) => {
      const { localApi } = await import('../standalone')
      calls.push({ url: path, method: options.method ?? 'GET' })
      return localApi(path, options)
    },
  }
})
const gemini = (payload: unknown) => ({
  candidates: [{ finishReason: 'STOP', content: { parts: [{ text: JSON.stringify(payload) }] } }],
})

beforeEach(async () => {
  calls.length = 0
  const store = new Map<string, string>()
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
  })
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input)
    const body = String(init?.body ?? '')
    const probe = body.includes('connection test')
    void url
    return new Response(
      JSON.stringify(gemini(probe ? { ok: true, model: 'gemini-2.5-flash' } : {})),
      {
        status: 200,
      }
    )
  })
  await eraseLocalData()
})
afterEach(() => {
  // No vitest globals here, so Testing Library does not clean up by itself.
  cleanup()
  vi.unstubAllGlobals()
})

describe('offline owner panel (real DOM, real device-storage layer)', () => {
  it('connects the analysis service with the owner key and proves it with a text call', async () => {
    const user = userEvent.setup()
    render(<LocalAdminPanel ctx={ctx} />)
    await waitFor(() => expect(screen.getByRole('heading', { name: 'پنل مدیر' })).toBeTruthy())

    await user.type(screen.getByLabelText('نام مدل'), 'gemini-2.5-flash')
    await user.type(screen.getByLabelText(/^کلید API Google/), 'AIzaSyDomTestExampleKey123')
    await user.click(screen.getByRole('button', { name: 'ذخیره' }))
    await waitFor(() =>
      expect(calls.some((c) => c.url === '/local/vision' && c.method === 'PUT')).toBe(true)
    )
    const stored = JSON.stringify(localStorage.getItem('pestino-direct-vision'))
    expect(stored).toContain('AIzaSyDomTestExampleKey123')
    expect(document.body.textContent).not.toContain('AIzaSyDomTestExampleKey123')

    await user.click(screen.getByRole('button', { name: /آزمون اتصال/ }))
    await waitFor(() => expect(calls.some((c) => c.url === '/local/vision/test')).toBe(true))
    await waitFor(() => expect(document.body.textContent).toContain('آزمون اتصال متن ساده موفق شد'))
    expect(document.body.textContent).not.toMatch(/اکانت|حساب گوگل|Google AI Studio/)
  })

  it('offers only free Gemini models and explains why a paid one fails', async () => {
    const user = userEvent.setup()
    vi.stubGlobal('fetch', async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/models?'))
        return new Response(
          JSON.stringify({
            models: [
              { name: 'models/gemini-2.5-flash', supportedGenerationMethods: ['generateContent'] },
              {
                name: 'models/gemini-3.1-pro-preview',
                supportedGenerationMethods: ['generateContent'],
              },
            ],
          }),
          { status: 200 }
        )
      // Google answers a paid-only model on a free key with 429 and "limit: 0".
      if (url.includes('gemini-3.1-pro-preview'))
        return new Response(
          JSON.stringify({ error: { message: 'generate_content_free_tier_requests, limit: 0' } }),
          { status: 429 }
        )
      return new Response(JSON.stringify(gemini({ ok: true, model: 'gemini-2.5-flash' })), {
        status: 200,
      })
    })
    render(<LocalAdminPanel ctx={ctx} />)
    await waitFor(() => expect(screen.getByRole('heading', { name: 'پنل مدیر' })).toBeTruthy())
    const options = Array.from(document.querySelectorAll('#pestino-direct-models option')).map(
      (o) => o.getAttribute('value') ?? ''
    )
    expect(options).toContain('gemini-2.5-flash')
    expect(options).not.toContain('gemini-3.1-pro-preview')
    expect(document.body.textContent).toContain('کلید رایگان از Google AI Studio')

    await user.type(screen.getByLabelText(/^کلید API Google/), 'AIzaSyDomFreeTierExample1234')
    await user.click(screen.getByRole('button', { name: 'ذخیره' }))
    await waitFor(() => expect(calls.some((c) => c.url === '/local/vision')).toBe(true))

    await user.click(screen.getByRole('button', { name: /فهرست مدل‌های مجاز/ }))
    await waitFor(() => expect(calls.some((c) => c.url === '/local/vision/models')).toBe(true))

    await user.click(screen.getByRole('button', { name: /آزمون مدل‌های پیشنهادی/ }))
    await waitFor(() => expect(calls.some((c) => c.url === '/local/vision/probe')).toBe(true))
    await waitFor(() =>
      expect(document.querySelector('.probe-table tbody tr.ok')?.textContent ?? '').toContain(
        'کار کرد'
      )
    )
    const rows = Array.from(document.querySelectorAll('.probe-table tbody tr'))
    expect(rows.length).toBeGreaterThan(1)
    expect(rows.every((r) => (r.textContent ?? '').includes('کار کرد'))).toBe(true)
  })

  it('keeps the owner card, records a manual receipt and deletes it', async () => {
    const user = userEvent.setup()
    render(<LocalAdminPanel ctx={ctx} />)
    await waitFor(() => expect(document.querySelector('.local-admin-page')).toBeTruthy())
    // The owner's real card ships seeded on the device.
    await waitFor(() => expect(document.body.textContent).toContain('9401 - 6524 - 7311 - 6063'))
    await user.clear(screen.getByLabelText('شماره کارت ۱۶ رقمی'))
    await user.type(screen.getByLabelText('شماره کارت ۱۶ رقمی'), '9401 6524 7311 6063')
    await user.clear(screen.getByLabelText('نام صاحب کارت'))
    await user.type(screen.getByLabelText('نام صاحب کارت'), 'احمد قرائی سلطان آبادی')
    await user.type(screen.getByLabelText('نام بانک (اختیاری)'), 'بانک ملی ایران')
    await user.click(screen.getByRole('button', { name: /ذخیره کارت مقصد/ }))
    await waitFor(() =>
      expect(document.querySelector('.form-error')?.textContent).toContain('تطبیق')
    )

    await user.click(screen.getByLabelText(/تأیید می‌کنم شماره کارت/))
    await user.click(screen.getByRole('button', { name: /ذخیره کارت مقصد/ }))
    await waitFor(() => expect(document.querySelector('.form-error')).toBeNull(), { timeout: 3000 })
    await waitFor(() => expect(document.body.textContent).toContain('9401 - 6524 - 7311 - 6063'))

    await user.type(screen.getByLabelText('نام پرداخت‌کننده'), 'باغدار نمونه')
    await user.type(screen.getByLabelText('مبلغ (تومان)'), '4900000')
    await user.click(screen.getByRole('button', { name: /ثبت در دفتر دریافتی‌ها/ }))
    await waitFor(() => expect(document.querySelector('.receipt-ledger')).toBeTruthy())
    const ledger = within(document.querySelector('.receipt-ledger') as HTMLElement)
    expect(ledger.getByText('باغدار نمونه')).toBeTruthy()
    expect(document.querySelector('.local-admin-page')?.textContent).toContain(
      'این دفتر ثبت دستی است، نه تأیید بانکی خودکار.'
    )

    await user.click(screen.getByRole('button', { name: /حذف دریافت باغدار نمونه/ }))
    await waitFor(() => expect(document.querySelector('.receipt-ledger')).toBeNull())
  })

  it('shows the manual transfer notice on the credits page and hides the server receipt flow', async () => {
    const { localApi } = await import('../standalone')
    await localApi('/local/billing', {
      method: 'PUT',
      body: JSON.stringify({
        card_number: '9401 6524 7311 6063',
        holder: 'احمد قرائی سلطان آبادی',
        bank: 'بانک ملی ایران',
        confirmed: true,
      }),
    })
    render(<Credits ctx={ctx} />)
    // The card arrives with the async bootstrap, so wait on the content, not the element.
    await waitFor(() =>
      expect(document.querySelector('.bank-card-display')?.textContent).toContain(
        '9401-6524-7311-6063'
      )
    )
    await waitFor(() =>
      expect(document.body.textContent).toContain('حالت دریافت دستی (بدون درگاه بانکی)')
    )
    const receiptButton = Array.from(document.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('ثبت رسید و درخواست اعتبار')
    )
    expect(receiptButton === undefined || receiptButton.closest('[hidden]')).toBeTruthy()
    expect(document.body.textContent).toContain('رفتن به دفتر دریافت در پنل مدیر')
  })
})

describe('admin gate protects the owner panel without ever locking the owner out', () => {
  it('ships a default owner password, then lets the owner replace it', async () => {
    const user = userEvent.setup()
    const { default: CreditAdmin } = await import('../pages/CreditAdmin')
    render(<CreditAdmin ctx={ctx} />)
    // First launch: a default password is seeded, so the panel is protected at once.
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeTruthy()
    )
    expect(document.body.textContent).toContain('رمز پیش‌فرض مالک')

    await user.type(screen.getByLabelText('رمز مدیر'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /باز کردن پنل مدیر/ }))
    await waitFor(() =>
      expect(document.querySelector('.form-error')?.textContent).toContain('رمز درست نیست')
    )
    expect(document.querySelector('.local-admin-page')).toBeNull()

    await user.type(screen.getByLabelText('رمز مدیر'), 'Pestino1404')
    await user.click(screen.getByRole('button', { name: /باز کردن پنل مدیر/ }))
    await waitFor(() => expect(document.querySelector('.local-admin-page')).toBeTruthy())
    expect(document.body.textContent).toContain('قفل پنل مدیر: فعال')

    // Replace the default with the owner's own password.
    await user.click(screen.getByRole('button', { name: /تغییر یا حذف رمز/ }))
    await user.type(screen.getByLabelText('رمز تازه'), 'bagh-peste-1404')
    await user.type(screen.getByLabelText('تکرار رمز تازه'), 'bagh-peste-1404')
    await user.clear(screen.getByLabelText(/^راهنمای رمز/))
    await user.type(screen.getByLabelText(/^راهنمای رمز/), 'سال تولد باغ')
    await user.click(screen.getByRole('button', { name: /جایگزینی رمز/ }))
    await waitFor(() => expect(document.body.textContent).toContain('قفل پنل مدیر: فعال'))

    await user.click(screen.getByRole('button', { name: /قفل کردن الان/ }))
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeTruthy()
    )
    expect(document.querySelector('.local-admin-page')).toBeNull()
    expect(document.body.textContent).toContain('راهنمای خودتان: سال تولد باغ')

    await user.type(screen.getByLabelText('رمز مدیر'), 'bagh-peste-1404')
    await user.click(screen.getByRole('button', { name: /باز کردن پنل مدیر/ }))
    await waitFor(() => expect(document.querySelector('.local-admin-page')).toBeTruthy())
  })

  it('lets a forgetful owner drop the lock with a typed confirmation, keeping the data', async () => {
    const user = userEvent.setup()
    const { setAdminPassword } = await import('../localAccess')
    const { localApi } = await import('../standalone')
    await localApi('/local/billing', {
      method: 'PUT',
      body: JSON.stringify({
        card_number: '9401 6524 7311 6063',
        holder: 'احمد قرائی سلطان آبادی',
        bank: 'بانک ملی ایران',
        confirmed: true,
      }),
    })
    await setAdminPassword('bagh-peste-1404')
    // Defining the password unlocks the current session, so lock it to test recovery.
    const { lockNow } = await import('../localAccess')
    lockNow()
    const { default: CreditAdmin } = await import('../pages/CreditAdmin')
    render(<CreditAdmin ctx={ctx} />)
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeTruthy()
    )
    await user.click(screen.getByRole('button', { name: 'رمز را فراموش کرده‌ام' }))
    await waitFor(() => expect(document.body.textContent).toContain('قفل مدیر را بردارید'))
    await user.type(screen.getByLabelText(/برای تأیید، عبارت/), 'چیز دیگری')
    await user.click(screen.getByRole('button', { name: /برداشتن قفل/ }))
    await waitFor(() =>
      expect(document.querySelector('.form-error')?.textContent).toContain('دقیقاً')
    )
    await user.clear(screen.getByLabelText(/برای تأیید، عبارت/))
    await user.type(screen.getByLabelText(/برای تأیید، عبارت/), 'حذف رمز مدیر')
    await user.click(screen.getByRole('button', { name: /برداشتن قفل/ }))
    await waitFor(() => expect(document.querySelector('.local-admin-page')).toBeTruthy())
    const view = await localApi<{ card: { card_number: string } | null }>('/local/billing')
    expect(view.card?.card_number).toBe('9401652473116063')
  })

  it('hides the full card number on the credits page while the panel is locked', async () => {
    const { setAdminPassword, lockNow } = await import('../localAccess')
    const { localApi } = await import('../standalone')
    await localApi('/local/billing', {
      method: 'PUT',
      body: JSON.stringify({
        card_number: '9401 6524 7311 6063',
        holder: 'احمد قرائی سلطان آبادی',
        bank: 'بانک ملی ایران',
        confirmed: true,
      }),
    })
    await setAdminPassword('bagh-peste-1404')
    lockNow()
    render(<Credits ctx={ctx} />)
    await waitFor(() => expect(document.querySelector('.bank-card-display')).toBeTruthy())
    await waitFor(() =>
      expect(document.querySelector('.bank-card-display')?.textContent).toContain('6063')
    )
    const shown = document.querySelector('.bank-card-display')?.textContent ?? ''
    expect(shown).not.toContain('9401 - 6524')
    expect(shown).toContain('••••')
  })
})
