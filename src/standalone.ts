/**
 * Local-only edition. No account, server, hosted payment or fabricated diagnosis.
 * Photo/soil/water interpretation is optional: it needs the owner's own Google key,
 * kept only on this device (see visionDirect.ts) and never bundled in the app.
 */
import type { AnalysisData, Bootstrap, Knowledge, Orchard, Report, Services, Task } from './types'
import knowledgeData from './data/knowledge.json'
import { assetUrl } from './config'
import { EMPTY_CONTEXT, validateContext } from './scientific'
import type { DiagnosticContext } from './scientific'
import { EMPTY_BILLING, validateField } from './fieldwork'
import type { BillingConfig } from './fieldwork'
import type { FieldKind, FieldRecord, LabInput } from './fieldwork'
import { emptyBilling, receiptsTotal, validateCard, validateReceipt } from './localAdmin'
import type { LocalBilling, LocalReceipt } from './localAdmin'
import {
  analyzePhotosDirect,
  clearDirectSettings,
  directSettings,
  interpretLabDirect,
  saveDirectSettings,
  testDirectConnection,
} from './visionDirect'

const DB_NAME = 'pestino-local-v1'
const KEY = 'data'
const MAX_BACKUP_BYTES = 32 * 1024 * 1024
export interface LabAssessment {
  id: string
  created_at: string
  input: LabInput
  units: Record<string, string>
  calculations: { key: string; label: string; value: number; formula: string }[]
  result: Record<string, unknown> & {
    title: string
    summary: string
    provider: string
    model: string
    disclaimer: string
  }
}
interface State {
  version: 1
  orchards: Orchard[]
  tasks: Task[]
  reports: Report[]
  fields: Record<FieldKind, FieldRecord<FieldKind>[]>
  assessments: LabAssessment[]
  billing: LocalBilling
}
export class LocalError extends Error {
  status = 400
}
const emptyState = (): State => ({
  version: 1,
  orchards: [],
  tasks: [],
  reports: [],
  fields: { labs: [], experiences: [], prices: [], climate: [] },
  assessments: [],
  billing: emptyBilling(),
})
const uid = () => {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 15) | 64
  bytes[8] = (bytes[8] & 63) | 128
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}
let connection: Promise<IDBDatabase> | null = null
let queue: Promise<unknown> = Promise.resolve()
function database() {
  if (!connection)
    connection = new Promise<IDBDatabase>((resolve, reject) => {
      if (!globalThis.indexedDB) {
        reject(new LocalError('ذخیره‌سازی دستگاه در دسترس نیست. حالت خصوصی مرورگر را ببندید.'))
        return
      }
      const open = indexedDB.open(DB_NAME, 1)
      open.onupgradeneeded = () => open.result.createObjectStore('state')
      open.onerror = () => {
        connection = null
        reject(
          new LocalError('ذخیره‌سازی دستگاه باز نشد. فضای آزاد و تنظیمات مرورگر را بررسی کنید.')
        )
      }
      open.onsuccess = () => {
        open.result.onversionchange = () => {
          open.result.close()
          connection = null
        }
        resolve(open.result)
      }
    })
  return connection
}
async function load(): Promise<State> {
  const db = await database()
  return new Promise((resolve, reject) => {
    const req = db.transaction('state').objectStore('state').get(KEY)
    req.onsuccess = () =>
      resolve({
        ...emptyState(),
        ...req.result,
        fields: { ...emptyState().fields, ...req.result?.fields },
        billing: {
          card: req.result?.billing?.card ?? null,
          receipts: Array.isArray(req.result?.billing?.receipts)
            ? (req.result.billing.receipts as LocalReceipt[])
            : [],
        },
      })
    req.onerror = () =>
      reject(new LocalError('خواندن داده‌های دستگاه ممکن نشد. داده‌ها را پاک نکنید.'))
  })
}
async function save(state: State) {
  if (
    new TextEncoder().encode(JSON.stringify({ app: 'pestino', ...state }, null, 2)).byteLength >
    MAX_BACKUP_BYTES - 4096
  )
    throw new LocalError(
      'سقف ایمن ذخیره‌سازی ۳۲ مگابایتی تکمیل شده؛ پشتیبان بگیرید و عکس‌های غیرضروری را حذف کنید.'
    )
  const db = await database()
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction('state', 'readwrite')
    tx.objectStore('state').put(state, KEY)
    tx.oncomplete = () => resolve()
    tx.onabort = tx.onerror = () =>
      reject(new LocalError('ذخیره نشد؛ فضای آزاد دستگاه را بررسی کنید. اطلاعات قبلی حفظ شده‌اند.'))
  })
}
function serialize<T>(operation: () => Promise<T>): Promise<T> {
  const next = queue.then(operation)
  queue = next.catch(() => {})
  return next
}
const VERIFIED_WINDOW_MS = 24 * 60 * 60 * 1000
/** Reported from the on-device key only; an unconfigured device claims nothing. */
export function serviceStatus(): Services {
  const settings = directSettings()
  const ready = !!settings.key
  const verified =
    ready &&
    settings.ok &&
    !!settings.checked_at &&
    Date.now() - Date.parse(settings.checked_at) < VERIFIED_WINDOW_MS
  return {
    vision_configured: ready,
    vision_provider: ready ? 'gemini' : 'none',
    vision_model: ready ? settings.model : '',
    vision_verified: verified,
    vision_checked_at: verified ? settings.checked_at : null,
    vision_connection_state: !ready
      ? 'unconfigured'
      : settings.checked_at
        ? verified
          ? 'responded'
          : 'expired'
        : 'untested',
    vision_scientifically_validated: false,
    lab_ai_configured: ready,
    payment_configured: false,
    payment_sandbox: true,
    knowledge_version: knowledgeData.version,
    knowledge_reviewed: false,
    weather_configured: false,
  }
}
/** Never returns the stored key; the device only reports whether one exists. */
function visionStatus() {
  const settings = directSettings()
  return {
    model: settings.model,
    key_present: !!settings.key,
    checked_at: settings.checked_at,
    connection_ok: !!settings.ok,
    note: settings.note,
    storage: 'دستگاه شما (خارج از فایل پشتیبان)',
  }
}
export function localKnowledge(): Knowledge {
  return {
    ...knowledgeData,
    articles: knowledgeData.articles.map((a) => ({ ...a, image: assetUrl(a.image) })),
  }
}
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value))
    throw new LocalError('فرمت اطلاعات معتبر نیست.')
  return value as Record<string, unknown>
}
function text(value: unknown, label: string, max: number, min = 0): string {
  if (typeof value !== 'string' || value.trim().length < min || value.length > max)
    throw new LocalError(`${label} معتبر نیست.`)
  return value.trim()
}
function number(value: unknown, label: string, min: number, max: number, integer = false): number {
  if (
    typeof value !== 'number' ||
    !Number.isFinite(value) ||
    value < min ||
    value > max ||
    (integer && !Number.isInteger(value))
  )
    throw new LocalError(`${label} معتبر نیست.`)
  return value
}
function orchardInput(body: Record<string, unknown>): Omit<Orchard, 'id' | 'is_sample'> {
  return {
    name: text(body.name, 'نام باغ', 80, 2),
    province: text(body.province, 'استان', 40, 2),
    city: text(body.city, 'شهر', 50, 2),
    cultivar: text(body.cultivar, 'رقم', 50, 2),
    irrigation: text(body.irrigation, 'آبیاری', 40, 2),
    area: number(body.area, 'مساحت', 0.01, 100000),
    trees: number(body.trees, 'تعداد درخت', 1, 10000000, true),
    age: number(body.age, 'سن درخت', 0, 150, true),
  }
}
function orchardId(state: State, value: unknown) {
  if (value === '' || value === null || value === undefined) return null
  const id = text(value, 'باغ', 80, 1)
  if (!state.orchards.some((o) => o.id === id)) throw new LocalError('باغ پیدا نشد.')
  return id
}
function taskInput(
  state: State,
  body: Record<string, unknown>
): Omit<Task, 'id' | 'is_sample' | 'done'> {
  const due = text(body.due_date, 'تاریخ', 10, 10)
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(due) ||
    Number.isNaN(Date.parse(due)) ||
    new Date(due).toISOString().slice(0, 10) !== due
  )
    throw new LocalError('تاریخ معتبر وارد کنید.')
  const kind = text(body.kind ?? 'general', 'نوع یادآور', 20, 1)
  if (!['monitoring', 'irrigation', 'nutrition', 'general'].includes(kind))
    throw new LocalError('نوع یادآور معتبر نیست.')
  const id = orchardId(state, body.orchard_id)
  return {
    title: text(body.title, 'عنوان', 160, 3),
    kind,
    due_date: due,
    orchard_id: id,
    orchard_name: state.orchards.find((o) => o.id === id)?.name ?? null,
  }
}
function photoData(part: string, notes: string): AnalysisData {
  return {
    title: `عکس ثبت‌شده ${part}`,
    summary:
      'این پرونده فقط عکس و یادداشت شماست. هیچ مدل یا کارشناس، تصویر را تحلیل نکرده و از آن تشخیص، امتیاز اطمینان یا توصیه درمانی تولید نشده است.',
    quality: 'تحلیل نشده',
    is_pistachio: null,
    observations: notes ? [`یادداشت شما: ${notes}`] : ['هنوز یادداشتی ثبت نکرده‌اید.'],
    hypotheses: [],
    actions: ['برای بررسی تخصصی، عکس و شرح سابقه باغ را به کارشناس محلی نشان دهید.'],
    needed_tests: [],
    follow_up_questions: [],
    urgency: 'low',
    knowledge_ids: ['sampling'],
    disclaimer:
      'پرونده عکس، نه تشخیص. این نسخه تحلیل خودکار، اندازه‌گیری نیاز غذایی یا تعیین دوز کود و سم انجام نمی‌دهد.',
    provider: 'local-storage',
    knowledge_version: knowledgeData.version,
  }
}
async function normalizedPhoto(file: File): Promise<string> {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 8 * 1024 * 1024)
    throw new LocalError('تصویر JPG، PNG یا WebP کمتر از ۸ مگابایت انتخاب کنید.')
  const bytes = new Uint8Array(await file.slice(0, 12).arrayBuffer())
  const valid =
    (bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) ||
    (bytes[0] === 137 && bytes[1] === 80 && bytes[2] === 78 && bytes[3] === 71) ||
    (String.fromCharCode(...bytes.slice(0, 4)) === 'RIFF' &&
      String.fromCharCode(...bytes.slice(8, 12)) === 'WEBP')
  if (!valid) throw new LocalError('محتوای فایل تصویر معتبر نیست.')
  const url = URL.createObjectURL(file)
  try {
    const image = new Image()
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve()
      image.onerror = () => reject(new LocalError('تصویر قابل خواندن نیست.'))
      image.src = url
    })
    const w = image.naturalWidth,
      h = image.naturalHeight
    if (w < 128 || h < 128 || w * h > 24000000)
      throw new LocalError('تصویر باید حداقل ۱۲۸ پیکسل و حداکثر ۲۴ مگاپیکسل باشد.')
    const scale = Math.min(1, 1600 / Math.max(w, h))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(w * scale))
    canvas.height = Math.max(1, Math.round(h * scale))
    const context = canvas.getContext('2d')
    if (!context) throw new LocalError('پردازش تصویر روی این دستگاه ممکن نشد.')
    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0, canvas.width, canvas.height)
    // Canvas encodes fresh pixels; original EXIF/GPS metadata is not copied.
    return canvas.toDataURL('image/jpeg', 0.82)
  } finally {
    URL.revokeObjectURL(url)
  }
}
const MANUAL_NOTICE =
  'حالت دریافت دستی: کارت مقصد را خودِ مالک دستگاه ثبت کرده و تأیید واریز، دستی است. درگاه بانکی، تأیید خودکار و اعتبار سروری وجود ندارد؛ وجهی بدون هماهنگی واریز نکنید.'
function billingConfig(state: State): BillingConfig {
  const card = state.billing.card
  return {
    ...EMPTY_BILLING,
    enabled: !!card,
    card_number: card?.card_number ?? '',
    holder: card?.holder ?? '',
    bank: card?.bank ?? '',
    notice: card
      ? `${MANUAL_NOTICE} این کارت در تاریخ ${card.confirmed_at.slice(0, 10)} توسط مالک دستگاه تأیید شده است.`
      : EMPTY_BILLING.notice,
  }
}
function billingView(state: State) {
  return {
    mode: 'manual' as const,
    enabled: !!state.billing.card,
    card: state.billing.card,
    receipts: state.billing.receipts,
    total_toman: receiptsTotal(state.billing.receipts),
    notice: MANUAL_NOTICE,
  }
}
function bootstrap(state: State): Bootstrap {
  return {
    user: {
      id: 'local-device',
      name: 'باغدار پستینو',
      email: null,
      role: 'user',
      is_demo: 0,
      subscription_until: null,
    },
    orchards: state.orchards,
    reports: state.reports.map((r) => ({
      ...r,
      orchard_name: state.orchards.find((o) => o.id === r.orchard_id)?.name ?? null,
    })),
    tasks: state.tasks.map((t) => ({
      ...t,
      orchard_name: state.orchards.find((o) => o.id === t.orchard_id)?.name ?? null,
    })),
    usage: { used: 0, limit: 0, premium: false },
    services: serviceStatus(),
    plans: [],
  }
}
export async function localApi<T>(path: string, options: RequestInit = {}): Promise<T> {
  return serialize(async () => {
    const state = await load()
    const method = options.method?.toUpperCase() ?? 'GET'
    const body = typeof options.body === 'string' ? object(JSON.parse(options.body)) : {}
    let result: unknown
    let modified = false
    if (path === '/knowledge' && method === 'GET') result = localKnowledge()
    else if (path === '/bootstrap' && method === 'GET') result = bootstrap(state)
    else if (path === '/payments' && method === 'GET') result = []
    else if (path === '/orchards' && method === 'POST') {
      if (state.orchards.length >= 500)
        throw new LocalError('سقف ایمنی ۵۰۰ باغ روی دستگاه تکمیل شده است.')
      const item = { ...orchardInput(body), id: uid(), is_sample: 0 }
      state.orchards.unshift(item)
      result = item
      modified = true
    } else if (path.startsWith('/orchards/') && ['PUT', 'DELETE'].includes(method)) {
      const id = path.slice('/orchards/'.length)
      const i = state.orchards.findIndex((o) => o.id === id)
      if (i < 0) throw new LocalError('باغ پیدا نشد.')
      if (method === 'PUT') state.orchards[i] = { ...orchardInput(body), id, is_sample: 0 }
      else {
        state.orchards.splice(i, 1)
        state.tasks = state.tasks.filter((t) => t.orchard_id !== id)
        state.fields.labs = state.fields.labs.map((r) => {
          const d = r.data as import('./fieldwork').LabInput
          return d.orchard_id === id ? { ...r, data: { ...d, orchard_id: null } } : r
        })
        state.reports = state.reports.map((r) =>
          r.orchard_id === id ? { ...r, orchard_id: null, orchard_name: null } : r
        )
      }
      result = { ok: true }
      modified = true
    } else if (path === '/tasks' && method === 'POST') {
      if (state.tasks.length >= 2000)
        throw new LocalError('سقف ایمنی یادآورهای دستگاه تکمیل شده است.')
      const item = { ...taskInput(state, body), id: uid(), is_sample: 0, done: 0 }
      state.tasks.push(item)
      result = item
      modified = true
    } else if (path.startsWith('/tasks/') && ['PUT', 'DELETE'].includes(method)) {
      const i = state.tasks.findIndex((t) => t.id === path.slice('/tasks/'.length))
      if (i < 0) throw new LocalError('یادآور پیدا نشد.')
      if (method === 'DELETE') state.tasks.splice(i, 1)
      else {
        if (typeof body.done !== 'boolean') throw new LocalError('وضعیت یادآور معتبر نیست.')
        state.tasks[i].done = body.done ? 1 : 0
      }
      result = { ok: true }
      modified = true
    } else if (path === '/local/photos' && method === 'POST') {
      if (!(options.body instanceof FormData)) throw new LocalError('تصویر دریافت نشد.')
      if (state.reports.length >= 500)
        throw new LocalError('سقف ایمنی ۵۰۰ عکس روی دستگاه تکمیل شده است.')
      const form = options.body
      const image = form.get('image')
      if (!(image instanceof File)) throw new LocalError('تصویر انتخاب کنید.')
      const part = text(form.get('tree_part'), 'بخش درخت', 30, 1)
      if (!['برگ', 'میوه', 'شاخه و تنه', 'کل درخت', 'ریشه و طوقه', 'گل و جوانه'].includes(part))
        throw new LocalError('بخش درخت معتبر نیست.')
      const notes = text(form.get('notes') ?? '', 'یادداشت', 1000)
      const orchard = orchardId(state, form.get('orchard_id'))
      const context = form.get('context')
        ? validateContext(JSON.parse(String(form.get('context'))))
        : { ...EMPTY_CONTEXT }
      const extra = form.getAll('additional_images')
      if (extra.length > 3 || extra.some((f) => !(f instanceof File)))
        throw new LocalError('حداکثر چهار تصویر برای هر پرونده انتخاب کنید.')
      const images = [await normalizedPhoto(image)]
      for (const f of extra) images.push(await normalizedPhoto(f as File))
      const record: Report = {
        id: uid(),
        orchard_id: orchard,
        orchard_name: state.orchards.find((o) => o.id === orchard)?.name ?? null,
        tree_part: part,
        notes,
        data: photoData(part, notes),
        image_url: images[0],
        image_urls: images,
        context,
        created_at: new Date().toISOString(),
        is_sample: 0,
      }
      state.reports.unshift(record)
      result = record
      modified = true
    } else if (path === '/local/vision' && method === 'GET') result = visionStatus()
    else if (path === '/local/vision' && method === 'PUT') {
      saveDirectSettings(
        String(body.model ?? ''),
        body.key === undefined ? undefined : String(body.key)
      )
      result = visionStatus()
    } else if (path === '/local/vision' && method === 'DELETE') {
      clearDirectSettings()
      result = visionStatus()
    } else if (path === '/local/vision/test' && method === 'POST') {
      // A text-only call: it proves key, model and network; it does not prove image accuracy.
      await testDirectConnection()
      result = visionStatus()
    } else if (path === '/local/analyses' && method === 'POST') {
      const settings = directSettings()
      if (!settings.key)
        throw new LocalError(
          'تحلیل عکس روی این دستگاه فعال نیست؛ کلید شخصی خود را در بخش تنظیمات ثبت کنید.'
        )
      if (body.consent !== true)
        throw new LocalError('برای ارسال تصویر به Google، رضایت آگاهانه لازم است.')
      const report = state.reports.find((r) => r.id === String(body.report_id ?? ''))
      if (!report) throw new LocalError('پرونده عکس پیدا نشد.')
      const analysis = await analyzePhotosDirect(
        report.image_urls?.length ? report.image_urls : [report.image_url ?? ''],
        report.context ?? { ...EMPTY_CONTEXT }
      )
      report.data = analysis
      result = report
      modified = true
    } else if (path.startsWith('/local/analyses/') && method === 'DELETE') {
      const report = state.reports.find((r) => r.id === path.slice('/local/analyses/'.length))
      if (!report) throw new LocalError('پرونده عکس پیدا نشد.')
      // Delete the screening text only; the photo and notes the farmer saved stay untouched.
      report.data = photoData(report.tree_part, report.notes)
      result = { ok: true }
      modified = true
    } else if (path === '/local/lab-analyses' && method === 'GET') result = state.assessments
    else if (path === '/local/lab-analyses' && method === 'POST') {
      if (!directSettings().key)
        throw new LocalError(
          'تفسیر هوشمند آزمایش روی این دستگاه فعال نیست؛ کلید شخصی خود را ثبت کنید.'
        )
      if (body.consent !== true)
        throw new LocalError('برای ارسال اعداد آزمایش به Google، رضایت آگاهانه لازم است.')
      const sample = validateField('labs', body.sample) as LabInput
      orchardId(state, sample.orchard_id)
      const linked = state.orchards.find((o) => o.id === sample.orchard_id)
      const context: DiagnosticContext = {
        ...EMPTY_CONTEXT,
        province: linked?.province ?? '',
        cultivar: linked?.cultivar ?? '',
        age: linked ? String(linked.age) : '',
        irrigation: linked?.irrigation ?? '',
      }
      const { result: assessment, units, calculations } = await interpretLabDirect(sample, context)
      if (state.assessments.length >= 200) state.assessments.length = 199
      const record: LabAssessment = {
        id: uid(),
        created_at: new Date().toISOString(),
        input: sample,
        units,
        calculations,
        result: assessment as LabAssessment['result'],
      }
      state.assessments.unshift(record)
      result = record
      modified = true
    } else if (path.startsWith('/local/lab-analyses/') && method === 'DELETE') {
      const i = state.assessments.findIndex(
        (r) => r.id === path.slice('/local/lab-analyses/'.length)
      )
      if (i < 0) throw new LocalError('تفسیر آزمایش پیدا نشد.')
      state.assessments.splice(i, 1)
      result = { ok: true }
      modified = true
    } else if (path.startsWith('/reports/') && method === 'DELETE') {
      const i = state.reports.findIndex((r) => r.id === path.slice('/reports/'.length))
      if (i < 0) throw new LocalError('پرونده عکس پیدا نشد.')
      state.reports.splice(i, 1)
      result = { ok: true }
      modified = true
    } else if (path === '/billing/config' && method === 'GET') result = billingConfig(state)
    else if (path === '/billing/my' && method === 'GET')
      result = {
        balance: 0,
        purchased: receiptsTotal(state.billing.receipts),
        used: 0,
        receipts: [],
        history: [],
      }
    else if (path === '/local/billing' && method === 'GET') result = billingView(state)
    else if (path === '/local/billing' && method === 'PUT') {
      // The owner's own destination card. Arithmetic cannot tell 6063…9401 from
      // 9401…6063, so an explicit confirmation of the typed digits is required.
      const checked = validateCard(body)
      const previous = state.billing.card
      state.billing.card = {
        ...checked,
        confirmed_at: new Date().toISOString(),
        updated_at: previous ? previous.updated_at : new Date().toISOString(),
      }
      result = billingView(state)
      modified = true
    } else if (path === '/local/billing/card' && method === 'DELETE') {
      state.billing.card = null
      result = billingView(state)
      modified = true
    } else if (path === '/local/billing/receipts' && method === 'POST') {
      const checked = validateReceipt(body)
      if (state.billing.receipts.length >= 500)
        throw new LocalError('سقف ۵۰۰ دریافت در این دستگاه پر شده است.')
      const record: LocalReceipt = {
        ...checked,
        id: uid(),
        created_at: new Date().toISOString(),
      }
      state.billing.receipts.unshift(record)
      result = record
      modified = true
    } else if (path.startsWith('/local/billing/receipts/') && method === 'DELETE') {
      const id = path.slice('/local/billing/receipts/'.length)
      const i = state.billing.receipts.findIndex((r) => r.id === id)
      if (i < 0) throw new LocalError('دریافت ثبت‌شده پیدا نشد.')
      state.billing.receipts.splice(i, 1)
      result = { ok: true }
      modified = true
    } else if (path.startsWith('/billing/'))
      throw new LocalError(
        'درگاه بانکی و تأیید خودکار واریز در نسخه مستقل وجود ندارد؛ فقط دفتر دریافت دستی در پنل مدیر فعال است.'
      )
    else if (path.startsWith('/field-records/')) {
      const [kind, recordId] = path.slice('/field-records/'.length).split('/') as [
        FieldKind,
        string | undefined,
      ]
      if (!Object.prototype.hasOwnProperty.call(state.fields, kind))
        throw new LocalError('نوع داده معتبر نیست.')
      const records = state.fields[kind]
      if (method === 'GET' && !recordId) result = records
      else if (method === 'POST' && !recordId) {
        if (records.length >= 500)
          throw new LocalError('سقف ایمن ۵۰۰ پرونده برای این بخش تکمیل شده است.')
        const data = validateField(kind, body)
        if (kind === 'labs') orchardId(state, (data as import('./fieldwork').LabInput).orchard_id)
        const record = {
          id: uid(),
          data,
          author: 'باغدار پستینو',
          visibility: 'private' as const,
          created_at: new Date().toISOString(),
        }
        records.unshift(record)
        result = record
        modified = true
      } else if (method === 'DELETE' && recordId) {
        const i = records.findIndex((r) => r.id === recordId)
        if (i < 0) throw new LocalError('پرونده پیدا نشد.')
        records.splice(i, 1)
        result = { ok: true }
        modified = true
      } else throw new LocalError('عملیات معتبر نیست.')
    } else if (
      path.startsWith('/auth/') ||
      path.startsWith('/admin/') ||
      path === '/analyses' ||
      path.startsWith('/lab-analyses') ||
      path.startsWith('/payments/')
    ) {
      throw new LocalError(
        'این نسخه مستقل و رایگان است؛ ورود اینترنتی، تشخیص هوشمند و پرداخت ندارد.'
      )
    } else throw new LocalError('این عملیات در نسخه مستقل پشتیبانی نمی‌شود.')
    if (modified) await save(state)
    // JSON-only state: avoid requiring structuredClone in older Android WebViews.
    return JSON.parse(JSON.stringify(result)) as T
  })
}
function id(value: unknown) {
  const result = text(value, 'شناسه', 80, 1)
  if (!/^[a-zA-Z0-9-]+$/.test(result)) throw new LocalError('شناسه فایل پشتیبان معتبر نیست.')
  return result
}
function uniqueIds(records: { id: string }[]) {
  if (new Set(records.map((r) => r.id)).size !== records.length)
    throw new LocalError('شناسه‌های تکراری در فایل پشتیبان وجود دارد.')
}
export function validateBackup(content: string): State {
  if (new TextEncoder().encode(content).byteLength > MAX_BACKUP_BYTES)
    throw new LocalError('فایل پشتیبان باید کمتر از ۳۲ مگابایت باشد.')
  let raw: Record<string, unknown>
  try {
    raw = object(JSON.parse(content.replace(/^\uFEFF/, '')))
  } catch {
    throw new LocalError('فایل پشتیبان قابل خواندن نیست.')
  }
  if (raw.app !== 'pestino' || raw.version !== 1)
    throw new LocalError('فایل، پشتیبان نسخه مستقل پستینو نیست.')
  if (
    !Array.isArray(raw.orchards) ||
    !Array.isArray(raw.tasks) ||
    !Array.isArray(raw.reports) ||
    raw.orchards.length > 500 ||
    raw.tasks.length > 2000 ||
    raw.reports.length > 500
  )
    throw new LocalError('مجموعه داده‌های پشتیبان معتبر نیست.')
  const state = emptyState()
  state.orchards = raw.orchards.map((value) => {
    const o = object(value)
    return { ...orchardInput(o), id: id(o.id), is_sample: 0 }
  })
  uniqueIds(state.orchards)
  state.tasks = raw.tasks.map((value) => {
    const t = object(value)
    return {
      ...taskInput(state, t),
      id: id(t.id),
      done: number(t.done, 'وضعیت', 0, 1, true),
      is_sample: 0,
    }
  })
  uniqueIds(state.tasks)
  state.reports = raw.reports.map((value) => {
    const r = object(value)
    const part = text(r.tree_part, 'بخش درخت', 30, 1)
    if (!['برگ', 'میوه', 'شاخه و تنه', 'کل درخت', 'ریشه و طوقه', 'گل و جوانه'].includes(part))
      throw new LocalError('بخش درخت معتبر نیست.')
    const notes = text(r.notes, 'یادداشت', 1000)
    const image = text(r.image_url, 'عکس', 12000000, 1)
    if (!/^data:image\/jpeg;base64,[A-Za-z0-9+/]+={0,2}$/.test(image))
      throw new LocalError('عکس پشتیبان باید JPEG محلی باشد؛ لینک و تصویر SVG پذیرفته نمی‌شود.')
    const extraImages = r.image_urls === undefined ? [image] : r.image_urls
    if (
      !Array.isArray(extraImages) ||
      extraImages.length < 1 ||
      extraImages.length > 4 ||
      extraImages[0] !== image ||
      extraImages.some(
        (v) =>
          typeof v !== 'string' ||
          v.length > 12000000 ||
          !/^data:image\/jpeg;base64,[A-Za-z0-9+/]+={0,2}$/.test(v)
      )
    )
      throw new LocalError('عکس پشتیبان باید JPEG محلی باشد.')
    const context = r.context ? validateContext(r.context) : { ...EMPTY_CONTEXT }
    const created = text(r.created_at, 'زمان ثبت', 40, 1)
    if (Number.isNaN(Date.parse(created))) throw new LocalError('زمان ثبت معتبر نیست.')
    const orchard = orchardId(state, r.orchard_id)
    return {
      id: id(r.id),
      orchard_id: orchard,
      orchard_name: state.orchards.find((o) => o.id === orchard)?.name ?? null,
      tree_part: part,
      notes,
      data: photoData(part, notes),
      image_url: image,
      image_urls: extraImages as string[],
      context,
      created_at: created,
      is_sample: 0,
    }
  })
  uniqueIds(state.reports)
  if (raw.billing !== undefined) {
    const billing = object(raw.billing)
    state.billing = emptyBilling()
    if (billing.card) {
      const checked = validateCard({ ...object(billing.card), confirmed: true })
      const card = object(billing.card)
      state.billing.card = {
        ...checked,
        confirmed_at: text(card.confirmed_at, 'تأیید کارت', 40, 1),
        updated_at: text(card.updated_at, 'به‌روزرسانی کارت', 40, 1),
      }
    }
    if (billing.receipts !== undefined) {
      if (!Array.isArray(billing.receipts) || billing.receipts.length > 500)
        throw new LocalError('دفتر دریافت‌های پشتیبان معتبر نیست.')
      state.billing.receipts = billing.receipts.map((value) => {
        const r = object(value)
        return {
          ...validateReceipt(r),
          id: id(r.id),
          created_at: text(r.created_at, 'زمان ثبت', 40, 1),
        }
      })
      uniqueIds(state.billing.receipts)
    }
  }
  if (raw.assessments !== undefined) {
    if (!Array.isArray(raw.assessments) || raw.assessments.length > 200)
      throw new LocalError('تاریخچه تفسیر آزمایش معتبر نیست.')
    state.assessments = raw.assessments.map((value) => {
      const a = object(value)
      const sample = validateField('labs', a.input) as LabInput
      const result = object(a.result)
      const units = object(a.units ?? {})
      return {
        id: id(a.id),
        created_at: text(a.created_at, 'زمان ثبت', 40, 1),
        input: sample,
        units: Object.fromEntries(Object.entries(units).map(([k, v]) => [k, text(v, 'واحد', 40)])),
        calculations: Array.isArray(a.calculations)
          ? a.calculations.slice(0, 8).map((c) => {
              const item = object(c)
              return {
                key: text(item.key, 'کلید', 20, 1),
                label: text(item.label, 'برچسب', 80, 1),
                value: number(item.value, 'مقدار', -1000000, 1000000),
                formula: text(item.formula, 'فرمول', 200),
              }
            })
          : [],
        result: result as unknown as LabAssessment['result'],
      }
    })
    uniqueIds(state.assessments)
  }
  if (raw.fields !== undefined) {
    const fields = object(raw.fields)
    for (const kind of ['labs', 'experiences', 'prices', 'climate'] as FieldKind[]) {
      const records = fields[kind] ?? []
      if (!Array.isArray(records) || records.length > 500)
        throw new LocalError('پرونده‌های پشتیبان معتبر نیستند.')
      state.fields[kind] = records.map((value) => {
        const r = object(value),
          data = validateField(kind, r.data)
        if (kind === 'labs') orchardId(state, (data as import('./fieldwork').LabInput).orchard_id)
        const created = text(r.created_at, 'زمان ثبت', 40, 1)
        if (Number.isNaN(Date.parse(created))) throw new LocalError('زمان ثبت معتبر نیست.')
        return {
          id: id(r.id),
          created_at: created,
          author: 'باغدار پستینو',
          visibility: 'private' as const,
          data,
        }
      })
      uniqueIds(state.fields[kind])
    }
  }
  return state
}
export async function exportBackup(): Promise<string> {
  return serialize(async () => JSON.stringify({ app: 'pestino', ...(await load()) }, null, 2))
}
export async function restoreBackup(content: string): Promise<void> {
  const replacement = validateBackup(content)
  await serialize(() => save(replacement))
}
export async function eraseLocalData(): Promise<void> {
  await serialize(() => save(emptyState()))
  localStorage.removeItem('pesteyar-bookmarks:local-device')
}
