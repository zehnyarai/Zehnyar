import { Capacitor, registerPlugin } from '@capacitor/core'

const KEY = 'pestino-direct-vision'
const vault = registerPlugin<{
  get: () => Promise<{ value: string | null }>
  set: (options: { value: string }) => Promise<void>
}>('PestinoKeyVault')
let cache: string | null = null
let initialized: Promise<void> | null = null
let queue = Promise.resolve()
let warning = ''

function legacyRead(): string | null {
  try {
    return globalThis.localStorage?.getItem(KEY) ?? null
  } catch {
    return null
  }
}
function validBlob(value: unknown): value is string {
  if (typeof value !== 'string' || value.length > 30000) return false
  try {
    const data = JSON.parse(value)
    return (
      !!data &&
      typeof data === 'object' &&
      ((data.version === 2 && data.slots && typeof data.slots === 'object') ||
        typeof data.key === 'string')
    )
  } catch {
    return false
  }
}
/** Native keys survive WebView storage loss and process restarts; never part of backups. */
export async function initializeKeyStorage(): Promise<void> {
  if (!Capacitor.isNativePlatform()) return
  if (!initialized)
    initialized = (async () => {
      const legacy = legacyRead()
      try {
        const stored = (await vault.get()).value
        cache = validBlob(legacy) ? legacy : validBlob(stored) ? stored : null
        if (validBlob(legacy)) {
          await vault.set({ value: legacy })
          try {
            globalThis.localStorage?.removeItem(KEY)
          } catch {
            /* Migration is already durable. */
          }
        }
        warning = ''
      } catch {
        cache = validBlob(legacy) ? legacy : null
        warning =
          'ذخیره‌سازی امن کلید روی دستگاه در دسترس نیست؛ داده‌های برنامه را پاک نکنید. ثبت کلید را دوباره امتحان کنید.'
        // Orchard/backup pages must still boot if the OS keystore is unavailable.
      }
    })()
  await initialized
}
export function keyStorageWarning(): string {
  return warning
}
export function readKeyStorage(): string | null {
  return Capacitor.isNativePlatform() ? (cache ?? legacyRead()) : legacyRead()
}
export function writeKeyStorage(value: string): void {
  if (!Capacitor.isNativePlatform()) {
    try {
      const store = globalThis.localStorage
      store.setItem(KEY, value)
      if (store.getItem(KEY) !== value) throw new Error('write verification failed')
    } catch {
      throw new Error(
        'ذخیره‌سازی کلید روی این دستگاه تأیید نشد؛ حالت خصوصی مرورگر و فضای آزاد را بررسی کنید.'
      )
    }
    return
  }
  const previous = cache
  cache = value
  queue = queue
    .catch(() => {})
    .then(async () => {
      try {
        await vault.set({ value })
        warning = ''
        try {
          globalThis.localStorage?.removeItem(KEY)
        } catch {
          /* Native vault is authoritative. */
        }
      } catch {
        if (cache === value) cache = previous
        warning = 'ذخیرهٔ پایدار کلید تأیید نشد؛ کلید قبلی حذف نشده است. دوباره ذخیره کنید.'
        throw new Error(warning)
      }
    })
  // Synchronous settings callers enqueue writes; settings API explicitly awaits durability.
  void queue.catch(() => {})
}
export async function flushKeyStorage(): Promise<void> {
  await queue
}
