import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { buildScientificBasis, selectEvidence } from '../../src/evidence'
import reasoning from '../fixtures/decision-reasoning.json'

test('saved scientific reasoning and source provenance survive reload, remain readable on mobile, and export without provider names', async ({
  page,
}) => {
  const pack = selectEvidence({ notes: 'خشکیدگی تنه' })
  const basis = buildScientificBasis(
    {
      ...reasoning,
      research_claims: [
        {
          statement: 'جداسازی قارچ به‌تنهایی علت را ثابت نمی‌کند.',
          source_ids: [pack[0].id, 'fabricated-id'],
          application_limit: 'این باغ در مطالعه نبوده؛ تشخیص عامل از عکس کافی نیست.',
        },
      ],
    },
    pack
  )
  await page.goto('./#/reports')
  await expect(page.getByRole('heading', { name: 'عکس‌ها و یادداشت‌ها' })).toBeVisible()
  await page.evaluate(async (science) => {
    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      const open = indexedDB.open('pestino-local-v1', 1)
      open.onsuccess = () => resolve(open.result)
      open.onerror = () => reject(open.error)
    })
    const canvas = document.createElement('canvas')
    canvas.width = 500
    canvas.height = 400
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction('state', 'readwrite')
      const store = tx.objectStore('state')
      const get = store.get('data')
      get.onsuccess = () =>
        store.put(
          {
            ...get.result,
            reports: [
              {
                id: 'scientific-fixture-only',
                orchard_id: null,
                orchard_name: null,
                tree_part: 'شاخه و تنه',
                notes: 'فقط پرونده آزمون نرم‌افزار',
                created_at: '2026-10-18T09:00:00Z',
                is_sample: 0,
                image_url: canvas.toDataURL('image/jpeg'),
                data: {
                  title: 'آزمون استدلال علمی',
                  summary: 'این نمونه فقط رفتار نرم‌افزار را می‌آزماید، نه صحت تشخیص.',
                  quality: 'نمونه آزمون',
                  is_pistachio: true,
                  observations: ['نمونه ساختگی برای آزمون'],
                  hypotheses: [],
                  actions: [],
                  needed_tests: [],
                  follow_up_questions: [],
                  urgency: 'medium',
                  knowledge_ids: [],
                  provider: 'gemini-direct-byo-key',
                  model: 'internal-test-model',
                  knowledge_version: 'fixture',
                  disclaimer: 'تشخیص واقعی نیست.',
                  scientific_basis: science,
                },
              },
            ],
          },
          'data'
        )
      tx.oncomplete = () => resolve()
      tx.onerror = () => reject(tx.error)
    })
    db.close()
  }, basis)
  await page.reload()
  await page.locator('.report-row').filter({ hasText: 'آزمون استدلال علمی' }).click()
  await page.locator('.scientific-basis summary').click()
  await expect(
    page.getByRole('heading', { name: 'احتمال‌های جایگزین و شواهد مخالف' })
  ).toBeVisible()
  await expect(page.locator('.scientific-basis')).toContainText('این باغ در مطالعه نبوده')
  await expect(page.locator('.scientific-basis')).toContainText('چکیده ناشر')
  await expect(page.locator('.scientific-basis a')).toHaveAttribute('href', pack[0].url)
  expect(await page.locator('.report-detail').innerText()).not.toMatch(
    /gemini|grok|internal-test-model|fabricated-id/i
  )
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  const file = page.waitForEvent('download')
  await page.getByRole('button', { name: 'دریافت گزارش متنی' }).click()
  const path = await (await file).path()
  const text = await readFile(path!, 'utf8')
  expect(text).toContain(pack[0].url)
  expect(text).toContain('بررسی‌های تغییردهندهٔ تصمیم')
  expect(text).not.toMatch(/gemini|grok|internal-test-model|fabricated-id/i)
})
