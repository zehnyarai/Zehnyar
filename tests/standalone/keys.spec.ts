import { test, expect } from '@playwright/test'

test('both keys persist across reload and tab-specific tests never ask for the saved key again', async ({
  page,
}) => {
  const calls: { url: string; authorization: string | null; google: string | null }[] = []
  await page.route('https://api.x.ai/**', async (route) => {
    const request = route.request()
    calls.push({
      url: request.url(),
      authorization: request.headers()['authorization'] ?? null,
      google: null,
    })
    await route.fulfill({
      status: request.url().endsWith('/models') ? 200 : 401,
      contentType: 'application/json',
      body: request.url().endsWith('/models')
        ? JSON.stringify({ data: [{ id: 'grok-4.3' }] })
        : JSON.stringify({ error: 'dummy account unauthorized' }),
    })
  })
  await page.route('https://generativelanguage.googleapis.com/**', async (route) => {
    calls.push({
      url: route.request().url(),
      authorization: null,
      google: route.request().headers()['x-goog-api-key'] ?? null,
    })
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        candidates: [{ finishReason: 'STOP', content: { parts: [{ text: '{"ok":true}' }] } }],
      }),
    })
  })
  async function unlock() {
    await page.goto('./#/admin')
    await expect(page.locator('.admin-gate-card, .local-admin-page')).toBeVisible()
    if (await page.getByLabel('رمز مدیر').isVisible()) {
      await page.getByLabel('رمز مدیر').fill('Pestino1404')
      await page.getByRole('button', { name: /باز کردن پنل مدیر/ }).click()
    }
    await expect(page.getByRole('heading', { name: 'کلید سرویس تحلیل' })).toBeVisible()
  }
  await unlock()
  await page.getByLabel(/^کلید API Google/).fill('AIzaSyBrowserDummySaved12345')
  await page.getByRole('button', { name: 'ذخیره', exact: true }).click()
  await expect(page.getByLabel(/^کلید API Google/)).toHaveValue('')
  await page.getByRole('tab', { name: /Grok \(xAI\)/ }).click()
  await page.getByLabel(/^کلید API xAI/).fill('xai-BrowserDummySaved12345')
  // Test first: the panel must persist a pasted key BEFORE trying the network.
  await page.getByRole('button', { name: 'آزمون اتصال', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('کلید xAI پذیرفته نشد')
  await expect(page.getByLabel(/^کلید API xAI/)).toHaveValue('')
  await page.reload()
  await unlock()
  await expect(page.getByRole('tab', { name: /Grok \(xAI\)/ })).toContainText('کلید ثبت شده')
  await expect(page.getByRole('tab', { name: /Gemini \(Google\)/ })).toContainText('کلید ثبت شده')
  await page.getByRole('tab', { name: /Gemini \(Google\)/ }).click()
  await page.getByRole('button', { name: 'آزمون اتصال', exact: true }).click()
  await expect(
    page.getByText(
      'آزمون اتصال موفق شد؛ پاسخ متنی دریافت شد. قابلیت و کیفیت عکس با این آزمون تأیید نمی‌شود.'
    )
  ).toBeVisible()
  expect(calls.some((r) => r.google === 'AIzaSyBrowserDummySaved12345')).toBe(true)
  expect(calls.some((r) => r.authorization === 'Bearer xai-BrowserDummySaved12345')).toBe(true)
  expect(await page.locator('.local-admin-page').innerText()).not.toMatch(/BrowserDummySaved/)
})
