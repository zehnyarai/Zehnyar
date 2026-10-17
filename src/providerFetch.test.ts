import { afterEach, describe, expect, it, vi } from 'vitest'
import { providerFetch } from './providerFetch'

const native = vi.hoisted(() => ({ platform: true, request: vi.fn() }))
vi.mock('@capacitor/core', () => ({
  Capacitor: { isNativePlatform: () => native.platform },
  CapacitorHttp: { request: native.request },
}))
afterEach(() => {
  vi.unstubAllGlobals()
  native.platform = true
  native.request.mockReset()
})

describe('real provider transport selection', () => {
  it('uses native HTTP in APK, not a WebView preflight; JSON is serialized only once', async () => {
    const webFetch = vi.fn()
    vi.stubGlobal('fetch', webFetch)
    native.request.mockResolvedValue({
      status: 200,
      data: '{"choices":[]}',
      headers: { 'Content-Type': 'application/json' },
    })
    const response = await providerFetch('https://api.x.ai/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: 'Bearer test-key', 'Content-Type': 'application/json' },
      body: '{"model":"account-model","messages":[]}',
    })
    expect(webFetch).not.toHaveBeenCalled()
    expect(native.request).toHaveBeenCalledWith({
      url: 'https://api.x.ai/v1/chat/completions',
      method: 'POST',
      headers: { authorization: 'Bearer test-key', 'content-type': 'application/json' },
      data: { model: 'account-model', messages: [] },
      responseType: 'text',
      connectTimeout: 30000,
      readTimeout: 180000,
    })
    expect(await response.json()).toEqual({ choices: [] })
  })
  it('preserves an xAI string-error HTTP response for the admin diagnostics', async () => {
    native.request.mockResolvedValue({
      status: 403,
      data: { code: 'forbidden', error: 'Account has no credits' },
      headers: {},
    })
    const response = await providerFetch('https://api.x.ai/v1/models')
    expect(response.status).toBe(403)
    expect(response.ok).toBe(false)
    expect(await response.json()).toEqual({ code: 'forbidden', error: 'Account has no credits' })
  })
  it('uses ordinary fetch only in the web edition', async () => {
    native.platform = false
    const fetcher = vi.fn().mockResolvedValue(new Response('{}'))
    vi.stubGlobal('fetch', fetcher)
    const init = { headers: { Authorization: 'Bearer test-key' } }
    await providerFetch('https://api.x.ai/v1/models', init)
    expect(fetcher).toHaveBeenCalledWith('https://api.x.ai/v1/models', init)
    expect(native.request).not.toHaveBeenCalled()
  })
})
