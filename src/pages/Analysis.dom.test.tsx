// @vitest-environment jsdom
// Regression test for the bug the owner hit on 2026-10-13: the offline APK hid the
// "رضایت آگاهانه" checkbox while the analyze guard still demanded it, so pressing
// «تحلیل تصویر و بررسی احتمال آفت» could only ever answer with a consent error.
import 'fake-indexeddb/auto'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import Analysis from './Analysis'
import { eraseLocalData, localApi } from '../standalone'
import type { AppContext } from '../types'

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
      return localApi(path, options)
    },
  }
})

// A real JPEG magic header: the device layer validates the first bytes itself.
const image = new File(
  [new Uint8Array([255, 216, 255, 224, 0, 16, 74, 70, 73, 70, 0, 1])],
  'leaf.jpg',
  { type: 'image/jpeg' }
)
const text = () => document.body.textContent?.replace(/\s+/g, ' ') ?? ''
const screened = {
  title: 'برگ پسته',
  summary: 'لکه روشن روی برگ دیده می‌شود.',
  quality: 'نور کافی',
  is_pistachio: true,
  observations: ['لکه روی برگ یک'],
  hypotheses: [{ name: 'تنش محیطی', evidence: 'بدون بافت قارچی', next_step: 'پایش هفتگی' }],
  actions: ['برگ آلوده جدا شود'],
  needed_tests: ['آزمایش برگ'],
  follow_up_questions: [],
  urgency: 'medium',
  limitations: ['آزمایش انجام نشده'],
  nutrition_considerations: [],
  yield_quality_plan: [],
  monitoring_plan: ['عکس هفتگی'],
  knowledge_ids: ['sampling'],
}
const posts: string[] = []
let visionCalls = 0

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
      vision_configured: true,
      vision_provider: 'gemini',
      vision_model: 'gemini-3.8-flash',
      vision_verified: true,
      vision_checked_at: new Date().toISOString(),
      lab_ai_configured: true,
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

beforeEach(async () => {
  posts.length = 0
  visionCalls = 0
  const store = new Map<string, string>([
    [
      'pestino-direct-vision',
      JSON.stringify({
        model: 'gemini-3.8-flash',
        key: 'AIzaSyAnalysisDomExample1234',
        checked_at: new Date().toISOString(),
        ok: true,
        note: 'آزمون اتصال متن ساده',
      }),
    ],
  ])
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
  })
  // jsdom neither decodes images nor paints canvases, so the device photo pipeline
  // (EXIF-stripping re-encode) gets a deterministic stand-in here.
  class FakeImage {
    naturalWidth = 800
    naturalHeight = 600
    onload: (() => void) | null = null
    onerror: (() => void) | null = null
    set src(_value: string) {
      queueMicrotask(() => this.onload?.())
    }
  }
  vi.stubGlobal('Image', FakeImage)
  URL.createObjectURL = () => 'blob:fake-photo'
  URL.revokeObjectURL = () => {}
  HTMLCanvasElement.prototype.getContext = (() => ({
    fillStyle: '',
    fillRect: () => {},
    drawImage: () => {},
  })) as unknown as typeof HTMLCanvasElement.prototype.getContext
  HTMLCanvasElement.prototype.toDataURL = () => 'data:image/jpeg;base64,AAAA'
  const { setFetchImplementation } = await import('../visionDirect')
  setFetchImplementation((async (url: string) => {
    visionCalls += 1
    void url
    return new Response(
      JSON.stringify({
        candidates: [
          { finishReason: 'STOP', content: { parts: [{ text: JSON.stringify(screened) }] } },
        ],
      }),
      { status: 200 }
    )
  }) as unknown as typeof fetch)
  await eraseLocalData()
})
afterEach(async () => {
  cleanup()
  vi.unstubAllGlobals()
  const { setFetchImplementation } = await import('../visionDirect')
  setFetchImplementation(null)
})

describe('offline photo analysis (the owner’s exact flow)', () => {
  it('shows the consent box in the APK and screens the photo once it is ticked', async () => {
    const user = userEvent.setup()
    render(<Analysis ctx={ctx} initialFile={image} />)

    const box = await screen.findByRole('checkbox', { name: /اجازه می‌دهم/ })
    expect((box as HTMLInputElement).checked).toBe(false)
    expect(text()).toContain('کلید شخصی')
    expect(text()).toContain('بهبود محصولات گوگل')

    // Without consent: no photo leaves the phone and the owner is told exactly what to do.
    await user.click(screen.getByRole('button', { name: /تحلیل تصویر و بررسی احتمال آفت/ }))
    const alert = await screen.findByRole('alert')
    expect(alert.textContent).toContain('رضایت آگاهانه')
    await waitFor(() => expect(document.querySelector('.consent-check.attention')).toBeTruthy())
    expect(visionCalls).toBe(0)
    expect((await localApi<{ reports: unknown[] }>('/bootstrap')).reports).toEqual([])

    // With consent: the screening runs for real through the device key.
    await user.click(box)
    expect(document.querySelector('.consent-check.attention')).toBeNull()
    await user.click(screen.getByRole('button', { name: /تحلیل تصویر و بررسی احتمال آفت/ }))
    await waitFor(() => expect(ctx.openReport).toHaveBeenCalled())
    expect(visionCalls).toBe(1)
    const saved = (await localApi<{ reports: { data: { provider: string } }[] }>('/bootstrap'))
      .reports
    expect(saved[0].data.provider).toBe('gemini-direct-byo-key')
  })

  it('gives two free analyses, then asks for a Toman package and unlocks with a code', async () => {
    const user = userEvent.setup()
    render(<Analysis ctx={ctx} initialFile={image} />)
    // Consent stays on for the session, so this only ticks it when it is still off.
    const tick = async () => {
      const box = (await screen.findByRole('checkbox', {
        name: /اجازه می‌دهم/,
      })) as HTMLInputElement
      if (!box.checked) await user.click(box)
      return box
    }
    await tick()
    // Analysis 1 of 2 (free)
    await user.click(screen.getByRole('button', { name: /تحلیل تصویر و بررسی احتمال آفت/ }))
    await waitFor(() => expect(visionCalls).toBe(1))
    await waitFor(() => expect(text()).toContain('تحلیل رایگان باقی‌مانده: ۱ از ۲'))
    // Analysis 2 of 2 (free)
    await tick()
    await user.click(screen.getByRole('button', { name: /تحلیل تصویر و بررسی احتمال آفت/ }))
    await waitFor(() => expect(visionCalls).toBe(2))
    // The third one is refused: no model call, and the payment screen appears instead.
    await tick()
    await user.click(screen.getByRole('button', { name: /تحلیل تصویر و بررسی احتمال آفت/ }))
    await waitFor(() => expect(text()).toContain('دو تحلیل رایگان تمام شد'))
    expect(visionCalls).toBe(2)
    expect(text()).toContain('برای ادامه، یک بستهٔ تحلیل تهیه کنید')
    expect(
      (screen.getByRole('button', { name: /تحلیل تصویر و بررسی احتمال آفت/ }) as HTMLButtonElement)
        .disabled
    ).toBe(true)

    // The owner's activation code (generated on the owner's own device) unlocks 20 analyses.
    const { createActivationCode } = await import('../quota')
    const generated = createActivationCode({
      analyses: 20,
      today: new Date().toISOString().slice(0, 10),
      serial: 4242,
    })
    const codeInput = screen.getByLabelText(/کد فعال‌سازی/) as HTMLInputElement
    await user.type(codeInput, generated.code)
    expect(codeInput.value).toBe(generated.code)
    await user.click(screen.getByRole('button', { name: /فعال‌سازی تحلیل/ }))
    await waitFor(() =>
      expect(ctx.notify).toHaveBeenCalledWith(
        expect.stringContaining('۲۰ تحلیل به دستگاه شما اضافه شد'),
        'success'
      )
    )
    await waitFor(() =>
      expect(
        (
          screen.getByRole('button', {
            name: /تحلیل تصویر و بررسی احتمال آفت/,
          }) as HTMLButtonElement
        ).disabled
      ).toBe(false)
    )
    // And the paid analysis now really runs and spends a package credit, not a free one.
    await tick()
    await user.click(screen.getByRole('button', { name: /تحلیل تصویر و بررسی احتمال آفت/ }))
    await waitFor(() => expect(visionCalls).toBe(3))
    const quota = await localApi<{ credits: number; free_left: number }>('/local/quota')
    expect(quota.free_left).toBe(0)
    expect(quota.credits).toBe(19)
  })

  it('still saves the file without analysis when the owner only wants a record', async () => {
    const user = userEvent.setup()
    render(<Analysis ctx={ctx} initialFile={image} />)
    await user.click(await screen.findByRole('button', { name: /ذخیره پرونده بدون تحلیل/ }))
    await waitFor(async () =>
      expect((await localApi<{ reports: unknown[] }>('/bootstrap')).reports).toHaveLength(1)
    )
    const reports = (await localApi<{ reports: { data: { provider: string } }[] }>('/bootstrap'))
      .reports
    expect(reports[0].data.provider).toBe('local-storage')
    expect(visionCalls).toBe(0)
  })
})
