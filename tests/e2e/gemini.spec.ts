import { test, expect } from '@playwright/test'

test('Gemini lab UI requires consent, sends no key and invalidates a changed interpretation', async ({
  page,
}) => {
  let posted = 0
  await page.route('**/api/bootstrap', async (route) => {
    const original = await route.fetch()
    const body = await original.json()
    body.user.is_demo = 0 // UI mock only; API ownership/consent are tested in Python.
    body.services.vision_configured = true
    body.services.lab_ai_configured = true
    body.services.vision_provider = 'gemini'
    body.services.vision_model = 'gemini-3.1-pro-preview'
    await route.fulfill({ json: body })
  })
  await page.route('**/api/lab-analyses', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ json: [] })
      return
    }
    const request = route.request().postDataJSON()
    posted++
    expect(request.consent).toBe(true)
    expect(request.sample.values).toEqual({ ph: 8, ec: 2 })
    expect(request.sample.method).toBe('water')
    expect(JSON.stringify(request)).not.toContain('API_KEY')
    expect(Object.keys(request)).toEqual(['sample', 'consent'])
    await route.fulfill({
      status: 201,
      json: {
        id: 'mock-lab-result',
        created_at: '2026-10-11T00:00:00Z',
        input: request.sample,
        units: { ph: 'dimensionless', ec: 'dS/m' },
        calculations: [],
        result: {
          title: 'پاسخ آزمایشی Gemini',
          summary: 'نمونه آزمون رابط، نه اتصال واقعی Google.',
          provider: 'gemini',
          model: 'gemini-3.1-pro-preview',
          disclaimer: 'تفسیر احتمالی؛ نه نسخه یا دقت تأییدشده.',
          findings: ['روش نمونه را بررسی کنید.'],
          nutrition_considerations: [],
          irrigation_considerations: [],
          care_plan: [],
          yield_quality_plan: [],
          needed_tests: [],
          limitations: ['اعتبار محلی این نمونه تأیید نشده است.'],
          follow_up_questions: [],
          knowledge_ids: [],
        },
      },
    })
  })
  await page.goto('/laboratory')
  await page.getByRole('tab', { name: 'آزمایش آب' }).click()
  await page.getByLabel('pH', { exact: true }).fill('8')
  await page.getByLabel(/^EC /).fill('2')
  await page.getByRole('button', { name: 'دریافت تفسیر Gemini', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('رضایت آگاهانه')
  expect(posted).toBe(0)
  await page.getByRole('checkbox', { name: /با ارسال مقادیر/ }).check()
  await page.getByRole('button', { name: 'دریافت تفسیر Gemini', exact: true }).click()
  await expect(page.locator('.lab-ai-result')).toContainText(
    'نمونه آزمون رابط، نه اتصال واقعی Google'
  )
  expect(posted).toBe(1)
  await page.getByLabel(/^EC /).fill('3')
  await expect(page.locator('.lab-ai-result')).toHaveCount(0)
  await expect(page.getByRole('checkbox', { name: /با ارسال مقادیر/ })).not.toBeChecked()
  expect(posted).toBe(1) // Changing inputs never silently calls a potentially billable model.
})
