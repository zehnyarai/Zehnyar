import reasoningFixture from '../fixtures/decision-reasoning.json'
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
  // The offline edition asks for the owner's own key instead of claiming a server model.
  await expect(page.getByRole('alert')).toContainText('تحلیل عکس هنوز فعال نشده است')
  await expect(page.locator('.hypothesis')).toHaveCount(0)
  await page.getByRole('button', { name: 'ذخیره پرونده بدون تحلیل', exact: true }).click()
  await expect(page.getByRole('dialog')).toContainText('هیچ تحلیل هوشمندی انجام نشده')
  await expect(page.locator('.report-gallery img')).toHaveCount(4)
})

test('credits show the real packages and the owner panel keeps the card and ledger honest', async ({
  page,
}) => {
  await page.goto('./#/subscription')
  await expect(page.getByRole('heading', { name: 'اعتبار من' })).toBeVisible()
  // Four support packages, all built on the owner's 350,000 Toman single-analysis price.
  await expect(page.locator('.plan-card')).toHaveCount(4)
  await expect(page.locator('.plan-card').first()).toContainText('تومان')
  await expect(page.locator('.plan-card').first()).toContainText('۳۵۰٬۰۰۰')
  await expect(page.locator('.plan-card').nth(1)).toContainText('۳۱۵٬۰۰۰')
  await expect(page.locator('.plan-card').nth(3)).toContainText('۴٬۹۰۰٬۰۰۰')
  await expect(page.locator('.local-credits')).toContainText('هر تحلیل ۳۵۰٬۰۰۰ تومان است')
  await expect(page.locator('.bank-card-display')).toContainText(/9401\s*[\s-]\s*6524/)
  await expect(page.getByRole('heading', { name: /کد فعال‌سازی دارم/ })).toBeVisible()
  // The owner panel opens only with the owner password.
  await page.goto('./#/admin')
  await expect(page.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeVisible()
  await page.getByLabel('رمز مدیر').fill('Pestino1404')
  await page.getByRole('button', { name: /باز کردن پنل مدیر/ }).click()
  await page.getByRole('tab', { name: 'کارت و پشتیبان' }).click()
  await expect(page.getByLabel('شماره کارت ۱۶ رقمی')).toHaveValue('9401652473116063')
  await expect(page.locator('.receipt-ledger')).toHaveCount(0)
  await expect(page.locator('.local-admin-page')).toContainText(
    'این دفتر ثبت دستی است، نه تأیید بانکی خودکار.'
  )
  await expect(page.locator('.local-admin-page')).toContainText('فقط مالک')
})

test('dated research library works offline and distinguishes source evidence from diagnosis', async ({
  page,
}) => {
  await page.goto('./#/knowledge')
  await page.getByRole('button', { name: 'پژوهش و نوآوری', exact: true }).click()
  await expect(page.locator('.research-card')).toHaveCount(27)
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
  await expect(page.locator('.research-card')).toHaveCount(27)
})

test('offline edition offers on-device key activation and refuses to fake analysis', async ({
  page,
}) => {
  const calls: string[] = []
  // Any Google call is stubbed: this test must never hit the network.
  page.on('request', (request) => {
    if (request.url().includes('generativelanguage.googleapis.com')) calls.push(request.url())
  })
  page.on('requestfailed', (request) => {
    if (request.url().includes('generativelanguage.googleapis.com'))
      calls.push(`FAILED ${request.url()}`)
  })
  await page.route('**://generativelanguage.googleapis.com/**', async (route) => {
    const probe = String(route.request().postData() ?? '').includes('connection test')
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        candidates: [
          {
            finishReason: 'STOP',
            content: {
              parts: [
                {
                  text: JSON.stringify(
                    probe
                      ? { ok: true, model: 'gemini-2.5-flash' }
                      : {
                          decision_reasoning: reasoningFixture,
                          title: 'برگ پسته',
                          summary: 'لکه روشن روی برگ دیده می‌شود؛ آزمایش برگ لازم است.',
                          quality: 'نور کافی',
                          is_pistachio: true,
                          observations: ['لکه روشن روی برگ یک'],
                          hypotheses: [
                            {
                              name: 'تنش محیطی',
                              evidence: 'بدون بافت قارچی',
                              next_step: 'پایش هفتگی',
                            },
                          ],
                          actions: ['برگ‌های آلوده را جدا کنید'],
                          needed_tests: ['آزمایش برگ'],
                          follow_up_questions: [],
                          urgency: 'medium',
                          limitations: ['آزمایش خاک انجام نشده'],
                          nutrition_considerations: [],
                          yield_quality_plan: [],
                          monitoring_plan: ['عکس هفتگی'],
                          knowledge_ids: ['sampling'],
                        }
                  ),
                },
              ],
            },
          },
        ],
      }),
    })
  })
  // The key entry lives only in the password-protected owner panel.
  await page.goto('./#/admin')
  await expect(page.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeVisible()
  await page.getByLabel('رمز مدیر').fill('Pestino1404')
  await page.getByRole('button', { name: /باز کردن پنل مدیر/ }).click()
  await expect(page.getByRole('heading', { name: 'کلید سرویس تحلیل' })).toBeVisible()
  await page.getByLabel('نام مدل').fill('gemini-2.5-flash')
  await page.getByLabel(/^کلید API Google/).fill('AIzaSyStandaloneExampleKey123')
  await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
  await expect(page.getByText('ثبت شده؛ بدون آزمون')).toBeVisible()
  await page.getByRole('button', { name: /آزمون اتصال/ }).click()
  // The stub answers the plain-text probe shape only for the connection test.
  // Wait for the visible success state before reading the recorded requests: the
  // network event can arrive a moment after the click returns.
  await expect(page.getByText(/آزمون اتصال موفق شد/)).toBeVisible()
  expect(calls.length).toBeGreaterThan(0)
  expect(calls[0]).toContain('gemini-2.5-flash:generateContent')
  expect(calls[0]).not.toContain('AIza')
  expect(await page.evaluate(() => document.body.innerText)).not.toContain('AIzaSyStandalone')
  const stored = await page.evaluate(() =>
    JSON.stringify(localStorage.getItem('pestino-direct-vision'))
  )
  expect(stored).toContain('AIzaSyStandaloneExampleKey123')
  // The stored key must never be part of the exportable backup.
  const backup = await page.evaluate(async () => {
    const db = await new Promise<IDBDatabase>((resolve) => {
      const open = indexedDB.open('pestino-local-v1', 1)
      open.onsuccess = () => resolve(open.result)
    })
    return await new Promise<string>((resolve, reject) => {
      const req = db.transaction('state').objectStore('state').get('data')
      req.onsuccess = () => resolve(JSON.stringify(req.result ?? {}))
      req.onerror = () => reject(req.error)
    })
  })
  expect(backup).not.toContain('AIzaSyStandalone')
})

test('offline admin panel connects the model and keeps the owner ledger honest', async ({
  page,
}) => {
  await page.route('**://generativelanguage.googleapis.com/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        candidates: [
          {
            finishReason: 'STOP',
            content: { parts: [{ text: JSON.stringify({ ok: true, model: 'gemini-2.5-flash' }) }] },
          },
        ],
      }),
    })
  })
  await page.goto('./#/admin')
  await expect(page.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeVisible()
  await page.getByLabel('رمز مدیر').fill('Pestino1404')
  await page.getByRole('button', { name: /باز کردن پنل مدیر/ }).click()
  await expect(page.getByRole('heading', { name: 'کلید سرویس تحلیل' })).toBeVisible()
  // Connect the model from the admin panel itself.
  await page.getByLabel('نام مدل').fill('gemini-2.5-flash')
  await page.getByLabel(/^کلید API Google/).fill('AIzaSyAdminPanelExampleKey123')
  await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
  await page.getByRole('button', { name: /آزمون اتصال/ }).click()
  await expect(page.getByText(/آزمون اتصال موفق شد/)).toBeVisible()
  // Card + ledger: confirmation is required, then the receipt is recorded.
  await page.getByRole('tab', { name: 'کارت و پشتیبان' }).click()
  await page.getByLabel('شماره کارت ۱۶ رقمی').fill('9401 6524 7311 6063')
  await page.getByLabel('نام صاحب کارت').fill('احمد قرائی سلطان آبادی')
  await page.getByLabel(/^نام بانک/).fill('بانک ملی ایران')
  await page.getByRole('button', { name: 'ذخیره کارت مقصد' }).click()
  await expect(page.getByRole('alert')).toContainText('تطبیق')
  await page.getByRole('checkbox', { name: /تأیید می‌کنم شماره کارت/ }).check()
  await page.getByRole('button', { name: 'ذخیره کارت مقصد' }).click()
  await expect(page.locator('.local-admin-page p.muted').filter({ hasText: '9401' })).toContainText(
    /9401\s*-\s*6524\s*-\s*7311\s*-\s*6063/
  )
  await page.getByLabel('نام پرداخت‌کننده').fill('باغدار نمونه')
  await page.getByLabel('مبلغ (تومان)').fill('4900000')
  await page.getByLabel('تاریخ واریز').fill('2026-10-12')
  await page.getByRole('button', { name: 'ثبت در دفتر دریافتی‌ها' }).click()
  await expect(page.locator('.receipt-ledger')).toContainText('باغدار نمونه')
  await expect(page.locator('.local-admin-page')).toContainText(
    'این دفتر ثبت دستی است، نه تأیید بانکی خودکار.'
  )
  // The credits screen shows the same card with the manual wording, not a gateway flow.
  await page.goto('./#/subscription')
  await expect(page.locator('.bank-card-display')).toContainText(/9401\s*[\s-]\s*6524/)
  await expect(page.locator('.local-credits')).toContainText('این برنامه درگاه بانکی')
})
