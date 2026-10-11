import { test, expect } from '@playwright/test'

test('dashboard, navigation and report sample are honest', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'دستیار هوشمند باغداران پسته' })).toBeVisible()
  await expect(page.getByText('فضای آزمایشی', { exact: false }).first()).toBeVisible()
  await page.goto('/reports')
  await page.getByRole('button', { name: /بررسی اولیه برگ پسته/ }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(
    page.getByText('گزارش نمونه؛ این نتیجه تحلیل عکس شما نیست.', { exact: false })
  ).toBeVisible()
  await page.getByRole('button', { name: 'اقدام و بررسی تکمیلی' }).click()
  await expect(page.getByRole('heading', { name: 'چه بررسی‌هایی کم داریم؟' })).toBeVisible()
  await page.getByRole('button', { name: 'بستن', exact: true }).click()
  await page.getByRole('button', { name: 'پرونده‌ها و عکس‌ها', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'گزارش‌های بررسی' })).toBeVisible()
  expect(errors).toEqual([])
})

test('new orchard persists across reload and can be edited', async ({ page }) => {
  await page.goto('/orchards')
  await page.getByRole('button', { name: 'ثبت باغ جدید' }).click()
  await page.getByLabel('نام باغ', { exact: true }).fill('باغ آزمون مرورگر')
  await page.getByLabel('شهر', { exact: true }).fill('دامغان')
  await page.getByLabel('مساحت (هکتار)').fill('2.5')
  await page.getByLabel('تعداد درخت').fill('350')
  await page.getByRole('button', { name: 'ثبت باغ', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'باغ آزمون مرورگر' })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'باغ آزمون مرورگر' })).toBeVisible()
  await page.getByRole('button', { name: 'ویرایش باغ آزمون مرورگر' }).click()
  await page.getByLabel('نام باغ', { exact: true }).fill('باغ آزمون ویرایش‌شده')
  await page.getByRole('button', { name: 'ذخیره تغییرات' }).click()
  await expect(page.getByRole('heading', { name: 'باغ آزمون ویرایش‌شده' })).toBeVisible()
})

test('task creation and completion are stored', async ({ page }) => {
  await page.goto('/calendar')
  await page.getByRole('button', { name: 'یادآور جدید' }).click()
  await page.getByLabel('عنوان یادآور').fill('بازدید آزمون مرورگر')
  await page.getByRole('button', { name: 'ثبت یادآور' }).click()
  await expect(page.getByText('بازدید آزمون مرورگر', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'انجام بازدید آزمون مرورگر', exact: true }).click()
  await expect(page.getByText('بازدید آزمون مرورگر', { exact: true })).not.toBeVisible()
  await page.getByRole('button', { name: 'نمایش انجام‌شده‌ها' }).click()
  await expect(
    page.getByRole('button', { name: 'بازگرداندن بازدید آزمون مرورگر', exact: true })
  ).toBeVisible()
})

test('knowledge search, category, sources and bookmarks work', async ({ page }) => {
  await page.goto('/knowledge')
  await page.getByRole('textbox', { name: 'جستجوی دانشنامه' }).fill('پسیل')
  await expect(
    page.locator('.article-card').filter({ hasText: 'پسیل پسته؛ قبل از مبارزه' })
  ).toBeVisible()
  await page.getByRole('button', { name: /نشان‌گذاری پسیل/ }).click()
  await page.getByRole('button', { name: 'نشان‌شده‌ها', exact: true }).click()
  await expect(
    page.locator('.article-card').filter({ hasText: 'پسیل پسته؛ قبل از مبارزه' })
  ).toBeVisible()
  await page.locator('.article-card').filter({ hasText: 'پسیل پسته؛ قبل از مبارزه' }).click()
  await expect(page.getByRole('heading', { name: 'منابع مطالعه و دامنه کاربرد' })).toBeVisible()
  await expect(page.getByRole('link', { name: /UC IPM/ })).toHaveAttribute(
    'href',
    'https://ipm.ucanr.edu/agriculture/pistachio/'
  )
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).not.toBeVisible()
})

test('image upload never fabricates diagnosis when provider is disconnected', async ({ page }) => {
  await page.goto('/analysis')
  await expect(page.getByText('تحلیل واقعی هنوز فعال نیست.', { exact: false })).toBeVisible()
  await page.locator('input[type=file]').first().setInputFiles('public/images/pistachio-leaves.jpg')
  await expect(page.getByAltText('تصویر انتخاب‌شده ۱ برای بررسی')).toBeVisible()
  await page.getByRole('checkbox', { name: /اجازه می‌دهم تصاویر/ }).check()
  await page.getByRole('button', { name: 'تحلیل تصویر و بررسی احتمال آفت', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('مدل بینایی واقعی هنوز متصل نیست')
  await page.getByRole('button', { name: 'ذخیره پرونده بدون تحلیل' }).click()
  await expect(page.getByRole('dialog')).toContainText('هیچ مدل یا کارشناس، تصاویر را تحلیل نکرده')
})

test('admin preview filters sample transactions and shows service states', async ({ page }) => {
  await page.goto('/admin')
  await expect(
    page.getByText('این بخش فقط برای مدیر احراز هویت‌شده است.', { exact: true })
  ).toBeVisible()
  await page.getByRole('button', { name: 'سرویس‌ها و درگاه', exact: true }).click()
  await expect(
    page.getByText('این پنل نمایش آزمایشی و فقط خواندنی است.', { exact: false })
  ).toBeVisible()
  await page.getByLabel('وضعیت پرداخت').selectOption('pending')
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await page.getByRole('button', { name: 'استعلام درگاه' }).click()
  await expect(page.getByRole('status')).toContainText('تراکنش نمونه فقط خواندنی')
  await page.getByRole('button', { name: 'وضعیت سرویس‌ها' }).click()
  await expect(page.getByRole('heading', { name: 'سرویس بینایی هوشمند' })).toBeVisible()
  await expect(page.getByText('تنظیم کلیدها فقط از محیط امن سرور', { exact: false })).toBeVisible()
})

test('registration creates a real, empty account instead of fake farm data', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'ورود به حساب واقعی' }).click()
  await page.getByRole('button', { name: 'ساخت حساب', exact: true }).click()
  await page.getByLabel('نام و نام خانوادگی').fill('باغدار مرورگر')
  await page.getByLabel('ایمیل', { exact: true }).fill(`e2e-${Date.now()}@example.com`)
  await page.getByLabel('رمز عبور', { exact: true }).fill('browser-test-password-2026')
  await page.getByRole('button', { name: 'ساخت حساب باغدار' }).click()
  await expect(page.getByRole('dialog')).not.toBeVisible()
  await expect(page.getByRole('button', { name: 'حساب و تنظیمات', exact: true })).toContainText(
    'باغدار مرورگر'
  )
  await expect(page.getByText('فضای آزمایشی', { exact: false })).not.toBeVisible()
  await page.getByRole('button', { name: 'باغ‌های من', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'اولین باغت را ثبت کن' })).toBeVisible()
})

test('subscription cannot turn a disconnected service into a paid plan', async ({ page }) => {
  await page.goto('/subscription?payment=success')
  await expect(page.getByText('دریافت وجه غیرفعال است.', { exact: true })).toBeVisible()
  await expect(page.locator('.bank-card-display')).toContainText('شماره کارت تنظیم نشده')
  await expect(
    page.getByRole('button', { name: 'ثبت رسید و درخواست اعتبار', exact: true })
  ).toBeDisabled()
})

test('all mobile pages fit viewport and the drawer opens and closes', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'دستیار هوشمند باغداران پسته' })).toBeVisible()
  await page.getByRole('button', { name: 'باز کردن منو' }).click()
  await page.getByRole('link', { name: 'تحلیل خاک و آب', exact: true }).click()
  await page.getByRole('button', { name: 'دفتر باغ و دانشنامه', exact: true }).click()
  await page.getByRole('button', { name: 'تقویم مراقبت', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'تقویم مراقبت', exact: true })).toBeVisible()
  for (const route of [
    '/',
    '/analysis',
    '/laboratory',
    '/community',
    '/market',
    '/install',
    '/orchards',
    '/knowledge',
    '/subscription',
    '/admin',
    '/reports',
    '/calendar',
  ]) {
    await page.goto(route)
    await expect(page.locator('main h1').first()).toBeVisible()
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth
    )
    expect(overflow, route).toBe(false)
  }
})
