import type { LabKind, LabValues } from './scientific'
import { interpretLab } from './scientific'

export const EXPERIENCE_CATEGORIES = ['مبارزه با آفات', 'کوددهی', 'آبیاری', 'برداشت', 'هرس', 'سایر']
export const CULTIVARS = ['احمدآقایی', 'اکبری', 'کله‌قوچی', 'فندقی', 'بادامی', 'سایر']
export interface LabInput {
  kind: LabKind
  values: LabValues
  method: string
  sample_date: string
  depth: string
  orchard_id: string | null
  notes: string
}
export interface ExperienceInput {
  title: string
  category: string
  body: string
  province: string
  cultivar: string
  season: string
}
export interface MarketInput {
  cultivar: string
  price: number
  currency: 'toman' | 'usd'
  province: string
  source: string
  observed_date: string
  grade: string
}
export interface ClimateInput {
  province: string
  observed_date: string
  minimum: number
  maximum: number
  humidity: number | null
  wind: number | null
  stage: string
  source: string
}
export type FieldKind = 'labs' | 'experiences' | 'prices' | 'climate'
export interface FieldPayloads {
  labs: LabInput
  experiences: ExperienceInput
  prices: MarketInput
  climate: ClimateInput
}
export type FieldRecord<K extends FieldKind> = {
  id: string
  created_at: string
  author: string
  visibility: 'private' | 'pending' | 'published'
  data: FieldPayloads[K]
}
const text = (value: unknown, label: string, max: number, min = 0) => {
  if (typeof value !== 'string' || value.trim().length < min || value.length > max)
    throw new Error(`${label} معتبر نیست.`)
  return value.trim()
}
const num = (value: unknown, label: string, min: number, max: number) => {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max)
    throw new Error(`${label} معتبر نیست.`)
  return value
}
export const validDate = (value: unknown) => {
  const date = text(value, 'تاریخ', 10, 10)
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
    Number.isNaN(Date.parse(date)) ||
    new Date(date).toISOString().slice(0, 10) !== date
  )
    throw new Error('تاریخ معتبر نیست.')
  return date
}
export function validateField<K extends FieldKind>(kind: K, raw: unknown): FieldPayloads[K] {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw))
    throw new Error('اطلاعات فرم معتبر نیست.')
  const b = raw as Record<string, unknown>
  let result: FieldPayloads[FieldKind]
  if (kind === 'labs') {
    if (!['soil', 'water'].includes(String(b.kind))) throw new Error('نوع آزمایش معتبر نیست.')
    if (
      !b.values ||
      typeof b.values !== 'object' ||
      Array.isArray(b.values) ||
      !Object.keys(b.values).length
    )
      throw new Error('مقادیر آزمایش را وارد کنید.')
    const method = text(b.method, 'روش آزمایش', 60, 1)
    if (!['saturated', '1:5', '1:2.5', 'unknown', 'water'].includes(method))
      throw new Error('روش آزمایش معتبر نیست.')
    if ((b.kind === 'water' && method !== 'water') || (b.kind === 'soil' && method === 'water'))
      throw new Error('روش آزمایش با نوع نمونه سازگار نیست.')
    const values = b.values as LabValues
    interpretLab(b.kind as LabKind, values, method)
    result = {
      kind: b.kind as LabKind,
      values: { ...values },
      method,
      sample_date: validDate(b.sample_date),
      depth: text(b.depth, 'عمق', 80),
      orchard_id: b.orchard_id ? text(b.orchard_id, 'باغ', 80, 1) : null,
      notes: text(b.notes, 'توضیحات', 1000),
    }
  } else if (kind === 'experiences') {
    if (!EXPERIENCE_CATEGORIES.includes(String(b.category)))
      throw new Error('دسته تجربه معتبر نیست.')
    result = {
      title: text(b.title, 'عنوان تجربه', 160, 3),
      category: String(b.category),
      body: text(b.body, 'متن تجربه', 4000, 20),
      province: text(b.province, 'استان', 60, 2),
      cultivar: text(b.cultivar, 'رقم', 60),
      season: text(b.season, 'فصل', 60),
    }
  } else if (kind === 'prices') {
    if (!['toman', 'usd'].includes(String(b.currency))) throw new Error('واحد قیمت معتبر نیست.')
    result = {
      cultivar: text(b.cultivar, 'رقم', 60, 2),
      price: num(b.price, 'قیمت', 0.01, 1000000000),
      currency: b.currency as 'toman' | 'usd',
      province: text(b.province, 'منطقه', 60, 2),
      source: text(b.source, 'منبع قیمت', 300, 3),
      observed_date: validDate(b.observed_date),
      grade: text(b.grade, 'درجه محصول', 120),
    }
  } else if (kind === 'climate') {
    const minimum = num(b.minimum, 'کمینه دما', -60, 65),
      maximum = num(b.maximum, 'بیشینه دما', -60, 65)
    if (minimum > maximum) throw new Error('کمینه دما نمی‌تواند بیشتر از بیشینه باشد.')
    result = {
      province: text(b.province, 'منطقه', 60, 2),
      observed_date: validDate(b.observed_date),
      minimum,
      maximum,
      humidity: b.humidity === null ? null : num(b.humidity, 'رطوبت', 0, 100),
      wind: b.wind === null ? null : num(b.wind, 'باد', 0, 300),
      stage: text(b.stage, 'مرحله رشد', 60),
      source: text(b.source, 'منبع', 300, 3),
    }
  } else throw new Error('نوع داده معتبر نیست.')
  return result as FieldPayloads[K]
}
export interface DollarPricing {
  mode: 'usd' | 'fixed'
  ready: boolean
  receiving_requested: boolean
  quote_id: string
  expires_at?: string | null
  confirmed?: boolean
  rate_toman_per_usd?: string | null
  rate_date?: string | null
  today?: string
  source?: string
  source_url?: string
  usd_prices?: Record<string, string>
  notice?: string
}
export interface BillingConfig {
  enabled: boolean
  card_number: string
  holder: string
  bank: string
  notice: string
  pricing?: DollarPricing
  packages: {
    id: string
    name: string
    analyses: number
    price_toman: number | null
    price_usd?: string | null
    description: string
  }[]
}
export const EMPTY_BILLING: BillingConfig = {
  enabled: false,
  card_number: '',
  holder: '',
  bank: '',
  notice:
    'دریافت وجه فعال نیست. هیچ واریزی انجام ندهید؛ این صفحه فقط ساختار اعتبار و رسید را نشان می‌دهد.',
  packages: [
    {
      id: 'trial',
      name: 'بسته آزمایشی',
      analyses: 10,
      price_toman: 290000,
      description: 'مناسب برای شروع و آشنایی',
    },
    {
      id: 'season',
      name: 'بسته فصلی',
      analyses: 40,
      price_toman: 990000,
      description: 'مناسب یک فصل باغداری',
    },
    {
      id: 'large',
      name: 'بسته باغ بزرگ',
      analyses: 120,
      price_toman: 2490000,
      description: 'مناسب باغ‌های چند هکتاری',
    },
  ],
}
export interface CreditReceipt {
  id: string
  name: string
  phone: string
  tracking: string
  package_id: string
  price_toman?: number
  analyses?: number
  price_snapshot?: {
    mode: string
    quote_id?: string
    price_usd?: string
    rate_toman_per_usd?: string
    rate_date?: string
    source?: string
    price_toman?: number
  }
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  image_url: string
  reason: string
}
export interface CreditAccount {
  balance: number
  purchased: number
  used: number
  receipts: CreditReceipt[]
  history: { id: string; reason: string; delta: number; created_at: string }[]
}
