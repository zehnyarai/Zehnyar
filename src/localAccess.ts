/**
 * Owner-defined admin lock for the offline edition.
 *
 * Nobody is asked for a password they do not have: the app is open, and the owner can
 * define/change/remove the admin password here. The lock protects the card number, the
 * receipt ledger and provider settings from someone who borrows the phone — it is not
 * disk encryption, and the backup file stays unencrypted.
 *
 * PBKDF2-SHA256 is used when WebCrypto is available (secure context, e.g. the packaged
 * app). Older WebViews without WebCrypto fall back to a salted iterated hash that is
 * explicitly weaker and is labelled as such in the UI.
 */
const KEY = 'pestino-admin-lock'
const ATTEMPTS = 'pestino-admin-attempts'
const SESSION = 'pestino-admin-unlocked'
export const MIN_PASSWORD = 8
const ITERATIONS = 120_000
const FALLBACK_ROUNDS = 20_000
const MAX_FAILS = 5
const LOCK_SECONDS = 60

export class AccessError extends Error {
  status = 400
}

export interface AdminLock {
  version: 1
  algo: 'pbkdf2-sha256' | 'iterated-fnv1a'
  iterations: number
  salt: string
  hash: string
  hint: string
  updated_at: string
}
interface Attempts {
  fails: number
  until: number
}

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>
function store(): StorageLike | null {
  try {
    const value = globalThis.localStorage
    return value && typeof value.getItem === 'function' && typeof value.setItem === 'function'
      ? value
      : null
  } catch {
    return null
  }
}
function sessionStore(): StorageLike | null {
  try {
    const value = globalThis.sessionStorage
    return value && typeof value.getItem === 'function' && typeof value.setItem === 'function'
      ? value
      : null
  } catch {
    return null
  }
}
function randomHex(bytes: number): string {
  const value = new Uint8Array(bytes)
  if (typeof crypto.getRandomValues === 'function') crypto.getRandomValues(value)
  else for (let i = 0; i < bytes; i += 1) value[i] = Math.floor(Math.random() * 256)
  return [...value].map((b) => b.toString(16).padStart(2, '0')).join('')
}
function hex(buffer: ArrayBuffer): string {
  return [...new Uint8Array(buffer)].map((b) => b.toString(16).padStart(2, '0')).join('')
}
/** Salted iterated FNV-1a for old WebViews only; slower to attack than plain text, weaker than PBKDF2. */
function fallbackHash(password: string, salt: string, rounds: number): string {
  const seed = `${salt}:${password}`
  let a = 0x811c9dc5
  let b = 0x01000193
  for (let round = 0; round < rounds; round += 1) {
    for (let i = 0; i < seed.length; i += 1) {
      a = (a ^ seed.charCodeAt(i)) >>> 0
      a = Math.imul(a, 0x01000193) >>> 0
      b = (b + a + (round & 255)) >>> 0
      b = (b ^ (b >>> 13)) >>> 0
    }
  }
  return (a >>> 0).toString(16).padStart(8, '0') + (b >>> 0).toString(16).padStart(8, '0')
}
async function derive(
  password: string,
  salt: string,
  rounds: number
): Promise<{ algo: AdminLock['algo']; hash: string }> {
  const subtle = globalThis.crypto?.subtle
  if (subtle) {
    try {
      const material = await subtle.importKey(
        'raw',
        new TextEncoder().encode(password),
        'PBKDF2',
        false,
        ['deriveBits']
      )
      const bits = await subtle.deriveBits(
        {
          name: 'PBKDF2',
          salt: new TextEncoder().encode(salt),
          iterations: rounds,
          hash: 'SHA-256',
        },
        material,
        256
      )
      return { algo: 'pbkdf2-sha256', hash: hex(bits) }
    } catch {
      // Fall through to the documented weaker mode rather than storing anything in clear.
    }
  }
  return { algo: 'iterated-fnv1a', hash: fallbackHash(password, salt, FALLBACK_ROUNDS) }
}
function same(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let diff = 0
  for (let i = 0; i < a.length; i += 1) diff |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return diff === 0
}
export function validateAdminPassword(password: unknown, repeat?: unknown): string {
  if (typeof password !== 'string' || password.length < MIN_PASSWORD || password.length > 128)
    throw new AccessError(`رمز مدیر باید حداقل ${MIN_PASSWORD} کاراکتر باشد.`)
  if (/\s/.test(password)) throw new AccessError('رمز مدیر نباید فاصله داشته باشد.')
  if (repeat !== undefined && repeat !== password)
    throw new AccessError('رمز و تکرار آن یکسان نیستند.')
  return password
}
export function adminLock(): AdminLock | null {
  const raw = store()?.getItem(KEY)
  if (!raw) return null
  try {
    const value = JSON.parse(raw) as Partial<AdminLock>
    if (
      value.version !== 1 ||
      typeof value.hash !== 'string' ||
      typeof value.salt !== 'string' ||
      (value.algo !== 'pbkdf2-sha256' && value.algo !== 'iterated-fnv1a')
    )
      return null
    return {
      version: 1,
      algo: value.algo,
      iterations: Number(value.iterations) || ITERATIONS,
      salt: value.salt,
      hash: value.hash,
      hint: typeof value.hint === 'string' ? value.hint : '',
      updated_at: typeof value.updated_at === 'string' ? value.updated_at : '',
    }
  } catch {
    return null
  }
}
export const hasAdminLock = () => adminLock() !== null
export const weakAdminLock = () => adminLock()?.algo === 'iterated-fnv1a'

export async function setAdminPassword(
  password: unknown,
  hint = '',
  repeat?: unknown
): Promise<AdminLock> {
  const checked = validateAdminPassword(password, repeat)
  if (typeof hint !== 'string' || hint.length > 80) throw new AccessError('راهنمای رمز معتبر نیست.')
  const salt = randomHex(16)
  const { algo, hash } = await derive(checked, salt, ITERATIONS)
  const lock: AdminLock = {
    version: 1,
    algo,
    iterations: algo === 'pbkdf2-sha256' ? ITERATIONS : FALLBACK_ROUNDS,
    salt,
    hash,
    hint: hint.trim(),
    updated_at: new Date().toISOString(),
  }
  const target = store()
  if (!target) throw new AccessError('ذخیره‌سازی این دستگاه در دسترس نیست.')
  target.setItem(KEY, JSON.stringify(lock))
  clearAttempts()
  unlock()
  return lock
}
/**
 * The owner asked for a password to exist from day one instead of an open panel. This
 * seeds one default lock per device, once; the owner can change it in the panel and can
 * always clear it with the documented recovery phrase.
 */
export const DEFAULT_ADMIN_PASSWORD = 'Pestino1404'
const SEEDED = 'pestino-admin-seeded'
export async function ensureDefaultAdminLock(): Promise<boolean> {
  if (hasAdminLock()) return false
  const target = store()
  if (target?.getItem(SEEDED)) return false
  await setAdminPassword(
    DEFAULT_ADMIN_PASSWORD,
    'رمز پیش‌فرض مالک؛ در پنل عوض کنید.',
    DEFAULT_ADMIN_PASSWORD
  )
  target?.setItem(SEEDED, '1')
  lockNow()
  return true
}
export function removeAdminLock(): void {
  store()?.removeItem(KEY)
  clearAttempts()
  sessionStore()?.removeItem(SESSION)
}
function attempts(): Attempts {
  try {
    const value = JSON.parse(store()?.getItem(ATTEMPTS) ?? '{}') as Partial<Attempts>
    return { fails: Number(value.fails) || 0, until: Number(value.until) || 0 }
  } catch {
    return { fails: 0, until: 0 }
  }
}
function clearAttempts() {
  store()?.removeItem(ATTEMPTS)
}
/** Seconds the owner must wait after repeated wrong passwords (0 when not blocked). */
export function lockoutSeconds(): number {
  const state = attempts()
  const remaining = Math.ceil((state.until - Date.now()) / 1000)
  return remaining > 0 ? remaining : 0
}
export function failedAttempts(): number {
  return attempts().fails
}
/** A successful or failed check; failures are rate limited, never answered optimistically. */
export async function verifyAdminPassword(password: unknown): Promise<boolean> {
  const lock = adminLock()
  if (!lock) return true
  if (lockoutSeconds() > 0)
    throw new AccessError(`پس از چند تلاش ناموفق، ${lockoutSeconds()} ثانیه صبر کنید.`)
  if (typeof password !== 'string' || !password) {
    recordFailure()
    return false
  }
  const { hash } = await derive(password, lock.salt, lock.iterations)
  const ok = same(hash, lock.hash)
  if (ok) {
    clearAttempts()
    unlock()
    return true
  }
  recordFailure()
  return false
}
function recordFailure() {
  const state = attempts()
  const fails = state.fails + 1
  const blocked = fails >= MAX_FAILS
  store()?.setItem(
    ATTEMPTS,
    JSON.stringify({
      fails: blocked ? 0 : fails,
      until: blocked ? Date.now() + LOCK_SECONDS * 1000 : 0,
    })
  )
}
export function unlock() {
  sessionStore()?.setItem(SESSION, String(Date.now()))
}
export function lockNow() {
  sessionStore()?.removeItem(SESSION)
}
/** Unlock lasts for the current app session only; closing the app locks again. */
export function isUnlocked(): boolean {
  return !adminLock() || !!sessionStore()?.getItem(SESSION)
}
export const REQUIREMENT_TEXT = `رمز مدیر را خودتان تعریف می‌کنید (حداقل ${MIN_PASSWORD} کاراکتر، بدون فاصله). این رمز فقط برای باز کردن پنل مدیر روی همین دستگاه است؛ کاربران و باغداران هیچ رمز یا شماره همراهی لازم ندارند.`
export const FORGOT_TEXT =
  'اگر رمز را فراموش کردید، می‌توانید قفل مدیر را بردارید؛ داده‌ها، کارت و دفتر دریافتی پاک نمی‌شوند. توجه: فایل پشتیبان و داده‌های روی دستگاه رمزگذاری نشده‌اند و قفل فقط مانع دسترسی از داخل برنامه است.'
