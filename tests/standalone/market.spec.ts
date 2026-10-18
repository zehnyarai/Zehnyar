import { test, expect } from '@playwright/test'
const origin = 'https://www.tahlilbazaar.com'
const article = `${origin}/news/434095/fixture`
const title = 'قیمت آجیل و خشکبار ۲۶ مهر ۱۴۰۵'
const table = `<h1>${title}</h1><table><tr><th>آجیل و خشکبار</th><th>قیمت درجه یک (ریال)</th></tr><tr><td>قیمت پسته اکبری</td><td>۳۰,۸۰۰,۰۰۰</td></tr><tr><td>قیمت پسته فندقی</td><td>۲۶,۱۰۰,۰۰۰</td></tr></table>`

test('continuous price typing works and automatic sourced quotes do not replace private observations', async ({
  page,
}) => {
  await page.clock.install({ time: new Date('2026-10-18T09:00:00Z') })
  await page.route(`${origin}/**`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: route.request().url().includes('/search?')
        ? `<a href="${article}">${title}</a>`
        : table,
    })
  )
  await page.goto('./#/market')
  const online = page.locator('.online-market')
  await expect(online).toContainText('۳٬۰۸۰٬۰۰۰')
  await expect(online).toContainText('مبنای وزن و اُنس در جدول منبع مشخص نیست')
  await expect(online.getByRole('link')).toHaveAttribute('href', article)
  await page.getByRole('button', { name: 'ثبت قیمت', exact: true }).click()
  for (const [name, text] of [
    ['قیمت هر کیلوگرم *', '2750000'],
    ['استان / بازار *', 'رفسنجان'],
    ['نوع، اُنس و درجه محصول', 'خشک با پوست انس ۲۶–۲۸'],
    ['منبع قیمت *', 'مشاهده خصوصی آزمایشی'],
  ]) {
    const input = page.getByLabel(name, { exact: true })
    await input.pressSequentially(text, { delay: 15 })
    await expect(input).toHaveValue(text)
    await expect(input).toBeFocused()
  }
  await page.getByRole('button', { name: 'ثبت مشاهده', exact: true }).click()
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await page.reload()
  await expect(page.locator('.market-prices')).toContainText('مشاهده خصوصی آزمایشی')
  await expect(online).toContainText('۳٬۰۸۰٬۰۰۰')
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
})

test('a freshly fetched old report never becomes today’s price', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-10-18T09:00:00Z') })
  await page.route(`${origin}/**`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: route.request().url().includes('/search?')
        ? `<a href="${article}">${title.replace('۲۶', '۲۵')}</a>`
        : table.replace('۲۶ مهر', '۲۵ مهر'),
    })
  )
  await page.goto('./#/market')
  await expect(page.locator('.online-market')).toContainText('گزارش قدیمی؛ نه قیمت امروز')
})

test('live public source adapter smoke (not a phone-network or market-price accuracy certification)', async ({
  page,
  request,
}) => {
  test.skip(
    process.env.PESTINO_LIVE_MARKET !== '1',
    'Optional public-network smoke; ordinary tests use fixtures.'
  )
  test.setTimeout(90000)
  // The CI request context reads the publisher's raw HTML. Fulfilling it locally isolates
  // the parser from browser CORS; Android uses native HTTP, NOT this test interception.
  await page.route(`${origin}/**`, async (route) => {
    try {
      const response = await request.get(route.request().url(), { timeout: 20000 })
      await route.fulfill({ response })
    } catch {
      await route.fulfill({ status: 503, body: '' })
    }
  })
  await page.goto('./#/market')
  await page
    .locator('.online-market .online-price-row, .online-market .info-banner.warning')
    .first()
    .waitFor({ timeout: 65000 })
  const count = await page.locator('.online-price-row').count()
  test.skip(
    !count,
    'Public source unavailable or format changed; app failed closed without invented rates.'
  )
  const cached = await page.evaluate(() =>
    JSON.parse(localStorage.getItem('pestino-market-quotes-v1') ?? 'null')
  )
  expect(cached.url).toMatch(/^https:\/\/www\.tahlilbazaar\.com\/news\/\d+\//)
  expect(cached.rows.length).toBeGreaterThan(0)
  console.log(
    `::notice title=Live market adapter::Fetched raw publisher report ${cached.report_date}, ${count} pistachio rows, explicit currency conversion; no owner key, no inferred weight basis. Phone connectivity and accuracy of publisher rates are NOT certified.`
  )
})
