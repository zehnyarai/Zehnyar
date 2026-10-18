// @vitest-environment jsdom
import 'fake-indexeddb/auto'
import { render, screen, cleanup, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, afterEach, expect, it, vi } from 'vitest'
import Market from './Market'
import { eraseLocalData, localApi } from '../standalone'
import type { AppContext } from '../types'
vi.mock('../config', async (original) => ({
  ...(await original<typeof import('../config')>()),
  IS_STANDALONE: true,
}))
vi.mock('../api', async (original) => ({
  ...(await original<typeof import('../api')>()),
  api: (path: string, options?: RequestInit) => localApi(path, options),
}))
const ctx = { notify: vi.fn(), knowledge: { articles: [] } } as unknown as AppContext
beforeEach(async () => {
  localStorage.clear()
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response('', { status: 503 }))
  )
  await eraseLocalData()
})
afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})
it.each(['2750000', '۲٬۷۵۰٬۰۰۰'])(
  'accepts continuous typing in EVERY price field, saves %s, and survives remount',
  async (amount) => {
    const user = userEvent.setup()
    render(<Market ctx={ctx} />)
    await user.click(screen.getByRole('button', { name: 'ثبت قیمت' }))
    const price = screen.getByLabelText('قیمت هر کیلوگرم *') as HTMLInputElement
    await user.type(price, amount)
    expect(price.value).toBe(amount)
    expect(document.activeElement).toBe(price)
    for (const [label, value] of [
      ['استان / بازار *', 'رفسنجان'],
      ['نوع، اُنس و درجه محصول', 'خشک با پوست، انس ۲۶–۲۸'],
      ['منبع قیمت *', 'معامله واقعی آزمایشی'],
    ]) {
      const field = screen.getByLabelText(label) as HTMLInputElement
      await user.type(field, value)
      expect(field.value).toBe(value)
      expect(document.activeElement).toBe(field)
    }
    await user.click(screen.getByRole('button', { name: 'ثبت مشاهده' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    const rows =
      await localApi<{ data: { price: number; source: string; grade: string } }[]>(
        '/field-records/prices'
      )
    expect(rows[0].data.price).toBe(2750000)
    expect(rows[0].data.source).toBe('معامله واقعی آزمایشی')
    cleanup()
    render(<Market ctx={ctx} />)
    await waitFor(() => expect(document.body.textContent).toContain('معامله واقعی آزمایشی'))
  }
)
it('keeps keyboard focus and appends more than one digit in weather fields too', async () => {
  const user = userEvent.setup()
  render(<Market ctx={ctx} />)
  await user.click(screen.getByRole('tab', { name: 'اقلیم و هشدار' }))
  await user.click(screen.getByRole('button', { name: /ثبت.*هوا/ }))
  const field = screen.getByLabelText('کمینه دما (°C) *') as HTMLInputElement
  await user.type(field, '-۱۲٫۵')
  expect(field.value).toBe('-۱۲٫۵')
  expect(document.activeElement).toBe(field)
})
