import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, checkImage, dueLabel, fa, relativeDate, today } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('first-party API client', () => {
  it('localizes network errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(api('/bootstrap')).rejects.toMatchObject({ status: 0 })
    await expect(api('/bootstrap')).rejects.toThrow('اتصال اینترنت را بررسی')
  })
  it('does not crash on a null error response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('null', { status: 503 })))
    await expect(api('/bootstrap')).rejects.toBeInstanceOf(ApiError)
  })
  it('sends JSON without exposing credentials', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }))
    vi.stubGlobal('fetch', fetcher)
    expect(
      await api('/tasks', { method: 'POST', body: JSON.stringify({ title: 'بازدید' }) })
    ).toEqual({ ok: true })
    expect(fetcher).toHaveBeenCalledWith(
      '/api/tasks',
      expect.objectContaining({
        credentials: 'same-origin',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      })
    )
  })
  it('lets the browser set the multipart boundary', async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response('{}'))
    vi.stubGlobal('fetch', fetcher)
    await api('/analyses', { method: 'POST', body: new FormData() })
    expect(fetcher.mock.calls[0][1].headers['Content-Type']).toBeUndefined()
  })
  it('shows the server error, rather than a fabricated result', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          new Response(JSON.stringify({ detail: 'تحلیل هنوز متصل نیست' }), { status: 503 })
        )
    )
    await expect(api('/analyses')).rejects.toMatchObject({
      message: 'تحلیل هنوز متصل نیست',
      status: 503,
    })
  })
  it('handles malformed responses safely', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('<html>proxy error</html>', { status: 502 }))
    )
    await expect(api('/bootstrap')).rejects.toBeInstanceOf(ApiError)
  })
  it('does not echo raw validation objects', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: [{ input: 'secret', msg: 'invalid' }] }), {
          status: 422,
        })
      )
    )
    await expect(api('/auth/login')).rejects.toThrow('اطلاعات واردشده معتبر نیست')
  })
})

describe('Persian presentation and image selection', () => {
  it('formats numbers using Persian digits', () => expect(fa(1460)).toBe('۱٬۴۶۰'))
  it('uses the Tehran date around midnight', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-08T21:00:00Z'))
    expect(today()).toBe('2026-10-09')
  })
  it('labels relative task dates', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-09T12:00:00Z'))
    expect(dueLabel('2026-10-09')).toBe('امروز')
    expect(dueLabel('2026-10-10')).toBe('فردا')
    expect(dueLabel('2026-10-08')).toBe('گذشته')
    expect(relativeDate('2026-10-08T03:00:00Z')).toBe('دیروز')
  })
  it('accepts supported images and rejects other formats', () => {
    expect(checkImage(new File(['ok'], 'leaf.jpg', { type: 'image/jpeg' }))).toBeNull()
    expect(checkImage(new File(['no'], 'leaf.svg', { type: 'image/svg+xml' }))).toContain('JPG')
  })
  it('rejects oversized images locally', () => {
    expect(
      checkImage(
        new File([new Uint8Array(8 * 1024 * 1024 + 1)], 'leaf.jpg', { type: 'image/jpeg' })
      )
    ).toContain('۸ مگابایت')
  })
})
