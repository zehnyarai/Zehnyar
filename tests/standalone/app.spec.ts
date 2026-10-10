import { expect, test } from '@playwright/test'
import fs from 'node:fs/promises'

async function addOrchard(page: import('@playwright/test').Page) {
  await page.goto('./#/orchards')
  await page.getByRole('button', { name: 'ثبت باغ جدید' }).click()
  await page.getByLabel('نام باغ', { exact: true }).fill('باغ مستقل آزمون')
  await page.getByLabel('شهر', { exact: true }).fill('رفسنجان')
  await page.getByLabel('مساحت (هکتار)').fill('2')
  await page.getByLabel('تعداد درخت').fill('200')
  await page.getByRole('dialog').getByRole('button', { name: 'ثبت باغ', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'باغ مستقل آزمون' })).toBeVisible()
}

test('boots at the project path without a single API call or payment/signup prompt', async ({ page }) => {
  const calls: string[] = [], errors: string[] = []
  page.on('request', request => { if (new URL(request.url()).pathname.includes('/api/')) calls.push(request.url()) })
  page.on('pageerror', error => errors.push(error.message))
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'باغ سالم، خیال آسوده' })).toBeVisible()
  await expect(page.getByText('نسخه مستقل و رایگان', { exact: false })).toBeVisible()
  expect(await page.locator('img.hero-photo').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true)
  expect(calls).toEqual([])
  expect(errors).toEqual([])
  await page.goto('./#/subscription')
  await expect(page.getByRole('heading', { name: 'داده‌ها و پشتیبان' })).toBeVisible()
  await expect(page.getByText('کارت بانکی یا اشتراک لازم نیست', { exact: false })).toBeVisible()
  await expect(page.getByRole('button', { name: 'انتخاب این طرح' })).toHaveCount(0)
})

test('orchard data survives a reload and can be edited', async ({ page }) => {
  await addOrchard(page)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'باغ مستقل آزمون' })).toBeVisible()
  await page.getByRole('button', { name: 'ویرایش باغ مستقل آزمون' }).click()
  await page.getByLabel('نام باغ', { exact: true }).fill('باغ مستقل ویرایش‌شده')
  await page.getByRole('button', { name: 'ذخیره تغییرات' }).click()
  await expect(page.getByRole('heading', { name: 'باغ مستقل ویرایش‌شده' })).toBeVisible()
})

test('task creation and completion work locally', async ({ page }) => {
  await page.goto('./#/calendar')
  await page.getByRole('button', { name: 'یادآور جدید' }).click()
  await page.getByLabel('عنوان یادآور').fill('بازدید مستقل برگ‌ها')
  await page.getByRole('button', { name: 'ثبت یادآور', exact: true }).click()
  await expect(page.getByText('بازدید مستقل برگ‌ها', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'انجام بازدید مستقل برگ‌ها', exact: true }).click()
  await expect(page.getByText('بازدید مستقل برگ‌ها', {exact: true})).not.toBeVisible()
  await page.reload()
  await page.getByRole('button', { name: 'نمایش انجام‌شده‌ها' }).click()
  await expect(page.getByRole('button', { name: 'بازگرداندن بازدید مستقل برگ‌ها', exact: true })).toBeVisible()
})

test('photo is normalized and saved, with no fabricated diagnosis', async ({ page }) => {
  await page.goto('./#/analysis')
  await expect(page.getByText('ثبت عکس، نه تشخیص هوشمند.', { exact: false })).toBeVisible()
  await page.locator('input[type=file]').first().setInputFiles('public/images/pistachio-leaves.jpg')
  await page.getByPlaceholder('علائم از چه زمانی شروع شده؟ آخرین آبیاری، کود یا سم‌پاشی چه زمانی بوده؟').fill('فقط یادداشت من، نه تشخیص')
  await page.getByRole('button', { name: 'ذخیره عکس و یادداشت', exact: true }).click()
  await expect(page.getByRole('dialog')).toContainText('هیچ مدل یا کارشناس، تصویر را تحلیل نکرده')
  await expect(page.locator('.hypothesis')).toHaveCount(0)
  expect(await page.getByRole('dialog').locator('.report-detail-image img').getAttribute('src')).toMatch(/^data:image\/jpeg;base64,/)
  await page.getByRole('button', { name: 'بستن', exact: true }).click()
  await page.goto('./#/reports')
  await page.reload()
  await page.getByRole('button', { name: /عکس ثبت‌شده برگ/ }).click()
  await expect(page.getByRole('dialog')).toContainText('فقط یادداشت من، نه تشخیص')
  await page.getByRole('button', { name: 'حذف گزارش و تصویر' }).click()
  await page.getByRole('button', { name: 'تأیید حذف', exact: true }).click()
  await expect(page.locator('.report-row')).toHaveCount(0)
})

test('backup download, erasure and confirmed restore work', async ({ page }) => {
  await addOrchard(page)
  await page.goto('./#/subscription')
  const downloadEvent = page.waitForEvent('download')
  await page.getByRole('button', { name: 'دریافت پشتیبان' }).click()
  const download = await downloadEvent
  const path = await download.path()
  expect(path).toBeTruthy()
  const content = await fs.readFile(path!, 'utf8')
  expect(JSON.parse(content.replace(/^\uFEFF/, '')).orchards).toHaveLength(1)
  await page.getByRole('button', { name: 'حذف همه داده‌های محلی' }).click()
  await page.getByRole('button', { name: 'تأیید حذف همه داده‌ها' }).click()
  await expect(page.getByRole('button', {name: 'بازگردانی پشتیبان'})).toBeEnabled()
  await expect(page.getByRole('status')).toContainText('اطلاعات محلی حذف شدند')
  await page.locator('input[type=file]').setInputFiles(path!)
  await expect(page.getByText('اطلاعات فعلی با فایل پشتیبان جایگزین شود؟')).toBeVisible()
  await page.getByRole('button', { name: 'تأیید بازگردانی' }).click()
  await page.goto('./#/orchards')
  await expect(page.getByRole('heading', { name: 'باغ مستقل آزمون' })).toBeVisible()
})

test('cached knowledge and local CRUD work completely offline', async ({ page, context }) => {
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'باغ سالم، خیال آسوده' })).toBeVisible()
  await page.evaluate(() => navigator.serviceWorker.ready)
  await page.waitForFunction(() => !!navigator.serviceWorker.controller)
  await context.setOffline(true)
  await addOrchard(page)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'باغ مستقل آزمون' })).toBeVisible()
  await page.goto('./#/knowledge')
  await page.getByRole('textbox', { name: 'جستجوی دانشنامه' }).fill('پسیل')
  await page.locator('.article-card').filter({ hasText: 'پسیل پسته؛ قبل از مبارزه' }).click()
  await expect(page.getByRole('dialog')).toContainText('منابع مطالعه و دامنه کاربرد')
})

test('mobile layout and installation metadata are valid', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'باغ سالم، خیال آسوده' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  const manifest = await page.evaluate(async () => {
    const href = document.querySelector<HTMLLinkElement>('link[rel=manifest]')!.href
    return (await fetch(href)).json()
  })
  expect(manifest.start_url).toBe('/Zehnyar/')
  expect(manifest.display).toBe('standalone')
  expect(manifest.icons).toHaveLength(2)
  await expect(page.locator('link[rel=apple-touch-icon]')).toHaveAttribute('href', '/Zehnyar/icon-180.png')
})


test.afterEach(async ({page}, info) => {
  if (info.status !== info.expectedStatus) {
    const diagnostic = await page.evaluate(() => ({url: location.href, hash: location.hash, text: document.body.innerText.slice(0, 7000), controlled: !!navigator.serviceWorker?.controller})).catch(() => ({url: page.url()}))
    const value = JSON.stringify(diagnostic).replace(/%/g, '%25').replace(/\r/g, '%0D').replace(/\n/g, '%0A')
    console.log('::notice title=Standalone UI failure context::' + value)
  }
})
