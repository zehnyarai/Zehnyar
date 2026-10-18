import { Capacitor, CapacitorHttp } from '@capacitor/core'

export const MARKET_ORIGIN = 'https://www.tahlilbazaar.com'
export const MARKET_SEARCH = `${MARKET_ORIGIN}/search?q=${encodeURIComponent('قیمت آجیل و خشکبار')}`
const CACHE_KEY = 'pestino-market-quotes-v1'
export interface MarketQuote {
  cultivar: string
  toman: number
  reported_amount: number
  reported_currency: 'rial' | 'toman'
  weight_basis: 'kg' | 'unspecified'
}
export interface MarketQuotes {
  version: 1
  source: 'خبرگزاری بازار'
  url: string
  report_date: string
  fetched_at: string
  rows: MarketQuote[]
}
const digits = (value: string) =>
  value.replace(/[۰-۹٠-٩]/g, (d) =>
    String('۰۱۲۳۴۵۶۷۸۹'.includes(d) ? '۰۱۲۳۴۵۶۷۸۹'.indexOf(d) : '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
  )
const normal = (s: string) =>
  digits(s)
    .replace(/ي/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/\u200c/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
export function marketDate(now = new Date()): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tehran',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(now)
  return ['year', 'month', 'day'].map((k) => parts.find((p) => p.type === k)!.value).join('-')
}
/** Use the dated headline, NEVER fetch time or "today" in boilerplate as an observation date. */
export function reportDate(title: string, now = new Date()): string | null {
  const match = normal(title).match(
    /^قیمت آجیل و خشکبار\s+(\d{1,2})\s+(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)\s+(\d{4})$/
  )
  if (!match) return null
  const formatter = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
    timeZone: 'Asia/Tehran',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
  for (let day = 0; day < 45; day++) {
    const date = new Date(now.getTime() - day * 86400000)
    const parts = formatter.formatToParts(date)
    const value = (key: string) => normal(parts.find((p) => p.type === key)?.value ?? '')
    if (
      Number(value('day')) === Number(match[1]) &&
      value('month') === match[2] &&
      value('year') === match[3]
    )
      return marketDate(date)
  }
  return null
}
export function allowedMarketUrl(value: string): boolean {
  try {
    const url = new URL(value)
    return (
      url.origin === MARKET_ORIGIN &&
      /^\/news\/\d+(?:\/[^?#]*)?$/.test(url.pathname) &&
      !url.search &&
      !url.hash &&
      !url.username &&
      !url.password
    )
  } catch {
    return false
  }
}
export function marketArticles(html: string, now = new Date()): { url: string; date: string }[] {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const found = new Map<string, { url: string; date: string }>()
  for (const node of doc.querySelectorAll('a[href]')) {
    const date = reportDate(node.textContent ?? '', now)
    if (!date) continue
    try {
      const url = new URL(node.getAttribute('href')!, MARKET_ORIGIN).href
      if (allowedMarketUrl(url)) found.set(url, { url, date })
    } catch {
      /* Skip malformed/outside-source links. */
    }
  }
  return [...found.values()].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 3)
}
export function parseMarketArticle(html: string, url: string, now = new Date()): MarketQuotes {
  if (!allowedMarketUrl(url) || html.length > 2000000) throw new Error('منبع قیمت قابل تأیید نیست.')
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const date = reportDate(doc.querySelector('h1')?.textContent ?? '', now)
  if (!date) throw new Error('تاریخ واقعی گزارش قیمت قابل خواندن نیست؛ نرخ روز ساخته نشد.')
  const rows: MarketQuote[] = []
  for (const table of doc.querySelectorAll('table')) {
    const header = normal(table.querySelector('tr')?.textContent ?? '')
    if (!header.includes('قیمت') || !header.includes('درجه یک')) continue
    const rial = header.includes('ریال'),
      toman = header.includes('تومان')
    if (rial === toman) continue // Missing/ambiguous currency is never guessed.
    const weight = /کیلوگرم|کیلو گرم|هر کیلو|\bkg\b/i.test(header) ? 'kg' : 'unspecified'
    for (const tr of table.querySelectorAll('tr')) {
      const cells = tr.querySelectorAll('td,th')
      if (cells.length !== 2) continue
      const name = normal(cells[0].textContent ?? '').replace(/\s/g, '')
      const cultivar = ['احمدآقایی', 'اکبری', 'فندقی'].find((c) => name === `قیمتپسته${c}`)
      if (!cultivar) continue
      const value = normal(cells[1].textContent ?? '')
      if (!/^(?:\d{1,3}(?:[,٬]\d{3})+|\d{4,10})$/.test(value)) continue
      const amount = Number(value.replace(/[,٬]/g, ''))
      const converted = rial ? amount / 10 : amount
      if (!Number.isFinite(converted) || converted <= 0 || converted > 1000000000) continue
      if (rows.some((r) => r.cultivar === cultivar && r.toman !== converted))
        throw new Error('جدول گزارش قیمت‌های متناقض دارد؛ نرخ انتخاب نشد.')
      if (!rows.some((r) => r.cultivar === cultivar))
        rows.push({
          cultivar,
          toman: converted,
          reported_amount: amount,
          reported_currency: rial ? 'rial' : 'toman',
          weight_basis: weight,
        })
    }
  }
  if (!rows.length)
    throw new Error('جدول قیمتِ دارای واحد مشخص از منبع دریافت نشد؛ قیمت حدس زده نشد.')
  return {
    version: 1,
    source: 'خبرگزاری بازار',
    url,
    report_date: date,
    fetched_at: now.toISOString(),
    rows,
  }
}
export function cachedMarketQuotes(): MarketQuotes | null {
  try {
    const data = JSON.parse(localStorage.getItem(CACHE_KEY) ?? 'null')
    if (
      !data ||
      data.version !== 1 ||
      data.source !== 'خبرگزاری بازار' ||
      !allowedMarketUrl(data.url) ||
      !/^\d{4}-\d{2}-\d{2}$/.test(data.report_date) ||
      !Number.isFinite(Date.parse(data.report_date)) ||
      !Number.isFinite(Date.parse(data.fetched_at)) ||
      !Array.isArray(data.rows) ||
      data.rows.length < 1 ||
      data.rows.length > 3
    )
      return null
    if (
      data.rows.some(
        (r: MarketQuote) =>
          !r ||
          !['احمدآقایی', 'اکبری', 'فندقی'].includes(r.cultivar) ||
          !Number.isFinite(r.toman) ||
          r.toman <= 0 ||
          r.toman > 1000000000 ||
          !Number.isFinite(r.reported_amount) ||
          !['rial', 'toman'].includes(r.reported_currency) ||
          (r.reported_currency === 'rial' ? r.reported_amount / 10 : r.reported_amount) !==
            r.toman ||
          !['kg', 'unspecified'].includes(r.weight_basis)
      )
    )
      return null
    return data as MarketQuotes
  } catch {
    return null
  }
}
async function sourceHtml(url: string): Promise<string> {
  if (url !== MARKET_SEARCH && !allowedMarketUrl(url)) throw new Error('نشانی منبع قیمت مجاز نیست.')
  let text: string
  if (Capacitor.isNativePlatform()) {
    const response = await CapacitorHttp.request({
      url,
      method: 'GET',
      responseType: 'text',
      connectTimeout: 15000,
      readTimeout: 20000,
      headers: { Accept: 'text/html' },
    })
    if (response.status !== 200 || typeof response.data !== 'string')
      throw new Error('منبع قیمت پاسخ معتبر نداد.')
    text = response.data
  } else {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 20000)
    try {
      const response = await fetch(url, {
        credentials: 'omit',
        signal: controller.signal,
        headers: { Accept: 'text/html' },
      })
      if (!response.ok) throw new Error('منبع قیمت در دسترس نیست.')
      text = await response.text()
    } finally {
      clearTimeout(timeout)
    }
  }
  if (text.length > 2000000) throw new Error('پاسخ منبع بیش از حد بزرگ بود.')
  return text
}
let inFlight: Promise<MarketQuotes> | null = null
export async function refreshMarketQuotes(): Promise<MarketQuotes> {
  if (inFlight) return inFlight
  inFlight = (async () => {
    const now = new Date()
    const articles = marketArticles(await sourceHtml(MARKET_SEARCH), now)
    for (const item of articles.slice(0, 2)) {
      try {
        const quotes = parseMarketArticle(await sourceHtml(item.url), item.url, now)
        if (quotes.report_date !== item.date) continue
        try {
          localStorage.setItem(CACHE_KEY, JSON.stringify(quotes))
        } catch {
          /* Live data is still shown; caching is best-effort. */
        }
        return quotes
      } catch {
        /* A dated older report is allowed, but is explicitly labelled old by the UI. */
      }
    }
    throw new Error(
      'گزارش تازهٔ قابل‌خواندن از منبع دریافت نشد. آخرین دادهٔ ذخیره‌شده، اگر وجود دارد، قیمت امروز محسوب نمی‌شود.'
    )
  })()
  try {
    return await inFlight
  } finally {
    inFlight = null
  }
}
