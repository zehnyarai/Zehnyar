import 'fake-indexeddb/auto'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Bootstrap, Orchard, Report } from './types'
import {
  eraseLocalData,
  exportBackup,
  localApi,
  localKnowledge,
  restoreBackup,
  validateBackup,
} from './standalone'
import { setFetchImplementation } from './visionDirect'
import { EMPTY_CONTEXT } from './scientific'

const orchard = {
  name: 'باغ آزمون',
  province: 'کرمان',
  city: 'رفسنجان',
  cultivar: 'اکبری',
  irrigation: 'قطره‌ای',
  area: 2,
  trees: 200,
  age: 10,
}
const post = (body: unknown) => ({ method: 'POST', body: JSON.stringify(body) })
beforeEach(async () => {
  vi.stubGlobal('localStorage', { removeItem: vi.fn() })
  await eraseLocalData()
})

describe('free local-only edition', () => {
  it('starts empty, with no fabricated accounts, payments or analysis', async () => {
    const b = await localApi<Bootstrap>('/bootstrap')
    expect(b.orchards).toEqual([])
    expect(b.reports).toEqual([])
    expect(b.tasks).toEqual([])
    expect(b.services.vision_configured).toBe(false)
    expect(b.services.payment_configured).toBe(false)
    expect(b.plans).toEqual([])
    expect(b.user?.email).toBeNull()
  })
  it('ships the educational knowledge without a network request', () => {
    expect(localKnowledge().articles).toHaveLength(26)
    expect(localKnowledge().reviewed).toBe(false)
  })
  it('stores, reloads and edits a real local orchard', async () => {
    const created = await localApi<Orchard>('/orchards', post(orchard))
    await localApi(`/orchards/${created.id}`, {
      method: 'PUT',
      body: JSON.stringify({ ...orchard, name: 'باغ ویرایش‌شده' }),
    })
    expect((await localApi<Bootstrap>('/bootstrap')).orchards[0].name).toBe('باغ ویرایش‌شده')
  })
  it('serializes concurrent mutations without losing records', async () => {
    await Promise.all([
      localApi('/orchards', post(orchard)),
      localApi('/orchards', post({ ...orchard, name: 'باغ دوم' })),
    ])
    expect((await localApi<Bootstrap>('/bootstrap')).orchards).toHaveLength(2)
  })
  it('checks numeric inputs instead of trusting a form', async () => {
    await expect(localApi('/orchards', post({ ...orchard, trees: -3 }))).rejects.toThrow(
      'تعداد درخت'
    )
    await expect(localApi('/orchards', post({ ...orchard, area: '2' }))).rejects.toThrow('مساحت')
    expect((await localApi<Bootstrap>('/bootstrap')).orchards).toHaveLength(0)
  })
  it('rejects references to an unknown orchard', async () => {
    await expect(
      localApi('/tasks', post({ title: 'بازدید برگ', due_date: '2026-10-10', orchard_id: 'other' }))
    ).rejects.toThrow('باغ پیدا نشد')
  })
  it('stores task completion and removes tasks linked to a deleted orchard', async () => {
    const o = await localApi<Orchard>('/orchards', post(orchard))
    const t = await localApi<{ id: string }>(
      '/tasks',
      post({ title: 'بازدید برگ', due_date: '2026-10-10', orchard_id: o.id })
    )
    await localApi(`/tasks/${t.id}`, { method: 'PUT', body: JSON.stringify({ done: true }) })
    expect((await localApi<Bootstrap>('/bootstrap')).tasks[0].done).toBe(1)
    await localApi(`/orchards/${o.id}`, { method: 'DELETE' })
    expect((await localApi<Bootstrap>('/bootstrap')).tasks).toHaveLength(0)
  })
  it('rejects invalid calendar dates and task toggles', async () => {
    await expect(
      localApi('/tasks', post({ title: 'بازدید برگ', due_date: '2026-02-31' }))
    ).rejects.toThrow('تاریخ')
    const t = await localApi<{ id: string }>(
      '/tasks',
      post({ title: 'بازدید برگ', due_date: '2026-10-10' })
    )
    await expect(
      localApi(`/tasks/${t.id}`, { method: 'PUT', body: JSON.stringify({ done: 'yes' }) })
    ).rejects.toThrow('وضعیت')
  })
  it.each(['/analyses', '/payments/request', '/auth/register', '/admin/overview'])(
    'never emulates online capabilities: %s',
    async (path) => {
      await expect(localApi(path, post({}))).rejects.toThrow('مستقل و رایگان')
    }
  )
  it('round-trips a backup without contacting any server', async () => {
    await localApi('/orchards', post(orchard))
    const backup = await exportBackup()
    await eraseLocalData()
    await restoreBackup('\uFEFF' + backup)
    expect((await localApi<Bootstrap>('/bootstrap')).orchards[0].name).toBe(orchard.name)
  })
  it('does not overwrite existing data when a backup is invalid', async () => {
    await localApi('/orchards', post(orchard))
    await expect(restoreBackup('{"app":"another","version":1}')).rejects.toThrow('پستینو')
    expect((await localApi<Bootstrap>('/bootstrap')).orchards).toHaveLength(1)
  })
  it('rejects duplicate identities, malicious image links and SVG backups', () => {
    const o = { ...orchard, id: 'one', is_sample: 0 }
    const raw = {
      app: 'pestino',
      version: 1,
      orchards: [o, o],
      tasks: [],
      reports: [] as unknown[],
    }
    expect(() => validateBackup(JSON.stringify(raw))).toThrow('تکراری')
    raw.orchards = [o]
    for (const image of ['https://evil.example/x.jpg', 'data:image/svg+xml;base64,PHN2Zz4=']) {
      raw.reports = [
        {
          id: 'photo',
          orchard_id: 'one',
          tree_part: 'برگ',
          notes: '',
          created_at: '2026-10-10T00:00:00Z',
          image_url: image,
        },
      ]
      expect(() => validateBackup(JSON.stringify(raw))).toThrow('JPEG محلی')
    }
  })
  it('ignores forged medical diagnoses in imported photo records', () => {
    const raw = {
      app: 'pestino',
      version: 1,
      orchards: [],
      tasks: [],
      reports: [
        {
          id: 'photo',
          orchard_id: null,
          tree_part: 'برگ',
          notes: 'یادداشت صاحب باغ',
          created_at: '2026-10-10T00:00:00Z',
          image_url: 'data:image/jpeg;base64,/9j/AA==',
          data: {
            hypotheses: [{ name: 'fake', confidence: 1 }],
            urgency: 'high',
            actions: ['fake dose'],
          },
        },
      ],
    }
    const result = validateBackup(JSON.stringify(raw)).reports[0]
    expect(result.data.hypotheses).toEqual([])
    expect(result.data.provider).toBe('local-storage')
    expect(result.data.summary).toContain('تحلیل نکرده')
    expect(result.data.actions).not.toContain('fake dose')
  })
})

describe('new reference-layout data remains local and backed up', () => {
  it('persists lab, experience, price and climate records in the same backup', async () => {
    const data = {
      labs: {
        kind: 'soil',
        values: { ph: 8, ec: 3 },
        method: 'saturated',
        sample_date: '2026-10-11',
        depth: '۰ تا ۳۰',
        orchard_id: null,
        notes: '',
      },
      experiences: {
        title: 'بازدید منظم باغ',
        category: 'آبیاری',
        body: 'در بازدید منظم باغ، یکنواختی خروجی قطره‌چکان‌ها را بررسی کردم.',
        province: 'کرمان',
        cultivar: 'اکبری',
        season: '۱۴۰۵',
      },
      prices: {
        cultivar: 'اکبری',
        price: 900000,
        currency: 'toman',
        province: 'کرمان',
        source: 'مشاهده بازار محلی',
        observed_date: '2026-10-11',
        grade: 'خشک با پوست',
      },
      climate: {
        province: 'کرمان',
        observed_date: '2026-10-11',
        minimum: 10,
        maximum: 30,
        humidity: null,
        wind: null,
        stage: '',
        source: 'دماسنج باغ',
      },
    }
    for (const [kind, body] of Object.entries(data))
      await localApi(`/field-records/${kind}`, post(body))
    const backup = await exportBackup()
    await eraseLocalData()
    await restoreBackup(backup)
    for (const kind of Object.keys(data))
      expect(await localApi(`/field-records/${kind}`)).toHaveLength(1)
    const record = (await localApi<{ visibility: string }[]>('/field-records/experiences'))[0]
    expect(record.visibility).toBe('private')
  })
  it('does not let a backup forge publication, credit or scientific output', async () => {
    const backup = JSON.parse(await exportBackup())
    backup.fields.experiences = [
      {
        id: 'entry',
        author: 'forged',
        visibility: 'published',
        created_at: '2026-10-11T00:00:00Z',
        data: {
          title: 'تجربه واقعی',
          category: 'سایر',
          body: 'این صرفاً شرح تجربه باغدار است و نه تشخیص علمی تأیید شده.',
          province: 'کرمان',
          cultivar: '',
          season: '',
        },
      },
    ]
    backup.balance = 1000000
    const validated = validateBackup(JSON.stringify(backup))
    expect(validated.fields.experiences[0].visibility).toBe('private')
    await restoreBackup(JSON.stringify(backup))
    // A forged "balance" in the backup is still ignored: the only balance is the real quota,
    // which is two free analyses on a fresh device — never a million credits.
    expect((await localApi<{ balance: number }>('/billing/my')).balance).toBe(2)
    expect(
      (await localApi<{ enabled: boolean; card_number: string }>('/billing/config')).card_number
    ).toBe('')
  })
  it('clears a deleted orchard reference from its lab records', async () => {
    const o = await localApi<Orchard>('/orchards', post(orchard))
    await localApi(
      '/field-records/labs',
      post({
        kind: 'soil',
        values: { ph: 8 },
        method: 'unknown',
        sample_date: '2026-10-11',
        depth: '',
        orchard_id: o.id,
        notes: '',
      })
    )
    await localApi(`/orchards/${o.id}`, { method: 'DELETE' })
    expect(validateBackup(await exportBackup()).fields.labs[0].data).toHaveProperty(
      'orchard_id',
      null
    )
  })
})

it('works without randomUUID on an older Android WebView, retaining secure random ids', async () => {
  const random = crypto.getRandomValues.bind(crypto)
  vi.stubGlobal('crypto', { getRandomValues: random })
  try {
    const saved = await localApi<Orchard>('/orchards', post(orchard))
    expect(saved.id).toMatch(
      /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/
    )
    expect((await localApi<Bootstrap>('/bootstrap')).orchards[0].name).toBe(orchard.name)
  } finally {
    vi.unstubAllGlobals()
  }
})

it('cannot pretend that a Gemini laboratory endpoint exists in an offline installer', async () => {
  const boot = await localApi<Bootstrap>('/bootstrap')
  expect(boot.services.lab_ai_configured).toBe(false)
  await expect(localApi('/lab-analyses', post({ consent: true }))).rejects.toThrow()
})

describe('device-direct analysis with the owner key (offline edition)', () => {
  const key = 'AIzaSyExampleExampleExample123'
  const sample = {
    kind: 'water',
    values: { ec: 2.1, sodium: 260, calcium: 88, magnesium: 30, bicarbonate: 210, carbonate: 0 },
    method: 'water',
    sample_date: '2026-10-01',
    depth: '',
    orchard_id: null,
    notes: 'چاه عمیق باغ',
  }
  const lab = {
    title: 'آب چاه',
    summary: 'نمونه تک‌نقطه‌ای است.',
    findings: ['شوری نیازمند پایش فصلی است'],
    nutrition_considerations: [],
    irrigation_considerations: ['زهکشی بررسی شود'],
    care_plan: [],
    yield_quality_plan: [],
    needed_tests: ['آزمایش خاک'],
    limitations: ['تکرار نمونه لازم است'],
    follow_up_questions: [],
    knowledge_ids: ['salinity'],
  }
  const screening = {
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
  const store = new Map<string, string>()
  let calls: { url: string; init: RequestInit }[] = []
  beforeEach(async () => {
    store.clear()
    calls = []
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    })
    setFetchImplementation((async (url: string, init: RequestInit) => {
      calls.push({ url, init })
      const body = String(init.body)
      const payload = body.includes('connection test')
        ? { ok: true, model: 'gemini-2.5-flash' }
        : body.includes('laboratory')
          ? lab
          : screening
      return new Response(
        JSON.stringify({
          candidates: [
            { finishReason: 'STOP', content: { parts: [{ text: JSON.stringify(payload) }] } },
          ],
        }),
        { status: 200 }
      )
    }) as unknown as typeof fetch)
    await eraseLocalData()
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    setFetchImplementation(null)
  })
  it('stays unconfigured until the owner stores a key, and never echoes the key back', async () => {
    expect((await localApi<Bootstrap>('/bootstrap')).services.vision_configured).toBe(false)
    await expect(
      localApi('/local/analyses', post({ report_id: 'x', consent: true }))
    ).rejects.toThrow('کلید شخصی')
    const stored = await localApi<{ key_present: boolean; model: string }>('/local/vision', {
      method: 'PUT',
      body: JSON.stringify({ model: 'gemini-2.5-flash', key }),
    })
    expect(stored.key_present).toBe(true)
    expect(JSON.stringify(stored)).not.toContain(key)
    const boot = await localApi<Bootstrap>('/bootstrap')
    expect(boot.services.vision_configured).toBe(true)
    expect(boot.services.lab_ai_configured).toBe(true)
    expect(boot.services.vision_verified).toBe(false)
    expect(calls).toHaveLength(0)
  })
  it('proves the connection with a text call, then interprets a laboratory sample', async () => {
    await localApi('/local/vision', {
      method: 'PUT',
      body: JSON.stringify({ model: 'gemini-2.5-flash', key }),
    })
    vi.stubGlobal('fetch', fetch)
    const tested = await localApi<{ connection_ok: boolean }>('/local/vision/test', {
      method: 'POST',
    })
    expect(tested.connection_ok).toBe(true)
    expect(calls[0].url).toContain('gemini-2.5-flash:generateContent')
    expect(calls[0].url).not.toContain('AIza')
    await expect(localApi('/local/lab-analyses', post({ sample, consent: false }))).rejects.toThrow(
      'رضایت'
    )
    const assessment = await localApi<{
      id: string
      units: Record<string, string>
      calculations: unknown[]
      result: { model: string; disclaimer: string }
    }>('/local/lab-analyses', post({ sample, consent: true }))
    expect(assessment.units.sodium).toBe('mg/L')
    expect(assessment.calculations.length).toBeGreaterThan(0)
    expect(assessment.result.model).toBe('gemini-2.5-flash')
    expect(assessment.result.disclaimer).toContain('نه آزمایش مستقل')
    expect(await localApi<unknown[]>('/local/lab-analyses')).toHaveLength(1)
    expect((await exportBackup()).includes(assessment.id)).toBe(true)
    await localApi(`/local/lab-analyses/${assessment.id}`, { method: 'DELETE' })
    expect(await localApi<unknown[]>('/local/lab-analyses')).toHaveLength(0)
  })
  it('screens a saved orchard photo without losing the original file, and can drop the text', async () => {
    const pixels = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA=='
    const backup = JSON.stringify({
      app: 'pestino',
      version: 1,
      orchards: [],
      tasks: [],
      reports: [
        {
          id: '11111111-1111-4111-8111-111111111111',
          orchard_id: null,
          tree_part: 'برگ',
          notes: 'لکه روشن',
          image_url: pixels,
          context: { ...EMPTY_CONTEXT, symptoms: [] },
          created_at: '2026-10-01T10:00:00.000Z',
        },
      ],
      fields: { labs: [], experiences: [], prices: [], climate: [] },
    })
    await restoreBackup(backup)
    await localApi('/local/vision', {
      method: 'PUT',
      body: JSON.stringify({ model: 'gemini-2.5-flash', key }),
    })
    const analyzed = await localApi<Report>(
      '/local/analyses',
      post({ report_id: '11111111-1111-4111-8111-111111111111', consent: true })
    )
    expect(analyzed.data.provider).toBe('gemini-direct-byo-key')
    expect(analyzed.data.hypotheses[0].confidence).toBeNull()
    expect(analyzed.image_url).toBe(pixels)
    const sent = JSON.parse(String(calls[0].init.body)) as {
      contents: { parts: { inlineData?: { data: string } }[] }[]
    }
    expect(sent.contents[0].parts.some((p) => p.inlineData?.data === pixels.split(',')[1])).toBe(
      true
    )
    await localApi('/local/analyses/11111111-1111-4111-8111-111111111111', { method: 'DELETE' })
    const cleared = (await localApi<Bootstrap>('/bootstrap')).reports[0]
    expect(cleared.data.provider).toBe('local-storage')
    expect(cleared.image_url).toBe(pixels)
  })
  it('enforces the free-two rule on the device API and unlocks after a paid code', async () => {
    const { createActivationCode } = await import('./quota')
    await localApi('/local/vision', {
      method: 'PUT',
      body: JSON.stringify({ model: 'gemini-2.5-flash', key }),
    })
    // A saved report is injected through a backup: the node test environment has no canvas
    // image pipeline, which the photo upload path needs.
    await restoreBackup(
      JSON.stringify({
        app: 'pestino',
        version: 1,
        orchards: [],
        tasks: [],
        reports: [
          {
            id: '22222222-2222-4222-8222-222222222222',
            orchard_id: null,
            tree_part: 'برگ',
            notes: 'لکه روشن',
            image_url: 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA==',
            context: { ...EMPTY_CONTEXT, symptoms: [] },
            created_at: '2026-10-01T10:00:00.000Z',
          },
        ],
        fields: { labs: [], experiences: [], prices: [], climate: [] },
      })
    )
    const run = () =>
      localApi(
        '/local/analyses',
        post({ report_id: '22222222-2222-4222-8222-222222222222', consent: true })
      )
    await run()
    await run()
    let blocked: { code?: string; message: string } | null = null
    try {
      await run()
    } catch (error) {
      blocked = error as { code?: string; message: string }
    }
    expect(blocked?.code).toBe('QUOTA_REQUIRED')
    expect(blocked?.message).toContain('تحلیل رایگان')
    expect((await localApi<{ blocked: boolean }>('/local/quota')).blocked).toBe(true)

    // The owner prices the package from the dollar day rate, then issues a code after payment.
    const priced = await localApi<{ price_toman: number; needs_price: boolean }>('/local/quota', {
      method: 'PUT',
      body: JSON.stringify({
        free_limit: 2,
        package: { analyses: 20, usd_price: 2, usd_rate: 92_000, rate_date: '2026-10-14' },
      }),
    })
    expect(priced.price_toman).toBe(190_000)
    expect(priced.needs_price).toBe(false)
    const issued = await localApi<{ code: string }>('/local/quota/code', {
      method: 'POST',
      body: JSON.stringify({ analyses: 20, days: null }),
    })
    expect(issued.code.startsWith('PST-')).toBe(true)
    await expect(
      localApi('/local/quota/redeem', post({ code: 'PST-K-0-1111-AAAAAA' }))
    ).rejects.toThrow()
    const redeemed = await localApi<{ added: number }>(
      '/local/quota/redeem',
      post({ code: issued.code })
    )
    expect(redeemed.added).toBe(20)
    await expect(localApi('/local/quota/redeem', post({ code: issued.code }))).rejects.toThrow(
      /قبلاً/
    )
    expect((await localApi<{ blocked: boolean }>('/local/quota')).blocked).toBe(false)
    await run()
    expect((await localApi<{ credits: number }>('/local/quota')).credits).toBe(19)
    // A code that was not signed by this app never grants anything.
    const another = createActivationCode({ analyses: 1, today: '2026-10-14', serial: 5555 })
    await expect(
      localApi('/local/quota/redeem', post({ code: another.code.replace('PST-', 'PST2-') }))
    ).rejects.toThrow()
  })
  it('shows the same quota numbers on the credits page as the analysis guard enforces', async () => {
    const fresh = await localApi<{
      balance: number
      purchased: number
      used: number
      free_left: number
    }>('/billing/my')
    expect(fresh).toMatchObject({ balance: 2, purchased: 0, used: 0, free_left: 2 })
    await localApi('/local/quota/grant', { method: 'POST', body: JSON.stringify({ analyses: 5 }) })
    const granted = await localApi<{ balance: number; purchased: number; free_left: number }>(
      '/billing/my'
    )
    expect(granted).toMatchObject({ balance: 7, purchased: 5, free_left: 2 })
  })
  it('confirms a recorded transfer and adds the package to this device', async () => {
    await localApi('/local/quota', {
      method: 'PUT',
      body: JSON.stringify({ free_limit: 2, package: { analyses: 10, price_toman: 900_000 } }),
    })
    const receipt = await localApi<{ id: string; confirmed_at: string | null }>(
      '/local/billing/receipts',
      post({
        payer: 'باغدار تست',
        amount_toman: 900_000,
        paid_at: '2026-10-14',
        reference: '778899',
        note: '',
      })
    )
    expect(receipt.confirmed_at).toBeNull()
    expect((await localApi<{ pending_receipts: number }>('/local/quota')).pending_receipts).toBe(1)
    const after = await localApi<{ credits: number; receipt: { granted_analyses: number } }>(
      `/local/billing/receipts/${receipt.id}/confirm`,
      { method: 'POST' }
    )
    expect(after.receipt.granted_analyses).toBe(10)
    expect(after.credits).toBe(10)
    await expect(
      localApi(`/local/billing/receipts/${receipt.id}/confirm`, { method: 'POST' })
    ).rejects.toThrow(/قبلاً/)
  })
  it('lists the key models and probes the free candidates through the local API', async () => {
    await localApi('/local/vision', {
      method: 'PUT',
      body: JSON.stringify({ model: 'gemini-2.5-flash', key }),
    })
    setFetchImplementation((async (url: string) => {
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
      if (url.includes('gemini-3.1-pro-preview'))
        return new Response(
          JSON.stringify({ error: { message: 'generate_content_free_tier_requests, limit: 0' } }),
          { status: 429 }
        )
      return new Response(
        JSON.stringify({
          candidates: [{ finishReason: 'STOP', content: { parts: [{ text: '{"ok":true}' }] } }],
        }),
        { status: 200 }
      )
    }) as unknown as typeof fetch)
    const listed = await localApi<{ id: string }[]>('/local/vision/models')
    expect(listed.map((m) => m.id)).toContain('gemini-2.5-flash')
    const probed = await localApi<{
      results: { model: string; ok: boolean; detail: string }[]
      notice: string
    }>('/local/vision/probe', post({ models: ['gemini-2.5-flash', 'gemini-3.1-pro-preview'] }))
    expect(probed.results[0].ok).toBe(true)
    expect(probed.results[1].ok).toBe(false)
    expect(probed.results[1].detail).toContain('سهمیهٔ رایگان')
    expect(probed.notice).toContain('بهبود محصولات گوگل')
    await expect(localApi('/local/vision/probe', post({ models: [] }))).resolves.toBeTruthy()
  })
})

describe('owner card and manual receipt ledger in the offline panel', () => {
  const card = {
    card_number: '۹۴۰۱ ۶۵۲۴ ۷۳۱۱ ۶۰۶۳',
    holder: 'احمد قرائی سلطان آبادی',
    bank: 'بانک ملی ایران',
  }
  const receipt = {
    payer: 'باغدار نمونه',
    amount_toman: 990_000,
    paid_at: '2026-10-12',
    reference: '123456',
    note: '',
  }
  const empty = async () => {
    const view = await localApi<{ enabled: boolean; card: unknown; receipts: unknown[] }>(
      '/local/billing'
    )
    return view
  }
  beforeEach(async () => {
    vi.stubGlobal('localStorage', { removeItem: vi.fn() })
    await eraseLocalData()
  })
  it('starts closed, and shows nothing to the credits page before a card exists', async () => {
    const view = await empty()
    expect(view.enabled).toBe(false)
    expect(view.card).toBeNull()
    const config = await localApi<{ enabled: boolean; card_number: string }>('/billing/config')
    expect(config.enabled).toBe(false)
    expect(config.card_number).toBe('')
    const mine = await localApi<{ purchased: number }>('/billing/my')
    expect(mine.purchased).toBe(0)
  })
  it('refuses a card without visual confirmation, then stores normalised digits', async () => {
    await expect(
      localApi('/local/billing', {
        method: 'PUT',
        body: JSON.stringify({ ...card, confirmed: false }),
      })
    ).rejects.toThrow('تطبیق')
    await expect(
      localApi('/local/billing', {
        method: 'PUT',
        body: JSON.stringify({ ...card, card_number: '1111', confirmed: true }),
      })
    ).rejects.toThrow('شماره کارت')
    const saved = await localApi<{ card: { card_number: string; holder: string } }>(
      '/local/billing',
      {
        method: 'PUT',
        body: JSON.stringify({ ...card, confirmed: true }),
      }
    )
    expect(saved.card.card_number).toBe('9401652473116063')
    const config = await localApi<{ enabled: boolean; card_number: string; notice: string }>(
      '/billing/config'
    )
    expect(config.enabled).toBe(true)
    expect(config.notice).toContain('دستی')
    // The notice must state that automatic verification does not exist.
    expect(config.notice).toContain('تأیید خودکار و اعتبار سروری وجود ندارد')
  })
  it('records and deletes manual receipts without claiming bank verification', async () => {
    await localApi('/local/billing', {
      method: 'PUT',
      body: JSON.stringify({ ...card, confirmed: true }),
    })
    await expect(
      localApi('/local/billing/receipts', post({ ...receipt, amount_toman: 10 }))
    ).rejects.toThrow('مبلغ')
    const row = await localApi<{ id: string }>('/local/billing/receipts', post(receipt))
    const view = await localApi<{
      receipts: { id: string }[]
      total_toman: number
      notice: string
    }>('/local/billing')
    expect(view.receipts).toHaveLength(1)
    expect(view.total_toman).toBe(990_000)
    expect(view.notice).toContain('درگاه بانکی')
    const mine = await localApi<{ purchased: number; balance: number }>('/billing/my')
    // Merely recording a receipt never grants analyses; the owner confirms the transfer first.
    expect(mine.purchased).toBe(0)
    expect(mine.balance).toBe(2)
    await localApi(`/local/billing/receipts/${row.id}`, { method: 'DELETE' })
    expect((await empty()).receipts).toHaveLength(0)
  })
  it('keeps card and ledger in the backup, but still rejects an invalid one', async () => {
    await localApi('/local/billing', {
      method: 'PUT',
      body: JSON.stringify({ ...card, confirmed: true }),
    })
    await localApi('/local/billing/receipts', post(receipt))
    const backup = await exportBackup()
    expect(backup).toContain('9401652473116063')
    expect(backup).toContain('باغدار نمونه')
    await eraseLocalData()
    expect((await empty()).enabled).toBe(false)
    await restoreBackup(backup)
    const view = await localApi<{ enabled: boolean; receipts: unknown[] }>('/local/billing')
    expect(view.enabled).toBe(true)
    expect(view.receipts).toHaveLength(1)
    const forged = JSON.parse(backup) as { billing: { card: { card_number: string } } }
    forged.billing.card.card_number = '1111111111111111'
    await expect(restoreBackup(JSON.stringify(forged))).rejects.toThrow()
  })
  it('removes only the card when the owner deletes it', async () => {
    await localApi('/local/billing', {
      method: 'PUT',
      body: JSON.stringify({ ...card, confirmed: true }),
    })
    await localApi('/local/billing/receipts', post(receipt))
    const view = await localApi<{ enabled: boolean; receipts: unknown[] }>('/local/billing/card', {
      method: 'DELETE',
    })
    expect(view.enabled).toBe(false)
    expect(view.receipts).toHaveLength(1)
  })
})
