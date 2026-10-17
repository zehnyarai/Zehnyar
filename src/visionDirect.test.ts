import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  DEFAULT_DIRECT_MODEL,
  FREE_MODELS,
  FREE_TIER_NOTICE,
  listDirectModels,
  probeDirectModels,
  providerError,
  safeProviderMessage,
  DirectError,
  analyzePhotosDirect,
  clearDirectSettings,
  directReady,
  directSettings,
  generateDirect,
  interpretLabDirect,
  labCalculations,
  labUnits,
  sanitizeLabResult,
  sanitizePhotoResult,
  saveDirectSettings,
  setFetchImplementation,
  testDirectConnection,
  validKey,
  validModel,
} from './visionDirect'
import { EMPTY_CONTEXT } from './scientific'
import type { LabInput } from './fieldwork'

const store = new Map<string, string>()
beforeEach(() => {
  store.clear()
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
  })
  setFetchImplementation(null)
})

const geminiReply = (value: unknown) => ({
  candidates: [{ finishReason: 'STOP', content: { parts: [{ text: JSON.stringify(value) }] } }],
})
function stub(body: unknown, status = 200) {
  const calls: { url: string; init: RequestInit }[] = []
  setFetchImplementation((async (url: string, init: RequestInit) => {
    calls.push({ url, init })
    return new Response(typeof body === 'string' ? body : JSON.stringify(body), { status })
  }) as unknown as typeof fetch)
  return calls
}
const photo = {
  title: 'برگ پسته با لکه',
  summary: 'لکه‌های روشن روی سطح برگ دیده می‌شود.',
  quality: 'نور کافی، فوکوس متوسط',
  is_pistachio: true,
  observations: ['لکه روشن روی برگ یک'],
  hypotheses: [
    { name: 'تنش محیطی', evidence: 'لکه بدون بافت قارچی', next_step: 'پایش دو هفته‌ای' },
  ],
  actions: ['برگ‌های آلوده را جدا کنید'],
  needed_tests: ['آزمایش برگ'],
  follow_up_questions: ['آبیاری اخیر چگونه بود؟'],
  urgency: 'medium',
  limitations: ['آزمایش خاک انجام نشده'],
  nutrition_considerations: ['آزمایش برگ لازم است'],
  yield_quality_plan: ['یکنواختی آبیاری بررسی شود'],
  monitoring_plan: ['هفتگی عکس تازه'],
  knowledge_ids: ['sampling', 'invented-id'],
}

describe('device-direct vision (owner key)', () => {
  it('accepts plausible models and keys but rejects junk', () => {
    expect(validModel('models/gemini-3.1-pro-preview')).toBe('gemini-3.1-pro-preview')
    expect(validModel('gemini-2.5-flash')).toBe('gemini-2.5-flash')
    expect(validModel('gpt-4o')).toBeNull()
    expect(validModel('gemini-3.1-pro-preview; drop table')).toBeNull()
    expect(validKey('AIzaSyExampleExampleExample123')).toBe('AIzaSyExampleExampleExample123')
    expect(validKey('short')).toBeNull()
    expect(validKey('has space inside key value')).toBeNull()
  })
  it('stores the key only on the device and never reports it back', () => {
    expect(directReady()).toBe(false)
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    expect(directSettings().model).toBe('gemini-2.5-flash')
    expect(directReady()).toBe(true)
    saveDirectSettings('gemini-2.5-pro')
    expect(directSettings().key).toBe('AIzaSyExampleExampleExample123')
    expect(directSettings().model).toBe('gemini-2.5-pro')
    clearDirectSettings()
    expect(directSettings()).toEqual({
      provider: 'gemini',
      key: '',
      model: DEFAULT_DIRECT_MODEL,
      checked_at: null,
      ok: false,
      note: '',
    })
  })
  it('sends the key in a header only, never in the URL or body', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    const calls = stub(geminiReply({ ok: true }))
    await testDirectConnection()
    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'
    )
    expect(calls[0].url).not.toContain('AIza')
    const headers = calls[0].init.headers as Record<string, string>
    expect(headers['x-goog-api-key']).toBe('AIzaSyExampleExampleExample123')
    expect(String(calls[0].init.body)).not.toContain('AIza')
    expect(directSettings().ok).toBe(true)
  })
  it('refuses to call the provider without a key or with a bad model', async () => {
    const calls = stub(geminiReply({ ok: true }))
    await expect(generateDirect({ system: 's', schema: {}, payload: {} })).rejects.toThrow(
      DirectError
    )
    // An unusable model falls back to the default instead of staying broken.
    saveDirectSettings('gpt-4o', 'AIzaSyExampleExampleExample123')
    expect(directSettings().model).toBe(DEFAULT_DIRECT_MODEL)
    await expect(
      generateDirect({
        system: 's',
        schema: {},
        payload: {},
        settings: {
          provider: 'gemini',
          model: 'gpt-4o',
          key: 'AIzaSyExampleExampleExample123',
          checked_at: null,
          ok: false,
          note: '',
        },
      })
    ).rejects.toThrow('کلید یا نام مدل')
    expect(calls).toHaveLength(0)
  })
  it('reports connectivity failure instead of fabricating a result', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    setFetchImplementation((async () => {
      throw new TypeError('Failed to fetch')
    }) as unknown as typeof fetch)
    await expect(testDirectConnection()).rejects.toThrow('اتصال مستقیم از این دستگاه')
    expect(directSettings().ok).toBe(false)
  })
  it("surfaces Google's own reason without inventing output", async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    stub({ error: { message: 'API key not valid. Please pass a valid API key.' } }, 400)
    await expect(testDirectConnection()).rejects.toThrow('کلید API پذیرفته نشد')
    stub({ error: { message: 'Quota exceeded' } }, 429)
    await expect(testDirectConnection()).rejects.toThrow('سهمیهٔ این مدل تمام شده')
    // The failure reason is remembered on the device for later review.
    expect(directSettings().ok).toBe(false)
    expect(directSettings().note).toContain('سهمیه')
  })
  it('sanitizes photo screening: no confidence, no invented guide ids, non-pistachio locked down', () => {
    const result = sanitizePhotoResult(photo)
    expect(result.hypotheses[0].confidence).toBeNull()
    expect(result.knowledge_ids).toEqual(['sampling'])
    expect(result.provider).toBe('gemini-direct-byo-key')
    expect(result.limitations).toEqual(['آزمایش خاک انجام نشده'])
    const other = sanitizePhotoResult({ ...photo, is_pistachio: false })
    expect(other.hypotheses).toEqual([])
    expect(other.monitoring_plan).toEqual([])
    expect(other.actions).toHaveLength(1)
  })
  it('rejects dose numbers and uncalibrated accuracy percentages in photo output', () => {
    expect(() =>
      sanitizePhotoResult({ ...photo, actions: ['۲ میلی‌لیتر در لیتر سمپاشی کنید'] })
    ).toThrow('دوز')
    expect(() => sanitizePhotoResult({ ...photo, summary: 'این تحلیل ۹۵٪ دقت دارد.' })).toThrow(
      'دقت'
    )
    expect(() => sanitizePhotoResult({ ...photo, summary: 'احتمال آلودگی ۸۰٪ است.' })).toThrow(
      'دقت'
    )
  })
  it('runs the photo request with the images and the research context', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    const calls = stub(geminiReply(photo))
    const result = await analyzePhotosDirect(['data:image/jpeg;base64,/9j/4AAQSkZJRg=='], {
      ...EMPTY_CONTEXT,
      province: 'کرمان',
    })
    expect(result.is_pistachio).toBe(true)
    const body = JSON.parse(String(calls[0].init.body)) as {
      contents: { parts: { inlineData?: { data: string } }[] }[]
      generationConfig: { responseJsonSchema: unknown }
    }
    expect(body.contents[0].parts.some((p) => p.inlineData?.data === '/9j/4AAQSkZJRg==')).toBe(true)
    expect(body.generationConfig.responseJsonSchema).toBeTruthy()
  })
  it('computes SAR/RSC itself and never trusts the model for arithmetic', async () => {
    const water: LabInput = {
      kind: 'water',
      values: { ec: 2.4, sodium: 320, calcium: 96, magnesium: 36, bicarbonate: 244, carbonate: 0 },
      method: 'laboratory',
      sample_date: '2026-10-01',
      depth: '',
      orchard_id: null,
      notes: 'چاه عمیق',
    }
    const calculations = labCalculations(water)
    const sar = calculations.find((c) => c.key === 'sar')
    expect(sar?.value).toBeGreaterThan(4)
    expect(sar?.value).toBeLessThan(7.5)
    expect(calculations.find((c) => c.key === 'rsc')?.value).toBeLessThan(0)
    expect(labUnits(water).ec).toBe('dS/m')
    expect(labUnits(water).sodium).toBe('mg/L')
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    stub(
      geminiReply({
        title: 'آب چاه',
        summary: 'شوری و نسبت جذب سدیم بررسی شود.',
        findings: ['شوری در محدوده متوسط'],
        nutrition_considerations: [],
        irrigation_considerations: ['زهکشی و یکنواختی پخش بررسی شود'],
        care_plan: [],
        yield_quality_plan: [],
        needed_tests: ['آزمایش خاک مزرعه'],
        limitations: ['نمونه تک‌نقطه‌ای است'],
        follow_up_questions: [],
        knowledge_ids: ['salinity', 'nope'],
      })
    )
    const { result, units } = await interpretLabDirect(water, EMPTY_CONTEXT)
    expect(result.model).toBe('gemini-2.5-flash')
    expect(result.knowledge_ids).toEqual(['salinity'])
    expect(units.sodium).toBe('mg/L')
  })
  it('rejects numeric concentrations in lab prose while the table keeps the numbers', () => {
    expect(() =>
      sanitizeLabResult({
        title: 'آب',
        summary: 'شوری ۲۴۰۰ ppm اندازه‌گیری شده است.',
        findings: [],
        limitations: ['x'],
        knowledge_ids: [],
      })
    ).toThrow('دوز')
    const clean = sanitizeLabResult({
      title: 'آب',
      summary: 'نمونه تک‌نقطه‌ای است و تکرار لازم دارد.',
      findings: ['شوری نیازمند بررسی فصلی است'],
      limitations: [],
      knowledge_ids: [],
    })
    expect(clean.limitations).toHaveLength(1)
    expect(clean.findings).toHaveLength(1)
  })

  it('explains a paid-only model instead of blaming the owner (Gemini 3.1 Pro is not free)', async () => {
    // Google returns 429 with "limit: 0" for a model without free quota, which reads like
    // "you ran out of quota" even though the model is simply not on the free tier.
    const paid = providerError(
      429,
      JSON.stringify({
        error: {
          code: 429,
          status: 'RESOURCE_EXHAUSTED',
          message: 'Quota exceeded for metric: generate_content_free_tier_requests, limit: 0',
        },
      }),
      'gemini-3.1-pro-preview'
    )
    expect(paid.message).toContain('سهمیهٔ رایگان Google سهمیه ندارد')
    expect(paid.message).toContain('gemini-2.5-flash')
    const quota = providerError(
      429,
      JSON.stringify({ error: { message: 'RPD limit reached' } }),
      'gemini-2.5-flash'
    )
    expect(quota.message).toContain('نیمه‌شب')
    const forbidden = providerError(
      403,
      JSON.stringify({ error: { message: 'PERMISSION_DENIED' } }),
      'gemini-2.5-flash'
    )
    expect(forbidden.message).toContain('Generative Language API')
    const missing = providerError(
      404,
      JSON.stringify({ error: { message: 'models/x is not found' } }),
      'gemini-nope'
    )
    expect(missing.message).toContain('فهرست مدل‌های مجاز')
  })
  it('never leaks a key from a provider error body', () => {
    const message = safeProviderMessage(
      JSON.stringify({ error: { message: 'API key not valid: AIzaSyLeakedExampleKey123' } })
    )
    expect(message).not.toContain('AIzaSyLeakedExampleKey123')
    expect(message).toContain('***')
    expect(safeProviderMessage('not json AIzaSyLeakedExampleKey123')).not.toContain('AIzaSyLeaked')
  })
  it('keeps the default model inside the verified free list and excludes paid-only ones', () => {
    const ids = FREE_MODELS.map((m) => m.id)
    expect(ids).toContain(DEFAULT_DIRECT_MODEL)
    for (const paid of ['gemini-3.1-pro-preview', 'gemini-3.1-flash-image'])
      expect(ids).not.toContain(paid)
    expect(FREE_TIER_NOTICE).toContain('بهبود محصولات گوگل')
  })
  it('lists only models this key may actually call', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    const calls = stub({
      models: [
        { name: 'models/gemini-2.5-flash', supportedGenerationMethods: ['generateContent'] },
        { name: 'models/gemini-embedding-2', supportedGenerationMethods: ['embedContent'] },
        { name: 'models/gemini-3.6-flash', supportedGenerationMethods: ['generateContent'] },
        { name: 'models/bad name!', supportedGenerationMethods: ['generateContent'] },
      ],
    })
    const rows = await listDirectModels()
    expect(rows.map((r) => r.id)).toEqual(['gemini-2.5-flash', 'gemini-3.6-flash'])
    expect(calls[0].url).toContain('/models?pageSize=1000')
    expect(calls[0].url).not.toContain('AIza')
    expect((calls[0].init.headers as Record<string, string>)['x-goog-api-key']).toBe(
      'AIzaSyExampleExampleExample123'
    )
  })
  it('probes each candidate model and reports per-model reasons', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123')
    let call = 0
    setFetchImplementation((async () => {
      call += 1
      if (call === 1)
        return new Response(
          JSON.stringify({
            candidates: [{ finishReason: 'STOP', content: { parts: [{ text: '{"ok":true}' }] } }],
          }),
          { status: 200 }
        )
      return new Response(
        JSON.stringify({ error: { message: 'generate_content_free_tier_requests, limit: 0' } }),
        { status: 429 }
      )
    }) as unknown as typeof fetch)
    const rows = await probeDirectModels(['gemini-2.5-flash', 'gemini-3.1-pro-preview'])
    expect(rows[0].ok).toBe(true)
    expect(rows[0].detail).toContain('کار می‌کند')
    expect(rows[1].ok).toBe(false)
    expect(rows[1].detail).toContain('سهمیهٔ رایگان')
  })
})
