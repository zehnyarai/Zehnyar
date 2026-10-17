import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'

test('photo receipt moves between independent farmer and manager browsers, then unlocks only the farmer', async ({
  page,
  browser,
}, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('./#/subscription')
  await expect(page.getByRole('heading', { name: 'اعتبار من', exact: true })).toBeVisible()
  await page.locator('.plan-card').nth(1).getByRole('button', { name: 'انتخاب بسته' }).click()
  const form = page.locator('.receipt-form')
  await form.getByLabel('عکس فیش واریزی').setInputFiles('public/images/pistachio-leaves.jpg') // Fixture only, NOT a real bank receipt.
  await expect(form.getByAltText('پیش‌نمایش فیش واریزی')).toBeVisible()
  await form.getByLabel('نام پرداخت‌کننده').fill('باغدار آزمون')
  await form.getByLabel('مبلغ (تومان)').fill('۱۵۷۵۰۰۰') // Phone keyboards use Persian digits.
  await form.getByLabel('کد پیگیری').fill('۱۲۳۴۵۶۷۸۹')
  await form.getByRole('button', { name: 'ذخیره فیش و آماده‌سازی ارسال' }).click()
  await expect(
    page.getByRole('status').filter({ hasText: 'فیش فقط روی این گوشی' }).first()
  ).toBeVisible()
  const downloadEvent = page.waitForEvent('download')
  await page.getByRole('button', { name: 'ذخیره فایل', exact: true }).click()
  const download = await downloadEvent
  const path = testInfo.outputPath('pestino-receipt.json')
  await download.saveAs(path)
  const content = await readFile(path, 'utf8')
  expect(content).toContain('image_data')
  expect(content).not.toContain('activation_code')

  const manager = await browser.newContext({ viewport: { width: 390, height: 844 } })
  const admin = await manager.newPage()
  try {
    await admin.goto(new URL('#/admin', page.url()).href)
    await admin.getByLabel('رمز مدیر').fill('Pestino1404')
    await admin.getByRole('button', { name: /باز کردن پنل مدیر/ }).click()
    await admin.getByRole('tab', { name: 'فیش‌های واریزی' }).click()
    const inbox = admin.getByRole('region', { name: 'فیش‌های ارسالی باغداران' })
    // section with accessible name has implicit region role.
    await inbox.getByLabel('فایل فیش باغدار').setInputFiles({
      name: 'pestino-receipt.json',
      mimeType: 'application/json',
      buffer: Buffer.from(content),
    })
    await expect(inbox).toContainText('باغدار آزمون')
    await inbox.getByRole('button', { name: 'مشاهده و بررسی' }).click()
    await expect(inbox.getByAltText('فیش واریزی باغدار آزمون')).toBeVisible()
    await expect(inbox).toContainText('۵ تحلیل')
    const confirm = inbox.getByRole('button', { name: 'تأیید و صدور اعتبار' })
    await expect(confirm).toBeDisabled()
    await inbox.getByLabel(/مبلغ، تاریخ و کد پیگیری/).check()
    await confirm.click()
    const codeField = inbox.getByLabel('کد اعتبار برای ارسال به باغدار')
    await expect(codeField).toHaveValue(/^PST-/)
    const code = await codeField.inputValue()
    await expect(inbox).toContainText('اعتبار به گوشی مدیر اضافه نشده است')
    await admin.reload()
    await admin.getByRole('tab', { name: 'فیش‌های واریزی' }).click()
    await inbox.getByRole('button', { name: 'مشاهده و بررسی' }).click()
    await expect(codeField).toHaveValue(code)
    await expect(confirm).toHaveCount(0)

    await page.getByLabel('کد فعال‌سازی', { exact: true }).fill(code)
    await page.getByRole('button', { name: 'فعال‌سازی', exact: true }).click()
    await expect(page.locator('.credit-counters')).toContainText('خریداری‌شده۵')
    await expect(page.locator('.credit-balance')).toContainText('۷') // 2 free + 5 paid.
    await page.getByLabel('کد فعال‌سازی', { exact: true }).fill(code)
    await page.getByRole('button', { name: 'فعال‌سازی', exact: true }).click()
    await expect(page.getByRole('alert')).toContainText('قبلاً')
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    expect(await admin.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true
    )
  } finally {
    await manager.close()
  }
})
