// @vitest-environment jsdom
// Full-app smoke test in the exact configuration of the Android APK (standalone).
// The owner reported on 2026-10-17 that «تحلیل» «آزمایشگاه» «دیوار تجربه» and «بازار و اقلیم»
// looked inactive; this test walks every section the way a farmer taps it.
import 'fake-indexeddb/auto'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { eraseLocalData } from './standalone'

vi.mock('./config', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./config')>()),
  IS_STANDALONE: true,
}))
vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return {
    ...actual,
    api: async (path: string, options: RequestInit = {}) => {
      const { localApi } = await import('./standalone')
      return localApi(path, options)
    },
  }
})

const text = () => document.body.textContent?.replace(/\s+/g, ' ') ?? ''
const CRASH = 'نمایش صفحه با مشکل روبه‌رو شد'

beforeEach(async () => {
  const store = new Map<string, string>()
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
  })
  await eraseLocalData()
  location.hash = '#/'
})
afterEach(() => cleanup())

describe('every section opens in the standalone APK', { timeout: 30000 }, () => {
  it('opens خانه، اسکن آفت، آزمایشگاه، دیوار تجربه، بازار و اقلیم، اعتبار and پنل مدیر', async () => {
    const user = userEvent.setup()
    render(<App />)
    await waitFor(() => expect(text()).toContain('دستیار هوشمند باغداران پسته'), { timeout: 8000 })

    const nav = (name: string | RegExp) => screen.getByRole('link', { name })
    // Each entry is [nav link, a unique marker that only that page's body shows].
    const pages: [string | RegExp, string][] = [
      [/اسکن آفت/, 'اسکن و تشخیص احتمال آفت'],
      [/تحلیل خاک و آب/, 'آزمایش خاک'],
      [/دیوار تجربه/, 'ثبت تجربه'],
      [/بازار و اقلیم/, 'قیمت'],
      [/اعتبار من/, 'کارت واریز'],
      [/خانه/, 'دستیار هوشمند باغداران پسته'],
    ]
    for (const [link, marker] of pages) {
      await user.click(nav(link))
      try {
        await waitFor(() => expect(text()).toContain(marker), { timeout: 6000 })
      } catch (error) {
        // eslint-disable-next-line no-console
        console.log('PAGE-DEBUG', String(link), JSON.stringify(text().slice(0, 900)))
        throw error
      }
      expect(text()).not.toContain(CRASH)
    }

    // The owner panel is password-protected from the first launch.
    await user.click(nav(/پنل مدیر/))
    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'ورود به پنل مدیر' })).toBeTruthy()
    )
    await user.type(screen.getByLabelText('رمز مدیر'), 'Pestino1404')
    await user.click(screen.getByRole('button', { name: /باز کردن پنل مدیر/ }))
    await waitFor(() => expect(text()).toContain('کلید سرویس تحلیل'), { timeout: 6000 })
    expect(text()).toContain('کارت واریز و دفتر دریافت')
  })

  it('opens the orchard book, the photo reports, the calendar, the knowledge base and backup', async () => {
    const user = userEvent.setup()
    render(<App />)
    await waitFor(() => expect(text()).toContain('دستیار هوشمند باغداران پسته'), { timeout: 8000 })
    // The secondary tools live behind one tap; without it they are invisible to a farmer.
    await user.click(screen.getByRole('button', { name: /دفتر باغ و دانشنامه/ }))
    // [button in the tools bar, the h1 that only the opened page shows]
    const tools = [
      ['باغ‌های من', 'باغ‌های من'],
      ['پرونده‌ها و عکس‌ها', 'عکس‌ها و یادداشت‌ها'],
      ['تقویم مراقبت', 'تقویم مراقبت'],
      ['دانشنامه پسته', 'دانشنامه پسته'],
      ['داده‌ها و پشتیبان', 'داده‌ها و پشتیبان'],
    ] as const
    const headings = () => screen.queryAllByRole('heading', { level: 1 }).map((h) => h.textContent)
    for (const [name, marker] of tools) {
      await user.click(screen.getByRole('button', { name }))
      await waitFor(() => expect(headings()).toContain(marker), { timeout: 6000 })
      expect(text()).not.toContain(CRASH)
    }
  })
})
