import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  AccessError,
  adminLock,
  failedAttempts,
  hasAdminLock,
  isUnlocked,
  lockNow,
  lockoutSeconds,
  removeAdminLock,
  setAdminPassword,
  validateAdminPassword,
  verifyAdminPassword,
  weakAdminLock,
} from './localAccess'

const store = new Map<string, string>()
const session = new Map<string, string>()
beforeEach(() => {
  store.clear()
  session.clear()
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
  })
  vi.stubGlobal('sessionStorage', {
    getItem: (k: string) => session.get(k) ?? null,
    setItem: (k: string, v: string) => void session.set(k, v),
    removeItem: (k: string) => void session.delete(k),
  })
})

describe('owner-defined admin password', () => {
  it('starts with no lock at all, so nobody is asked for a password they never chose', () => {
    expect(hasAdminLock()).toBe(false)
    expect(isUnlocked()).toBe(true)
    expect(adminLock()).toBeNull()
  })
  it('refuses weak or mistyped passwords before storing anything', async () => {
    expect(() => validateAdminPassword('short')).toThrow(AccessError)
    expect(() => validateAdminPassword('has space here')).toThrow('فاصله')
    expect(() => validateAdminPassword('longenough1', 'longenough2')).toThrow('تکرار')
    await expect(setAdminPassword('short', '')).rejects.toThrow(AccessError)
    expect(hasAdminLock()).toBe(false)
  })
  it('stores a salted hash, never the password itself', async () => {
    const password = 'bagh-peste-1404'
    await setAdminPassword(password, 'سال تولد باغ')
    const raw = store.get('pestino-admin-lock') ?? ''
    expect(raw).not.toContain(password)
    const lock = adminLock()
    expect(lock?.salt).toHaveLength(32)
    expect(lock?.hash.length).toBeGreaterThanOrEqual(16)
    expect(lock?.hint).toBe('سال تولد باغ')
    expect(lock?.algo).toBe('pbkdf2-sha256')
    expect(weakAdminLock()).toBe(false)
  })
  it('accepts only the right password once the lock exists', async () => {
    await setAdminPassword('bagh-peste-1404')
    lockNow()
    expect(isUnlocked()).toBe(false)
    expect(await verifyAdminPassword('wrong-password')).toBe(false)
    expect(isUnlocked()).toBe(false)
    expect(await verifyAdminPassword('bagh-peste-1404')).toBe(true)
    expect(isUnlocked()).toBe(true)
  })
  it('blocks repeated attempts briefly instead of allowing endless guessing', async () => {
    await setAdminPassword('bagh-peste-1404')
    lockNow()
    for (let i = 0; i < 5; i += 1) expect(await verifyAdminPassword('nope')).toBe(false)
    expect(lockoutSeconds()).toBeGreaterThan(0)
    await expect(verifyAdminPassword('bagh-peste-1404')).rejects.toThrow('صبر کنید')
    // The counter resets after the block expires, but never turns into a silent unlock.
    expect(failedAttempts()).toBe(0)
  })
  it('changing the password invalidates the previous one', async () => {
    await setAdminPassword('bagh-peste-1404')
    await setAdminPassword('bagh-peste-1405')
    lockNow()
    expect(await verifyAdminPassword('bagh-peste-1404')).toBe(false)
    expect(await verifyAdminPassword('bagh-peste-1405')).toBe(true)
  })
  it('removing the lock keeps data untouched and opens the panel again', async () => {
    store.set('pestino-data', '{"orchards":1}')
    await setAdminPassword('bagh-peste-1404')
    removeAdminLock()
    expect(hasAdminLock()).toBe(false)
    expect(store.get('pestino-data')).toBe('{"orchards":1}')
    expect(isUnlocked()).toBe(true)
  })
})
