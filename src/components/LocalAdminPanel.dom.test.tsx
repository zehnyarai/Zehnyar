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
  it('lists every capability with its honest state and connects the model with the owner key', async () => {
    const user = userEvent.setup()
    render(<LocalAdminPanel ctx={ctx} />)
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'پنل مدیر (نسخه مستقل)' })).toBeTruthy()
    )
    const board = document.querySelectorAll('.capability-list li')
    const text = Array.from(board).map((li) => li.textContent ?? '')
    expect(text.some((t) => t.includes('تحلیل عکس برگ') && t.includes('نیازمند تنظیم'))).toBe(true)
    expect(text.some((t) => t.includes('SAR') && t.includes('فعال'))).toBe(true)
    expect(text.some((t) => t.includes('درگاه بانکی') && t.includes('در این نسخه ممکن نیست'))).toBe(
      true
    )
    expect(text.some((t) => t.includes('نسخه iPhone') && t.includes('در این نسخه ممکن نیست'))).toBe(
      true
    )
    expect(text.some((t) => t.includes('فایل نصبی اندروید') && t.includes('فعال'))).toBe(true)

    await user.type(screen.getByLabelText(/^مدل/), 'gemini-2.5-flash')
    await user.type(screen.getByLabelText(/^کلید API شخصی/), 'AIzaSyDomTestExampleKey123')
    await user.click(screen.getByRole('button', { name: /ذخیره روی این دستگاه/ }))
    await waitFor(() =>
      expect(calls.some((c) => c.url === '/local/vision' && c.method === 'PUT')).toBe(true)
    )
    const stored = JSON.stringify(localStorage.getItem('pestino-direct-vision'))
    expect(stored).toContain('AIzaSyDomTestExampleKey123')
    expect(document.body.textContent).not.toContain('AIzaSyDomTestExampleKey123')

    await user.click(screen.getByRole('button', { name: /آزمون اتصال/ }))
    await waitFor(() => expect(calls.some((c) => c.url === '/local/vision/test')).toBe(true))
    await waitFor(() => expect(document.body.textContent).toContain('آزمون اتصال متن ساده موفق شد'))
    await waitFor(() =>
      expect(
        Array.from(document.querySelectorAll('.capability-list li')).some(
          (li) =>
            (li.textContent ?? '').includes('تحلیل عکس برگ') &&
            (li.textContent ?? '').includes('فعال')
        )
      ).toBe(true)
    )
  })

  it('requires visual confirmation of the card, then records and deletes a manual receipt', async () => {
    const user = userEvent.setup()
    render(<LocalAdminPanel ctx={ctx} />)
    await waitFor(() => expect(document.querySelector('.local-admin-page')).toBeTruthy())
    await user.type(screen.getByLabelText('شماره کارت ۱۶ رقمی'), '9401 6524 7311 6063')
    await user.type(screen.getByLabelText('نام صاحب کارت'), 'احمد قرائی سلطان آبادی')
    await user.type(screen.getByLabelText('نام بانک'), 'بانک ملی ایران')
    await user.click(screen.getByRole('button', { name: /ذخیره کارت مقصد/ }))
    await waitFor(() =>
      expect(document.querySelector('.form-error')?.textContent).toContain('تطبیق')
    )
    expect(document.body.textContent).not.toContain('9401')

    await user.click(screen.getByLabelText(/تأیید می‌کنم شماره کارت/))
    await user.click(screen.getByRole('button', { name: /ذخیره کارت مقصد/ }))
    await waitFor(() => expect(document.body.textContent).toContain('کارت ثبت‌شده'))
    expect(document.body.textContent).toContain('9401 - 6524 - 7311 - 6063')

    await user.type(screen.getByLabelText('نام پرداخت‌کننده'), 'باغدار نمونه')
    await user.type(screen.getByLabelText('مبلغ (تومان)'), '990000')
    await user.click(screen.getByRole('button', { name: /ثبت در دفتر دریافتی‌ها/ }))
    await waitFor(() => expect(document.querySelector('.receipt-ledger')).toBeTruthy())
    const ledger = within(document.querySelector('.receipt-ledger') as HTMLElement)
    expect(ledger.getByText('باغدار نمونه')).toBeTruthy()
    expect(document.querySelector('.local-admin-page')?.textContent).toContain(
      'ثبت دستی، نه تأیید بانکی'
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
  it('opens the panel by default, offers to define a password, and asks for it afterwards', async () => {
    const user = userEvent.setup()
    const { default: CreditAdmin } = await import('../pages/CreditAdmin')
    render(<CreditAdmin ctx={ctx} />)
    // No password exists yet: the panel is reachable and the lock is offered, not forced.
    await waitFor(() => expect(document.querySelector('.local-admin-page')).toBeTruthy())
    expect(document.body.textContent).toContain('رمز مدیر را خودتان تعریف کنید')
    expect(document.body.textContent).toContain('قفل پنل مدیر: تعریف نشده')

    await user.type(screen.getByLabelText(/^رمز مدیر \(حداقل/), 'bagh-peste-1404')
    await user.type(screen.getByLabelText('تکرار رمز'), 'bagh-peste-1404')
    await user.type(screen.getByLabelText(/^راهنمای رمز/), 'سال تولد باغ')
    await user.click(screen.getByRole('button', { name: /ذخیره رمز مدیر/ }))
    await waitFor(() => expect(document.body.textContent).toContain('قفل پنل مدیر: فعال'))

    // Locking now hides the panel behind the owner's own password.
    await user.click(screen.getByRole('button', { name: /قفل کردن الان/ }))
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeTruthy()
    )
    expect(document.querySelector('.local-admin-page')).toBeNull()
    expect(document.body.textContent).toContain('راهنمای خودتان: سال تولد باغ')

    await user.type(screen.getByLabelText('رمز مدیر'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /باز کردن پنل مدیر/ }))
    await waitFor(() =>
      expect(document.querySelector('.form-error')?.textContent).toContain('رمز درست نیست')
    )
    expect(document.querySelector('.local-admin-page')).toBeNull()

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
