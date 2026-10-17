import 'fake-indexeddb/auto'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { eraseLocalData, exportBackup, localApi, restoreBackup } from './standalone'
import { parseReceiptPacket, receiptPacket } from './receiptTransfer'
import type { LocalReceipt } from './localAdmin'
import { validateReceiptImage } from './localAdmin'

const image = 'data:image/jpeg;base64,/9j/4AAQSkZJRg=='
const post = (body: unknown) => ({ method: 'POST', body: JSON.stringify(body) })
const receipt = {
  payer: 'باغدار نمونه',
  amount_toman: 1_575_000,
  reference: '123456789',
  paid_at: '2026-10-17',
  note: 'بستهٔ پنج تحلیلی',
  image_data: image,
}
const row: LocalReceipt = {
  ...receipt,
  id: '12345678-1234-4321-9876-123456789012',
  created_at: '2026-10-17T12:00:00Z',
}

beforeEach(async () => {
  const storage = new Map<string, string>()
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => storage.set(key, value),
    removeItem: (key: string) => storage.delete(key),
  })
  await eraseLocalData()
})
afterEach(() => vi.unstubAllGlobals())

describe('photo receipt file exchange between two independent phones', () => {
  it('exports only payment fields and resets any user-supplied approval', () => {
    const packet = receiptPacket({
      ...row,
      confirmed_at: '2026-10-17',
      activation_code: 'forged',
      granted_analyses: 500,
    })
    expect(packet).not.toContain('activation_code')
    expect(packet).not.toContain('confirmed_at')
    const parsed = parseReceiptPacket(packet)
    expect(parsed).toMatchObject({
      imported: true,
      confirmed_at: null,
      image_data: image,
      amount_toman: 1575000,
    })
    expect(parsed.activation_code).toBeUndefined()
    const forged = JSON.parse(packet)
    forged.receipt.granted_analyses = 500
    forged.receipt.confirmed_at = 'today'
    expect(parseReceiptPacket(JSON.stringify(forged)).granted_analyses).toBeUndefined()
  })
  it('refuses scripts, links, huge files, non-receipts and missing tracking/image', () => {
    for (const value of [
      'data:image/svg+xml;base64,PHN2Zz4=',
      'https://example.com/a.jpg',
      'javascript:alert(1)',
      image.repeat(100000),
    ])
      expect(() => validateReceiptImage(value)).toThrow()
    for (const content of ['null', '{}', '[]', '<html>', 'a'.repeat(2200001)])
      expect(() => parseReceiptPacket(content)).toThrow()
    expect(() => receiptPacket({ ...row, image_data: undefined })).toThrow('عکس')
    expect(() => parseReceiptPacket(receiptPacket({ ...row, reference: '' }))).toThrow('کد پیگیری')
  })
  it('does not spend or grant anything until review, gives the manager a code not credits, and redeems once on the farmer phone', async () => {
    const saved = await localApi<LocalReceipt>('/local/billing/receipts', post(receipt))
    const senderBackup = await exportBackup()
    const { content } = await localApi<{ content: string }>(
      `/local/billing/receipts/${saved.id}/export`
    )
    expect((await localApi<{ credits: number }>('/local/quota')).credits).toBe(0)
    await eraseLocalData() // A separate manager device, not the farmer's database.
    const imported = await localApi<LocalReceipt>(
      '/local/billing/receipts/import',
      post({ content })
    )
    expect(imported.confirmed_at).toBeNull()
    expect((await localApi<{ credits: number }>('/local/quota')).credits).toBe(0)
    const confirmed = await localApi<{ credits: number; receipt: LocalReceipt }>(
      `/local/billing/receipts/${imported.id}/confirm`,
      { method: 'POST' }
    )
    expect(confirmed.credits).toBe(0) // Must never credit the manager's own phone.
    expect(confirmed.receipt.granted_analyses).toBe(5) // Discount honoured.
    expect(confirmed.receipt.activation_code).toMatch(/^PST-/)
    await expect(
      localApi(`/local/billing/receipts/${imported.id}/confirm`, { method: 'POST' })
    ).rejects.toThrow('قبلاً')
    await expect(localApi('/local/billing/receipts/import', post({ content }))).rejects.toThrow(
      'قبلاً'
    )
    await expect(
      localApi(`/local/billing/receipts/${imported.id}`, { method: 'DELETE' })
    ).rejects.toThrow('حذف')
    const managerBackup = await exportBackup()
    await eraseLocalData()
    await restoreBackup(managerBackup)
    const billing = await localApi<{ receipts: LocalReceipt[] }>('/local/billing')
    expect(billing.receipts[0]).toMatchObject({
      imported: true,
      image_data: image,
      activation_code: confirmed.receipt.activation_code,
      granted_analyses: 5,
    })
    await expect(
      localApi(`/local/billing/receipts/${imported.id}/confirm`, { method: 'POST' })
    ).rejects.toThrow('قبلاً')
    await eraseLocalData()
    await restoreBackup(senderBackup)
    const result = await localApi<{ credits: number }>(
      '/local/quota/redeem',
      post({ code: confirmed.receipt.activation_code })
    )
    expect(result.credits).toBe(5)
    await expect(
      localApi('/local/quota/redeem', post({ code: confirmed.receipt.activation_code }))
    ).rejects.toThrow('قبلاً')
  })
  it('refuses another receipt with the same tracking number even under a different ID', async () => {
    await localApi('/local/billing/receipts/import', post({ content: receiptPacket(row) }))
    await expect(
      localApi(
        '/local/billing/receipts/import',
        post({ content: receiptPacket({ ...row, id: 'another-unique-receipt-id' }) })
      )
    ).rejects.toThrow('کد پیگیری')
  })
  it('rejects an underpayment instead of gifting a paid analysis', async () => {
    const imported = await localApi<LocalReceipt>(
      '/local/billing/receipts/import',
      post({ content: receiptPacket({ ...row, amount_toman: 1000 }) })
    )
    await expect(
      localApi(`/local/billing/receipts/${imported.id}/confirm`, { method: 'POST' })
    ).rejects.toThrow('کافی نیست')
    expect((await localApi<{ credits: number }>('/local/quota')).credits).toBe(0)
  })
  it('keeps rejection reason, refuses later confirmation, and grants no credit', async () => {
    const imported = await localApi<LocalReceipt>(
      '/local/billing/receipts/import',
      post({ content: receiptPacket(row) })
    )
    await localApi(
      `/local/billing/receipts/${imported.id}/reject`,
      post({ reason: 'در گردش حساب واریز نبود' })
    )
    await expect(
      localApi(`/local/billing/receipts/${imported.id}/confirm`, { method: 'POST' })
    ).rejects.toThrow('رد شده')
    const backup = await exportBackup()
    await eraseLocalData()
    await restoreBackup(backup)
    const billing = await localApi<{ receipts: LocalReceipt[] }>('/local/billing')
    expect(billing.receipts[0].rejected_reason).toBe('در گردش حساب واریز نبود')
    expect((await localApi<{ credits: number }>('/local/quota')).credits).toBe(0)
  })
})
