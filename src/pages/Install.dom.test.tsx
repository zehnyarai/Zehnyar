// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import Install from './Install'
import type { AppContext } from '../types'

afterEach(cleanup)
it('pauses installer downloads without asking for keys or destructive reinstall', async () => {
  const navigate = vi.fn()
  const { container } = render(<Install ctx={{ navigate } as unknown as AppContext} />)
  expect(screen.getByText(/انتشار فایل نصب تازه تا آماده شدن امضای ثابت متوقف است/)).toBeTruthy()
  expect(screen.getByText(/نیازی به ارسال دوبارهٔ کلیدهای سرویس/)).toBeTruthy()
  expect(container.querySelector('a[href$=".apk"]')).toBeNull()
  expect(screen.getByText(/برنامه یا داده‌ها را حذف نکنید/)).toBeTruthy()
  await userEvent.click(screen.getByRole('button', { name: 'داده‌ها و پشتیبان' }))
  expect(navigate).toHaveBeenCalledWith('settings')
})
