import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  DEFAULT_DIRECT_MODEL,
  FREE_MODELS,
  FREE_TIER_NOTICE,
  listDirectModels,
  probeDirectModels,
  providerError,
  safeProviderMessage,
  connectionFailure,
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
  directFailureMessage,
  preferGrokModel,
  providerKeyHint,
  providerStatus,
  diagnoseProviders,
  setFallback,
  fallbackEnabled,
  anyProviderReady,
  DEFAULT_GROK_MODEL,
  GROK_MODELS,
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
    // Invisible marks and line breaks from a chat app are cleaned, not treated as junk.
    expect(validKey('  xai-ExampleExampleKey123\u200f\n')).toBe('xai-ExampleExampleKey123')
    expect(validKey('AIzaSyExampleExampleExample123\u202a')).toBe('AIzaSyExampleExampleExample123')
    expect(validKey('xai-abc def-ExampleKey123')).toBe('xai-abcdef-ExampleKey123')
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
      fallback: true,
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

describe('xAI Grok provider (owner key)', () => {
  const grokReply = (value: unknown) => ({
    choices: [
      { finish_reason: 'stop', message: { role: 'assistant', content: JSON.stringify(value) } },
    ],
  })
  it('keeps a separate Grok key and switches the active provider without losing Gemini', () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123', 'gemini')
    saveDirectSettings('grok-4', 'xai-ExampleExampleKey123', 'grok')
    expect(directSettings().provider).toBe('grok')
    expect(directSettings().key).toBe('xai-ExampleExampleKey123')
    expect(directSettings().model).toBe(DEFAULT_GROK_MODEL)
    const slots = JSON.parse(store.get('pestino-direct-vision') ?? '{}').slots
    expect(slots.gemini.key).toBe('AIzaSyExampleExampleExample123')
    expect(slots.grok.key).toBe('xai-ExampleExampleKey123')
  })
  it('calls api.x.ai with a bearer key and image_url parts, never putting the key in the body', async () => {
    saveDirectSettings('grok-4', 'xai-ExampleExampleKey123', 'grok')
    const calls = stub(grokReply(photo))
    const result = await analyzePhotosDirect(['data:image/jpeg;base64,AAAA'], {
      ...EMPTY_CONTEXT,
    })
    expect(result.summary).toContain('لکه')
    expect(calls).toHaveLength(1)
    expect(calls[0].url).toBe('https://api.x.ai/v1/chat/completions')
    expect(calls[0].url).not.toContain('xai-')
    const headers = calls[0].init.headers as Record<string, string>
    expect(headers['Authorization']).toBe('Bearer xai-ExampleExampleKey123')
    const body = JSON.parse(String(calls[0].init.body)) as {
      model: string
      messages: { content: unknown }[]
    }
    expect(body.model).toBe('grok-4.7')
    expect(JSON.stringify(body)).not.toContain('xai-ExampleExampleKey123')
    expect(JSON.stringify(body)).toContain('data:image/jpeg;base64,AAAA')
  })
  it('rejects a model from the wrong provider instead of calling it', () => {
    saveDirectSettings('grok-4', 'xai-ExampleExampleKey123', 'grok')
    expect(validModel('gemini-2.5-flash', 'grok')).toBeNull()
    expect(validModel('grok-4', 'grok')).toBe('grok-4')
  })
})

describe('neutral failure copy for farmers', () => {
  it('never names a provider or a model in a message shown to the user', () => {
    const cases = [
      new DirectError('کلید xAI پذیرفته نشد (پاسخ سرویس: invalid key)', 401),
      new DirectError('مدل «gemini-2.5-flash» روی سهمیهٔ رایگان Google سهمیه ندارد', 429),
      new DirectError('اتصال مستقیم از این دستگاه به xAI برقرار نشد.', 0),
      new DirectError('سرور xAI خطا داد', 503),
    ]
    for (const error of cases) {
      const text = directFailureMessage(error)
      expect(text).not.toMatch(/xAI|Google|Gemini|grok|مدل|کلید|API|api\./i)
      expect(text.length).toBeGreaterThan(20)
    }
    expect(directFailureMessage(new Error('anything else'))).toBe('')
  })
})

describe('xAI model names stay current and self-heal', () => {
  it('never ships a retired Grok model as the default or a suggestion', () => {
    // xAI retired grok-4 / grok-4-fast / grok-3 on 2026-05-15; a stale name looked
    // exactly like a broken key, so the default must be a model that still answers.
    expect(DEFAULT_GROK_MODEL).toBe('grok-4.7')
    expect(['grok-4', 'grok-4-fast', 'grok-3']).not.toContain(DEFAULT_GROK_MODEL)
    expect(GROK_MODELS.map((m) => m.id)).toContain(DEFAULT_GROK_MODEL)
    expect(GROK_MODELS.every((m) => !['grok-4', 'grok-4-fast', 'grok-3'].includes(m.id))).toBe(true)
  })
  it('moves a retired id saved by an older build onto the current default', () => {
    saveDirectSettings('grok-4', 'xai-ExampleExampleKey123', 'grok')
    expect(directSettings().model).toBe(DEFAULT_GROK_MODEL)
    saveDirectSettings('grok-4.6', 'xai-ExampleExampleKey123', 'grok')
    expect(directSettings().model).toBe('grok-4.6')
  })
  it('picks the newest usable chat model from the account list, not an image model', () => {
    const ids = [
      'grok-imagine-image-quality',
      'grok-4.3',
      'grok-4.6',
      'grok-4.7',
      'grok-4.20-0309-non-reasoning',
      'grok-voice-1',
    ]
    expect(preferGrokModel(ids)).toBe('grok-4.7')
    expect(preferGrokModel(['grok-4.3', 'grok-4.5'])).toBe('grok-4.5')
    // 4.3 shipped after 4.20, so it wins even though the number looks smaller.
    expect(preferGrokModel(['grok-4.20-0309-non-reasoning', 'grok-4.3'])).toBe('grok-4.3')
    expect(preferGrokModel(['grok-4.20-0309-non-reasoning', 'grok-voice-1'])).toBe(
      'grok-4.20-0309-non-reasoning'
    )
    expect(preferGrokModel(['grok-imagine-image-quality', 'grok-voice-1'])).toBeNull()
    expect(preferGrokModel([])).toBeNull()
  })
  it('moves a key that an older build saved in the wrong tab', () => {
    // Someone pasted the xAI key while the Gemini tab was open; the prefix makes it obvious.
    store.set(
      'pestino-direct-vision',
      JSON.stringify({
        version: 2,
        active: 'gemini',
        slots: {
          gemini: { model: 'gemini-2.5-flash', key: 'xai-ExampleExampleKey123', ok: false },
          grok: { model: 'grok-4', key: '', ok: false },
        },
      })
    )
    expect(directSettings()).toMatchObject({
      provider: 'grok',
      key: 'xai-ExampleExampleKey123',
      model: DEFAULT_GROK_MODEL,
    })
    expect(providerStatus().gemini.key_present).toBe(false)
    expect(providerStatus().grok.key_present).toBe(true)
    // The reverse mix is repaired too, and a deliberate key in both tabs is left alone.
    store.set(
      'pestino-direct-vision',
      JSON.stringify({
        version: 2,
        active: 'grok',
        slots: {
          gemini: { model: 'gemini-2.5-flash', key: '', ok: false },
          grok: { model: 'grok-4.7', key: 'AIzaSyExampleExampleExample123', ok: false },
        },
      })
    )
    expect(directSettings()).toMatchObject({
      provider: 'gemini',
      key: 'AIzaSyExampleExampleExample123',
    })
    store.set(
      'pestino-direct-vision',
      JSON.stringify({
        version: 2,
        active: 'gemini',
        slots: {
          gemini: { model: 'gemini-2.5-flash', key: 'AIzaSyExampleExampleExample123', ok: true },
          grok: { model: 'grok-4.7', key: 'xai-ExampleExampleKey123', ok: true },
        },
      })
    )
    expect(providerStatus()).toMatchObject({
      gemini: { key_present: true },
      grok: { key_present: true },
    })
  })
  it('names the right tab when the wrong provider key is pasted', () => {
    expect(providerKeyHint('grok', 'AIzaSyExampleExample')).toContain('Gemini')
    expect(providerKeyHint('gemini', 'xai-ExampleExampleKey123')).toContain('Grok')
    expect(providerKeyHint('grok', 'xai-ExampleExampleKey123')).toBe('')
    expect(providerKeyHint('gemini', 'AIzaSyExampleExample')).toBe('')
    expect(providerKeyHint('grok', '')).toBe('')
  })
  it('re-tests with a working model before reporting a stale-name failure', async () => {
    saveDirectSettings('grok-4.6', 'xai-ExampleExampleKey123', 'grok')
    const calls: { url: string; init: RequestInit }[] = []
    setFetchImplementation((async (url: string, init: RequestInit) => {
      calls.push({ url, init })
      if (url.endsWith('/v1/models'))
        return new Response(JSON.stringify({ data: [{ id: 'grok-4.3' }, { id: 'grok-4.7' }] }), {
          status: 200,
        })
      const body = JSON.parse(String(init.body)) as { model: string }
      if (body.model === 'grok-4.6')
        return new Response(JSON.stringify({ error: { message: 'Model not found: grok-4.6' } }), {
          status: 404,
        })
      return new Response(JSON.stringify({ choices: [{ message: { content: '{"ok":true}' } }] }), {
        status: 200,
      })
    }) as unknown as typeof fetch)

    const answer = await testDirectConnection()
    expect(answer.provider).toBe('grok')
    expect(answer.model).toBe('grok-4.7')
    expect(answer.ok).toBe(true)
    expect(answer.note).toContain('grok-4.7')
    // Discover the account first; don't spend a failed call on an unavailable ID.
    expect(calls.map((c) => (c.url.endsWith('/v1/models') ? 'list' : 'chat'))).toEqual([
      'list',
      'chat',
    ])
    expect(directSettings().model).toBe('grok-4.7')
    expect(directSettings().ok).toBe(true)
  })
  it('sends a plain string for text-only Grok calls and typed parts only for photos', async () => {
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    const calls = stub({ choices: [{ message: { content: '{"ok":true}' } }] })
    await testDirectConnection()
    const textBody = JSON.parse(String(calls.find((c) => c.init.body)?.init.body)) as {
      messages: { role: string; content: unknown }[]
      response_format?: unknown
      temperature?: unknown
    }
    expect(typeof textBody.messages[1].content).toBe('string')
    // Parameters some reasoning models reject are simply not sent.
    expect(textBody.response_format).toBeUndefined()
    expect(textBody.temperature).toBeUndefined()

    const image = 'data:image/jpeg;base64,AAAA'
    calls.length = 0
    await analyzePhotosDirect([image], { ...EMPTY_CONTEXT })
    const photoBody = JSON.parse(String(calls[0].init.body)) as {
      messages: { role: string; content: { type: string }[] }[]
    }
    const parts = photoBody.messages[1].content
    expect(Array.isArray(parts)).toBe(true)
    expect(parts[0].type).toBe('text')
    expect(parts[1].type).toBe('image_url')
  })
})

describe('one working provider is enough (automatic failover)', () => {
  const grokOk = () =>
    new Response(JSON.stringify({ choices: [{ message: { content: JSON.stringify(photo) } }] }), {
      status: 200,
    })
  it('saves a key that arrived with invisible characters instead of silently dropping it', () => {
    saveDirectSettings('grok-4.7', ' \u200f xai-ExampleExampleKey123\n', 'grok')
    expect(providerStatus().grok.key_present).toBe(true)
    expect(directSettings().key).toBe('xai-ExampleExampleKey123')
    // A key that is still too short is rejected with a clear reason, not stored empty.
    expect(() => saveDirectSettings('grok-4.7', 'xai-123', 'grok')).toThrow(/کلید/)
    expect(providerStatus().grok.key_present).toBe(true)
  })
  it('falls back to the second provider when the active one fails', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123', 'gemini')
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    // Make Gemini active again, then fail it with a quota error.
    saveDirectSettings('gemini-2.5-flash', undefined, 'gemini')
    const urls: string[] = []
    setFetchImplementation((async (url: string) => {
      urls.push(url)
      if (url.includes('generativelanguage')) {
        return new Response(JSON.stringify({ error: { message: 'quota exceeded' } }), {
          status: 429,
        })
      }
      return grokOk()
    }) as unknown as typeof fetch)
    const result = await analyzePhotosDirect(['data:image/jpeg;base64,AAAA'], {
      ...EMPTY_CONTEXT,
    })
    expect(result.summary).toContain('لکه')
    expect(result.provider).toBe('grok-direct-byo-key')
    expect(urls[0]).toContain('generativelanguage')
    expect(urls[1]).toBe('https://api.x.ai/v1/chat/completions')
    // The provider that answered becomes the active one, so the next call starts there.
    expect(directSettings().provider).toBe('grok')
    expect(directSettings().ok).toBe(true)
  })
  it('does not try the other provider when the owner turns fallback off', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123', 'gemini')
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    saveDirectSettings('gemini-2.5-flash', undefined, 'gemini')
    expect(fallbackEnabled()).toBe(true)
    setFallback(false)
    expect(fallbackEnabled()).toBe(false)
    const urls: string[] = []
    setFetchImplementation((async (url: string) => {
      urls.push(url)
      if (url.includes('generativelanguage'))
        return new Response(JSON.stringify({ error: { message: 'quota exceeded' } }), {
          status: 429,
        })
      return grokOk()
    }) as unknown as typeof fetch)
    await expect(
      analyzePhotosDirect(['data:image/jpeg;base64,AAAA'], { ...EMPTY_CONTEXT })
    ).rejects.toThrow()
    expect(urls).toHaveLength(1)
    expect(urls[0]).toContain('generativelanguage')
    setFallback(true)
  })
  it('reports both reasons when neither provider answers', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123', 'gemini')
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    saveDirectSettings('gemini-2.5-flash', undefined, 'gemini')
    setFetchImplementation((async (url: string) => {
      if (url.includes('generativelanguage'))
        return new Response(JSON.stringify({ error: { message: 'quota exceeded' } }), {
          status: 429,
        })
      return new Response(JSON.stringify({ error: { message: 'invalid api key' } }), {
        status: 401,
      })
    }) as unknown as typeof fetch)
    await expect(
      analyzePhotosDirect(['data:image/jpeg;base64,AAAA'], { ...EMPTY_CONTEXT })
    ).rejects.toThrow(/Google|کلید xAI| |Gemini/s)
  })
  it('treats a key on either provider as configured, even if the other is active', () => {
    expect(anyProviderReady()).toBe(false)
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    saveDirectSettings('gemini-2.5-flash', undefined, 'gemini')
    expect(directSettings().key).toBe('')
    expect(anyProviderReady()).toBe(true)
  })
  it('diagnoses both providers, keeps the failing reason and activates the one that works', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123', 'gemini')
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    saveDirectSettings('gemini-2.5-flash', undefined, 'gemini')
    setFetchImplementation((async (url: string) => {
      if (url.includes('generativelanguage'))
        return new Response(JSON.stringify({ error: { message: 'API key expired' } }), {
          status: 401,
        })
      return new Response(JSON.stringify({ choices: [{ message: { content: '{"ok":true}' } }] }), {
        status: 200,
      })
    }) as unknown as typeof fetch)
    const rows = await diagnoseProviders()
    expect(rows).toHaveLength(2)
    expect(rows[0]).toMatchObject({ provider: 'gemini', ok: false, status: 401 })
    expect(rows[0].detail).toContain('پذیرفته نشد')
    expect(rows[1]).toMatchObject({ provider: 'grok', ok: true, status: 200 })
    expect(directSettings().provider).toBe('grok')
  })
})

describe('provider connection regressions (no real key or paid call)', () => {
  it('understands xAI string errors as well as nested Google errors and strips both keys', () => {
    const message = safeProviderMessage(
      JSON.stringify({
        code: 'SomeCode',
        error: 'Not enough credits xai-ExampleExampleKey123 Bearer secret-token-value',
      })
    )
    expect(message).toContain('Not enough credits')
    expect(message).not.toContain('ExampleExampleKey123')
    expect(message).not.toContain('secret-token-value')
    expect(
      providerError(
        403,
        JSON.stringify({ error: 'Your team has no credits' }),
        'grok-account-model',
        'grok'
      ).message
    ).toContain('اعتبار')
    expect(safeProviderMessage('<html>proxy error</html>')).not.toContain('<html>')
  })
  it('separates TLS, DNS and timeout from bad keys without exposing native error payloads', () => {
    for (const [raw, expected] of [
      ['SSLHandshakeException xai-ExampleExampleKey123', 'ارتباط امن'],
      ['UnknownHostException api.x.ai', 'نشانی'],
      ['SocketTimeoutException', 'مهلت'],
      ['Failed to fetch with Authorization Bearer secret', 'هیچ پاسخ HTTP'],
    ]) {
      const result = connectionFailure(new Error(raw), 'grok')
      expect(result.status).toBe(0)
      expect(result.message).toContain(expected)
      expect(result.message).not.toMatch(/secret|ExampleExampleKey123|Authorization/)
    }
  })
  it('does not erase the second provider after a successful single-provider test', async () => {
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123', 'gemini')
    stub(geminiReply({ ok: true }))
    await testDirectConnection()
    expect(providerStatus()).toMatchObject({
      gemini: { key_present: true, ok: true },
      grok: { key_present: true },
    })
    expect(fallbackEnabled()).toBe(true)
  })
  it('keeps both provider keys and the disabled fallback setting after a failed test', async () => {
    saveDirectSettings('gemini-2.5-flash', 'AIzaSyExampleExampleExample123', 'gemini')
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    setFallback(false)
    stub({ error: 'Unauthorized' }, 401)
    await expect(testDirectConnection()).rejects.toMatchObject({ status: 401 })
    expect(providerStatus()).toMatchObject({
      gemini: { key_present: true },
      grok: { key_present: true, ok: false },
    })
    expect(fallbackEnabled()).toBe(false)
  })
  it('accepts text content parts and rejects truncated output rather than storing it', async () => {
    saveDirectSettings('grok-4.7', 'xai-ExampleExampleKey123', 'grok')
    stub({
      choices: [
        { message: { content: [{ type: 'text', text: '{"ok":true}' }] }, finish_reason: 'stop' },
      ],
    })
    expect((await testDirectConnection()).ok).toBe(true)
    stub({ choices: [{ message: { content: '{"ok":true}' }, finish_reason: 'length' }] })
    await expect(testDirectConnection()).rejects.toThrow('سقف طول')
  })
})
