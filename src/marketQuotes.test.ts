// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest'
import {
  MARKET_ORIGIN,
  MARKET_SEARCH,
  marketArticles,
  parseMarketArticle,
  reportDate,
  marketDate,
  refreshMarketQuotes,
  cachedMarketQuotes,
} from './marketQuotes'
const now = new Date('2026-10-18T09:00:00Z')
const url = `${MARKET_ORIGIN}/news/434095/example`
const table = (unit = 'ریال', value = '۳۰,۸۰۰,۰۰۰') =>
  `<h1>قیمت آجیل و خشکبار ۲۶ مهر ۱۴۰۵</h1><table><tr><th>آجیل و خشکبار</th><th>قیمت درجه یک (${unit})</th></tr><tr><td>قیمت پسته اکبری</td><td>${value}</td></tr><tr><td>قیمت خلال پسته</td><td>۷۹,۸۰۰,۰۰۰</td></tr></table>`
afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
  localStorage.clear()
})
it('uses the headline date, distinguishes Tehran midnight, and never converts fetch time into report time', () => {
  expect(reportDate('قیمت آجیل و خشکبار ۲۶ مهر ۱۴۰۵', now)).toBe('2026-10-18')
  expect(reportDate('قیمت آجیل و خشکبار ۲۵ مهر ۱۴۰۵', now)).toBe('2026-10-17')
  expect(reportDate('قیمت امروز', now)).toBeNull()
  expect(reportDate('قیمت آجیل و خشکبار ۲۷ مهر ۱۴۰۵', now)).toBeNull()
  expect(marketDate(new Date('2026-10-18T21:00:00Z'))).toBe('2026-10-19')
})
it('selects only dated, same-origin report links in newest-first order', () => {
  const html = `<a href="/news/1/old">قیمت آجیل و خشکبار ۲۵ مهر ۱۴۰۵</a><a href="${url}">قیمت آجیل و خشکبار ۲۶ مهر ۱۴۰۵</a><a href="https://evil.invalid/news/123">قیمت آجیل و خشکبار ۲۶ مهر ۱۴۰۵</a><a href="/news/3">قیمت امروز</a>`
  expect(marketArticles(html, now).map((r) => r.url)).toEqual([url, `${MARKET_ORIGIN}/news/1/old`])
})
it('converts explicit rial to toman, excludes kernels/slivers, and does NOT invent kilogram/ounce basis', () => {
  const quote = parseMarketArticle(table(), url, now)
  expect(quote.rows).toEqual([
    {
      cultivar: 'اکبری',
      toman: 3080000,
      reported_amount: 30800000,
      reported_currency: 'rial',
      weight_basis: 'unspecified',
    },
  ])
  expect(quote.report_date).toBe('2026-10-18')
  expect(parseMarketArticle(table('تومان', '۳,۰۸۰,۰۰۰'), url, now).rows[0].toman).toBe(3080000)
})
it('rejects missing/ambiguous currency, malformed amounts, unknown date and poisoned article URLs', () => {
  for (const html of [
    table(''),
    table('ریال و تومان'),
    table('ریال', '۳۰,۸۰,۰۰۰'),
    table().replace('۲۶ مهر ۱۴۰۵', 'امروز'),
  ])
    expect(() => parseMarketArticle(html, url, now)).toThrow()
  expect(() => parseMarketArticle(table(), 'https://evil.invalid/news/1', now)).toThrow()
})
it('keeps old report dates old even when freshly downloaded', () => {
  expect(parseMarketArticle(table().replace('۲۶ مهر', '۲۵ مهر'), url, now).report_date).toBe(
    '2026-10-17'
  )
})
it('rejects contradictory prices for the same cultivar', () => {
  const html = table().replace(
    '</table>',
    '<tr><td>قیمت پسته اکبری</td><td>۴۰,۰۰۰,۰۰۰</td></tr></table>'
  )
  expect(() => parseMarketArticle(html, url, now)).toThrow('متناقض')
})
it('fetches without keys/cookies and preserves the last cached report on a failed refresh', async () => {
  vi.useFakeTimers()
  vi.setSystemTime(now)
  const fetch = vi.fn(async (request: string, init: RequestInit) => {
    expect(init.credentials).toBe('omit')
    expect(JSON.stringify(init)).not.toMatch(/Authorization|AIza|xai-/)
    return new Response(
      request === MARKET_SEARCH ? `<a href="${url}">قیمت آجیل و خشکبار ۲۶ مهر ۱۴۰۵</a>` : table()
    )
  })
  vi.stubGlobal('fetch', fetch)
  const data = await refreshMarketQuotes()
  expect(data.rows[0].toman).toBe(3080000)
  expect(fetch).toHaveBeenCalledTimes(2)
  const saved = cachedMarketQuotes()
  expect(saved?.report_date).toBe('2026-10-18')
  fetch.mockRejectedValue(new Error('offline'))
  await expect(refreshMarketQuotes()).rejects.toThrow()
  expect(cachedMarketQuotes()).toEqual(saved)
})
