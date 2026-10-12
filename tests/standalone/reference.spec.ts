import { test, expect } from '@playwright/test'

test('reference header and every new screen are responsive and navigable', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (e) => errors.push(e.message))
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'دستیار هوشمند باغداران پسته' })).toBeVisible()
  await page.getByRole('button', { name: 'شروع اسکن آفت', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'اسکن و تشخیص احتمال آفت' })).toBeVisible()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'باز کردن منو' }).click()
  await page.getByRole('link', { name: 'تحلیل خاک و آب', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'تحلیل خاک و آب', exact: true })).toBeVisible()
  for (const path of [
    'laboratory',
    'community',
    'market',
    'analysis',
    'subscription',
    'admin',
    'install',
    'settings',
  ]) {
    await page.goto(`./#/${path}`)
    await expect(page.locator('.reference-main')).not.toBeEmpty()
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      path
    ).toBe(true)
  }
  expect(errors).toEqual([])
})

test('soil form has all twelve reference fields and does not interpret unknown extraction as ECe', async ({
  page,
}) => {
  await page.goto('./#/laboratory')
  await expect(page.locator('.lab-grid input')).toHaveCount(12)
  await page.getByLabel(/^EC /).fill('5')
  await page.getByRole('button', { name: 'تحلیل و توصیه', exact: true }).click()
  await expect(page.locator('.lab-result')).toContainText('روش سنجش EC مشخص نیست')
  await page.getByLabel('روش اندازه‌گیری EC').selectOption('saturated')
  await expect(page.locator('.lab-result')).toHaveCount(0) // Editing invalidates stale interpretation.
  await page.getByRole('button', { name: 'تحلیل و توصیه', exact: true }).click()
  await expect(page.locator('.lab-result')).toContainText('آستانه افت محصول پسته نیست')
  await page.getByRole('button', { name: 'ذخیره پرونده آزمایش', exact: true }).click()
  await expect(page.getByRole('button', { name: 'پرونده ذخیره شده', exact: true })).toBeDisabled()
  await page.reload()
  await expect(page.locator('.lab-history .field-record-row')).toHaveCount(1)
})

test('water chemistry computes SAR from actual ions and never treats missing as zero', async ({
  page,
}) => {
  await page.goto('./#/laboratory')
  await page.getByRole('tab', { name: 'آزمایش آب' }).click()
  await page.getByLabel(/^سدیم/).fill('229.898')
  await page.getByLabel(/^کلسیم/).fill('40.078')
  await page.getByRole('button', { name: 'تحلیل و توصیه', exact: true }).click()
  await expect(page.locator('.calculation-grid')).toHaveCount(0)
  await page.getByLabel(/^منیزیم/).fill('24.305')
  await page.getByRole('button', { name: 'تحلیل و توصیه', exact: true }).click()
  await expect(page.locator('.calculation-grid')).toContainText('SAR محاسبه‌شده')
  await expect(page.locator('.calculation-grid')).toContainText('meq/L')
  await expect(page.locator('.lab-result')).toContainText('تفسیر آموزشی، نه نسخه')
})

test('experience form saves privately, filters and survives reload', async ({ page }) => {
  await page.goto('./#/community')
  await page.getByRole('button', { name: 'ثبت تجربه', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('عنوان تجربه *').fill('بازدید هفتگی آبیاری')
  await dialog.getByLabel('دسته تجربه').selectOption('آبیاری')
  await dialog.getByLabel('استان / منطقه *').fill('کرمان')
  await dialog
    .getByLabel('شرح تجربه و نتیجه مشاهده‌شده *')
    .fill(
      'در بازدید باغ، گرفتگی چند قطره‌چکان را پیدا کردم؛ این تجربه فقط مربوط به شرایط باغ من است.'
    )
  await dialog.getByRole('button', { name: 'ثبت تجربه', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'بازدید هفتگی آبیاری' })).toBeVisible()
  await expect(page.locator('.experience-card')).toContainText('خصوصی روی دستگاه')
  await page.reload()
  await page.getByRole('button', { name: 'برداشت', exact: true }).click()
  await expect(page.locator('.experience-card')).toHaveCount(0)
  await page.getByRole('button', { name: 'آبیاری', exact: true }).click()
  await expect(page.locator('.experience-card')).toHaveCount(1)
})

test('prices and climate are empty until sourced manual observations are entered', async ({
  page,
}) => {
  await page.goto('./#/market')
  await expect(page.locator('.market-summary').first()).toContainText('قیمت واقعی هنوز وارد نشده')
  await page.getByRole('button', { name: 'ثبت قیمت', exact: true }).click()
  const dialog = page.getByRole('dialog')
  await dialog.getByLabel('قیمت هر کیلوگرم *').fill('800000')
  await dialog.getByLabel('استان / بازار *').fill('کرمان')
  await dialog.getByLabel('منبع قیمت *').fill('مشاهده بازار محلی، داده آزمون')
  await dialog.getByRole('button', { name: 'ثبت مشاهده', exact: true }).click()
  await expect(page.locator('.market-summary').first()).toContainText(
    'مشاهده بازار محلی، داده آزمون'
  )
  await page.getByRole('tab', { name: 'اقلیم و هشدار' }).click()
  await page.getByRole('button', { name: 'ثبت وضعیت هوا', exact: true }).click()
  await dialog.getByLabel('استان / محل باغ *').fill('کرمان')
  await dialog.getByLabel('کمینه دما (°C) *').fill('-1')
  await dialog.getByLabel('بیشینه دما (°C) *').fill('8')
  await dialog.getByLabel('منبع داده *').fill('دماسنج باغ — داده آزمون')
  await dialog.getByRole('button', { name: 'ثبت مشاهده', exact: true }).click()
  await expect(page.locator('.climate-observation')).toContainText('مشاهده دستی، نه پیش‌بینی')
  await expect(page.locator('.climate-observation')).toContainText('نقطه انجماد')
})

test('four image views are stored, disconnected analysis never produces a diagnosis', async ({
  page,
}) => {
  await page.goto('./#/analysis')
  const file = 'public/images/pistachio-leaves.jpg'
  await page.getByLabel('انتخاب تصاویر درخت').setInputFiles([file, file, file, file])
  await expect(page.locator('.photo-grid figure')).toHaveCount(4)
  await page.getByRole('button', { name: 'تحلیل تصویر و بررسی احتمال آفت', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('مدل بینایی واقعی هنوز متصل نیست')
  await expect(page.locator('.hypothesis')).toHaveCount(0)
  await page.getByRole('button', { name: 'ذخیره پرونده بدون تحلیل', exact: true }).click()
  await expect(page.getByRole('dialog')).toContainText('هیچ مدل یا کارشناس، تصویر را تحلیل نکرده')
  await expect(page.locator('.report-gallery img')).toHaveCount(4)
})

test('credit and admin reference fields exist but no money or dummy card is active', async ({
  page,
}) => {
  await page.goto('./#/subscription')
  await expect(page.getByText('دریافت وجه غیرفعال است.', { exact: true })).toBeVisible()
  await expect(page.locator('.credit-packages label')).toHaveCount(3)
  await expect(
    page.getByRole('button', { name: 'ثبت رسید و درخواست اعتبار', exact: true })
  ).toBeDisabled()
  await expect(page.locator('.bank-card-display')).toContainText('شماره کارت تنظیم نشده')
  await page.goto('./#/admin')
  await expect(page.getByLabel('شماره کارت ۱۶ رقمی *')).toBeDisabled()
  await expect(page.getByRole('button', { name: 'ذخیره اطلاعات کارت', exact: true })).toBeDisabled()
  await expect(page.locator('.admin-credits tbody tr')).toHaveCount(0)
})

test('dated research library works offline and distinguishes source evidence from diagnosis', async ({
  page,
}) => {
  await page.goto('./#/knowledge')
  await page.getByRole('button', { name: 'پژوهش و نوآوری', exact: true }).click()
  await expect(page.locator('.research-card')).toHaveCount(24)
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByLabel('جستجوی پژوهش پسته').fill('آفلاتوکسین')
  await expect(
    page.locator('.research-card').filter({ hasText: 'آفلاتوکسین با حسگر طیفی' })
  ).toBeVisible()
  const card = page.locator('.research-card').filter({ hasText: 'آفلاتوکسین با حسگر طیفی' })
  await card.getByText('کاربرد در باغ، حدود شواهد و منبع', { exact: true }).click()
  await expect(card).toContainText('دقت پستینو نیست')
  await expect(card.locator('a')).toHaveAttribute(
    'href',
    'https://pmc.ncbi.nlm.nih.gov/articles/PMC11902545/'
  )
  await page.context().setOffline(true)
  await page.reload()
  await page.getByRole('button', { name: 'پژوهش و نوآوری', exact: true }).click()
  await expect(page.locator('.research-card')).toHaveCount(24)
})
