/**
 * Owner bookkeeping for the offline edition: the destination card and a manual receipt
 * ledger. There is no payment gateway here — no bank verification happens, and the app
 * never claims otherwise. Everything stays in the device database and the backup.
 */
export class AdminError extends Error {
  status = 400
}

export interface LocalCard {
  card_number: string
  holder: string
  bank: string
  confirmed_at: string
  updated_at: string
}
export interface LocalReceipt {
  id: string
  payer: string
  amount_toman: number
  paid_at: string
  reference: string
  note: string
  created_at: string
  /** Owner confirmation is what unlocks paid analyses; there is no automatic verification. */
  confirmed_at?: string | null
  granted_analyses?: number
}
export interface LocalBilling {
  card: LocalCard | null
  receipts: LocalReceipt[]
}

const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩'
/** Persian/Arabic-Indic digits and separators are normalised before validation. */
export function digitsOnly(value: unknown): string {
  if (typeof value !== 'string') return ''
  return [...value]
    .map((ch) => {
      const fa = FA_DIGITS.indexOf(ch)
      if (fa >= 0) return String(fa)
      const ar = AR_DIGITS.indexOf(ch)
      if (ar >= 0) return String(ar)
      return ch
    })
    .join('')
    .replace(/[\s\u200c\u200f\u202a-\u202e-]/g, '')
}
export function luhnValid(digits: string): boolean {
  if (!/^\d{16}$/.test(digits)) return false
  let sum = 0
  for (let i = 0; i < 16; i += 1) {
    let d = Number(digits[15 - i])
    if (i % 2 === 1) {
      d *= 2
      if (d > 9) d -= 9
    }
    sum += d
  }
  return sum % 10 === 0
}
export function grouped(value: string): string {
  return value.match(/.{1,4}/g)?.join(' - ') ?? value
}
function text(value: unknown, label: string, max: number, min = 1): string {
  if (typeof value !== 'string') throw new AdminError(`${label} معتبر نیست.`)
  const result = value.trim()
  if (result.length < min || result.length > max) throw new AdminError(`${label} معتبر نیست.`)
  return result
}
function stamp(value: unknown, label: string): string {
  const raw = text(value, label, 40)
  if (Number.isNaN(Date.parse(raw))) throw new AdminError(`${label} معتبر نیست.`)
  return raw
}

/**
 * Deliberately conservative: card order ambiguity (for example 6063…9401 versus
 * 9401…6063) cannot be solved by arithmetic, so the owner must confirm the number they
 * typed against the physical card before it may be shown to anyone.
 */
export function validateCard(raw: unknown): Omit<LocalCard, 'confirmed_at' | 'updated_at'> {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw))
    throw new AdminError('اطلاعات کارت معتبر نیست.')
  const body = raw as Record<string, unknown>
  const card_number = digitsOnly(body.card_number)
  if (!luhnValid(card_number))
    throw new AdminError('شماره کارت ۱۶ رقمی معتبر نیست؛ رقم‌ها را دوباره با کارت تطبیق دهید.')
  if (body.confirmed !== true)
    throw new AdminError('پیش از ذخیره، تأیید کنید که شماره را با کارت واقعی خود تطبیق داده‌اید.')
  return {
    card_number,
    holder: text(body.holder, 'نام صاحب کارت', 100, 3),
    bank: text(body.bank, 'نام بانک', 80, 2),
  }
}
export function validateReceipt(raw: unknown): Omit<LocalReceipt, 'id' | 'created_at'> {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw))
    throw new AdminError('اطلاعات دریافت معتبر نیست.')
  const body = raw as Record<string, unknown>
  const amount = Number(body.amount_toman)
  if (!Number.isInteger(amount) || amount < 1000 || amount > 500_000_000)
    throw new AdminError('مبلغ دریافت باید عددی بین ۱٬۰۰۰ و ۵۰۰٬۰۰۰٬۰۰۰ تومان باشد.')
  return {
    payer: text(body.payer, 'نام پرداخت‌کننده', 80, 2),
    amount_toman: amount,
    paid_at: stamp(body.paid_at, 'تاریخ واریز'),
    reference: text(body.reference, 'کد پیگیری', 60, 0),
    note: text(body.note, 'توضیح', 300, 0),
  }
}
export function emptyBilling(): LocalBilling {
  return { card: null, receipts: [] }
}
export function receiptsTotal(receipts: LocalReceipt[]): number {
  return receipts.reduce((sum, r) => sum + r.amount_toman, 0)
}

/** One row per capability the owner asked about, with its real state in this build. */
export interface Capability {
  key: string
  title: string
  group: 'تحلیل' | 'داده و محتوا' | 'سرویس‌های سروری' | 'انتشار'
  state: 'active' | 'setup' | 'offline-blocked'
  detail: string
  how?: string
}
export function capabilities(input: {
  keyPresent: boolean
  keyVerified: boolean
  model: string
  cardSaved: boolean
  receipts: number
  orchards: number
  reports: number
  analyzed: number
  labs: number
  /** Owner rule of 2026-10-13: two free analyses, then a paid Toman package. */
  packagePriced?: boolean
  freeLeft?: number
}): Capability[] {
  const model = input.model || 'تنظیم نشده'
  const vision = (key: string, title: string): Capability => ({
    key,
    title,
    group: 'تحلیل',
    state: !input.keyPresent ? 'setup' : input.keyVerified ? 'active' : 'setup',
    detail: !input.keyPresent
      ? 'کلید شخصی Google ثبت نشده است.'
      : input.keyVerified
        ? `اتصال با مدل ${model} آزموده شده است.`
        : `کلید ثبت شده اما آزمون اتصال موفق نشده؛ نتیجه‌ای ساخته نمی‌شود.`,
    how: input.keyPresent
      ? 'اگر دسترسی شبکه به Google برقرار نیست، آزمون اتصال را دوباره بزنید یا مسیر سروری را فعال کنید.'
      : 'کلید شخصی خود را از aistudio.google.com/apikey بسازید و در همین پنل ثبت و آزمون کنید.',
  })
  return [
    vision('vision-photo', 'تحلیل عکس برگ، میوه، شاخه، تنه، تاج و ریشه/طوقه'),
    vision('vision-lab', 'تفسیر آزمایش خاک و آب'),
    {
      key: 'sar',
      title: 'محاسبات علمی مستقل آزمایش (شوری، SAR، RSC، بُر)',
      group: 'تحلیل',
      state: 'active',
      detail: 'این محاسبات در خود برنامه و بدون اینترنت از اعداد واردشده انجام می‌شوند.',
    },
    {
      key: 'guides',
      title: '۲۶ راهنمای آموزشی پسته + ۲۴ رکورد پژوهش با منبع و تاریخ',
      group: 'داده و محتوا',
      state: 'active',
      detail: 'کامل آفلاین؛ با برچسب «غیربازبینی‌شده محلی» و محدودیت هر منبع.',
    },
    {
      key: 'entry',
      title: 'ورود باغدار بدون شماره همراه، ایمیل یا کد پیامکی',
      group: 'داده و محتوا',
      state: 'active',
      detail:
        'ورود با یک ضربه و بدون هیچ رمزی؛ رمز فقط اختیاری و برای قفل پنل مدیر است. حذف برنامه یا پاک‌کردن داده‌ها تنها راه از دست رفتن اطلاعات است، پس پشتیبان بگیرید.',
    },
    {
      key: 'field',
      title: 'باغ‌ها، پرونده‌ها، یادآورها، تجربه‌ها، بازار و اقلیم',
      group: 'داده و محتوا',
      state: 'active',
      detail: `${input.orchards} باغ · ${input.reports} پرونده عکس (${input.analyzed} تحلیل‌شده) · ${input.labs} آزمایش ثبت‌شده روی همین دستگاه.`,
    },
    {
      key: 'sales',
      title: 'فروش تحلیل: دو تحلیل رایگان، بعد بستهٔ تومانی',
      group: 'سرویس‌های سروری',
      state: input.packagePriced ? 'active' : 'setup',
      detail: input.packagePriced
        ? `هر دستگاه دو تحلیل رایگان دارد و بعد از آن بستهٔ تومانی لازم است؛ تحلیل رایگان باقی‌مانده روی این دستگاه: ${input.freeLeft ?? 0}. پرداخت کارت‌به‌کارت با کد فعال‌سازی است، نه درگاه بانکی.`
        : 'قیمت بستهٔ تحلیل هنوز تعیین نشده؛ تا آن زمان خریدار نمی‌داند چقدر بپردازد. در بخش «تحلیل رایگان، بستهٔ تومانی و کد فعال‌سازی» قیمت را وارد کنید.',
      how: 'قیمت تومانی را خودتان یا از دلار × نرخ روز تعیین کنید؛ کد فعال‌سازی را فقط پس از واریز واقعی بسازید.',
    },
    {
      key: 'ledger',
      title: 'دفتر دریافت وجه (ثبت دستی)',
      group: 'سرویس‌های سروری',
      state: input.cardSaved ? 'active' : 'setup',
      detail: input.cardSaved
        ? `کارت مقصد ثبت شده و ${input.receipts} دریافت در دفتر محلی است. تأیید واریز خودکار نیست و درگاه بانکی وجود ندارد.`
        : 'کارت مقصد ثبت نشده است؛ بدون آن هیچ راهنمای واریزی نمایش داده نمی‌شود.',
      how: 'شماره کارت، نام صاحب کارت و نام بانک را در همین پنل وارد و با کارت واقعی تطبیق کنید.',
    },
    {
      key: 'gateway',
      title: 'درگاه بانکی و اعتبار خودکار سروری',
      group: 'سرویس‌های سروری',
      state: 'offline-blocked',
      detail: 'به سرور فعال، حساب کاربری و تأیید بانکی نیاز دارد؛ در نسخه مستقل وجود ندارد.',
      how: 'با استقرار سرور پستینو (render.yaml) و فعال‌سازی صریح مالک امکان‌پذیر است.',
    },
    {
      key: 'sync',
      title: 'همگام‌سازی چند دستگاه و چند کاربر',
      group: 'سرویس‌های سروری',
      state: 'offline-blocked',
      detail: 'هر دستگاه داده خودش را دارد؛ انتقال با فایل پشتیبان رمزگذاری‌نشده انجام می‌شود.',
    },
    {
      key: 'weather',
      title: 'آب‌وهوا و هشدار یخبندان زنده',
      group: 'سرویس‌های سروری',
      state: 'offline-blocked',
      detail: 'نیازمند سرویس هواشناسی معتبر و کلید اختصاصی است؛ داده ساختگی نمایش داده نمی‌شود.',
    },
    {
      key: 'ios',
      title: 'نسخه iPhone (IPA)',
      group: 'انتشار',
      state: 'offline-blocked',
      detail:
        'نصب روی iPhone بدون حساب توسعه‌دهنده اپل (۷۹۹ دلار سالانه) ممکن نیست؛ نسخه وب روی آیفون کار می‌کند.',
    },
    {
      key: 'apk',
      title: 'فایل نصبی اندروید رایگان',
      group: 'انتشار',
      state: 'active',
      detail: 'همین نسخه ۰.۵.۰؛ نصب با اجازه «نصب از منابع نامشخص» و بدون Google Play.',
    },
  ]
}
