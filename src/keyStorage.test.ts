import { beforeEach, afterEach, expect, it, vi } from 'vitest'
const mock = vi.hoisted(() => ({
  native: true,
  saved: null as string | null,
  fail: false,
  get: vi.fn(),
  set: vi.fn(),
}))
vi.mock('@capacitor/core', () => ({
  Capacitor: { isNativePlatform: () => mock.native },
  registerPlugin: () => ({ get: mock.get, set: mock.set }),
}))
let storage: Map<string, string>
const key = 'pestino-direct-vision'
const blob = (a = 'dummy-google-key', b = 'dummy-xai-key') =>
  JSON.stringify({
    version: 2,
    active: 'grok',
    slots: { gemini: { key: a }, grok: { key: b } },
    fallback: true,
  })
beforeEach(() => {
  vi.resetModules()
  storage = new Map()
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => storage.set(key, value),
    removeItem: (key: string) => storage.delete(key),
  })
  mock.native = true
  mock.saved = null
  mock.fail = false
  mock.get.mockReset().mockImplementation(async () => ({ value: mock.saved }))
  mock.set.mockReset().mockImplementation(async ({ value }: { value: string }) => {
    if (mock.fail) throw new Error('native failure with private data')
    mock.saved = value
  })
})
afterEach(() => vi.unstubAllGlobals())
it('migrates both legacy provider keys once, verifies native persistence, and removes plaintext WebView copy', async () => {
  storage.set(key, blob())
  const store = await import('./keyStorage')
  await store.initializeKeyStorage()
  expect(mock.saved).toBe(blob())
  expect(storage.has(key)).toBe(false)
  expect(store.readKeyStorage()).toBe(blob())
  await store.initializeKeyStorage()
  expect(mock.get).toHaveBeenCalledTimes(1)
})
it('recovers both keys after module/process restart without any WebView key copy', async () => {
  const store = await import('./keyStorage')
  await store.initializeKeyStorage()
  store.writeKeyStorage(blob())
  await store.flushKeyStorage()
  vi.resetModules()
  const restarted = await import('./keyStorage')
  await restarted.initializeKeyStorage()
  expect(restarted.readKeyStorage()).toBe(blob())
  expect(storage.has(key)).toBe(false)
})
it('does not destroy the legacy keys if secure migration fails', async () => {
  storage.set(key, blob())
  mock.fail = true
  const store = await import('./keyStorage')
  await store.initializeKeyStorage()
  expect(store.readKeyStorage()).toBe(blob())
  expect(storage.get(key)).toBe(blob())
  expect(store.keyStorageWarning()).toContain('پاک نکنید')
})
it('rejects failed native writes, restores the previous memory value, and can retry without losing either key', async () => {
  mock.saved = blob()
  const store = await import('./keyStorage')
  await store.initializeKeyStorage()
  mock.fail = true
  store.writeKeyStorage(blob('replacement', 'unchanged'))
  await expect(store.flushKeyStorage()).rejects.toThrow('تأیید نشد')
  expect(store.readKeyStorage()).toBe(blob())
  expect(mock.saved).toBe(blob())
  mock.fail = false
  store.writeKeyStorage(blob('replacement', 'unchanged'))
  await store.flushKeyStorage()
  expect(mock.saved).toBe(blob('replacement', 'unchanged'))
})
it('persists explicit per-provider deletion, rather than resurrecting an old key at next launch', async () => {
  mock.saved = blob()
  const store = await import('./keyStorage')
  await store.initializeKeyStorage()
  store.writeKeyStorage(blob('dummy-google-key', ''))
  await store.flushKeyStorage()
  vi.resetModules()
  const restarted = await import('./keyStorage')
  await restarted.initializeKeyStorage()
  expect(JSON.parse(restarted.readKeyStorage()!).slots.grok.key).toBe('')
  expect(JSON.parse(restarted.readKeyStorage()!).slots.gemini.key).toBe('dummy-google-key')
})
it('does not report a successful web save if localStorage silently drops writes', async () => {
  mock.native = false
  vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {} })
  const store = await import('./keyStorage')
  expect(() => store.writeKeyStorage(blob())).toThrow('تأیید نشد')
  expect(mock.set).not.toHaveBeenCalled()
})
