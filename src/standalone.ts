/** Local-only edition. No account, network API, payment or fabricated diagnosis. */
import type { AnalysisData, Bootstrap, Knowledge, Orchard, Report, Task } from './types'
import knowledgeData from './data/knowledge.json'
import { assetUrl } from './config'

const DB_NAME = 'pestino-local-v1'
const KEY = 'data'
const MAX_BACKUP_BYTES = 32 * 1024 * 1024
interface State {
  version: 1
  orchards: Orchard[]
  tasks: Task[]
  reports: Report[]
}
export class LocalError extends Error {
  status = 400
}
const emptyState = (): State => ({ version: 1, orchards: [], tasks: [], reports: [] })
const uid = () => crypto.randomUUID()
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
    req.onsuccess = () => resolve(req.result ?? emptyState())
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
const services = {
  vision_configured: false,
  vision_provider: 'none',
  payment_configured: false,
  payment_sandbox: true,
  knowledge_version: knowledgeData.version,
  knowledge_reviewed: false,
  weather_configured: false,
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
    services,
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
      if (!['برگ', 'میوه', 'شاخه و تنه', 'کل درخت', 'ریشه و طوقه'].includes(part))
        throw new LocalError('بخش درخت معتبر نیست.')
      const notes = text(form.get('notes') ?? '', 'یادداشت', 1000)
      const orchard = orchardId(state, form.get('orchard_id'))
      const record: Report = {
        id: uid(),
        orchard_id: orchard,
        orchard_name: state.orchards.find((o) => o.id === orchard)?.name ?? null,
        tree_part: part,
        notes,
        data: photoData(part, notes),
        image_url: await normalizedPhoto(image),
        created_at: new Date().toISOString(),
        is_sample: 0,
      }
      state.reports.unshift(record)
      result = record
      modified = true
    } else if (path.startsWith('/reports/') && method === 'DELETE') {
      const i = state.reports.findIndex((r) => r.id === path.slice('/reports/'.length))
      if (i < 0) throw new LocalError('پرونده عکس پیدا نشد.')
      state.reports.splice(i, 1)
      result = { ok: true }
      modified = true
    } else if (
      path.startsWith('/auth/') ||
      path.startsWith('/admin/') ||
      path === '/analyses' ||
      path.startsWith('/payments/')
    ) {
      throw new LocalError(
        'این نسخه مستقل و رایگان است؛ ورود اینترنتی، تشخیص هوشمند و پرداخت ندارد.'
      )
    } else throw new LocalError('این عملیات در نسخه مستقل پشتیبانی نمی‌شود.')
    if (modified) await save(state)
    return structuredClone(result) as T
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
    if (!['برگ', 'میوه', 'شاخه و تنه', 'کل درخت', 'ریشه و طوقه'].includes(part))
      throw new LocalError('بخش درخت معتبر نیست.')
    const notes = text(r.notes, 'یادداشت', 1000)
    const image = text(r.image_url, 'عکس', 12000000, 1)
    if (!/^data:image\/jpeg;base64,[A-Za-z0-9+/]+={0,2}$/.test(image))
      throw new LocalError('عکس پشتیبان باید JPEG محلی باشد؛ لینک و تصویر SVG پذیرفته نمی‌شود.')
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
      created_at: created,
      is_sample: 0,
    }
  })
  uniqueIds(state.reports)
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
