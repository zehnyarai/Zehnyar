import { describe, expect, it } from 'vitest'
import {
  AdminError,
  capabilities,
  digitsOnly,
  grouped,
  luhnValid,
  receiptsTotal,
  validateCard,
  validateReceipt,
} from './localAdmin'

const card = {
  card_number: '9401 6524 7311 6063',
  holder: 'احمد قرائی سلطان آبادی',
  bank: 'بانک ملی ایران',
  confirmed: true,
}
describe('owner card validation', () => {
  it('normalises Persian digits, spaces and dashes', () => {
    expect(digitsOnly('۹۴۰۱-۶۵۲۴ ۷۳۱۱ ۶۰۶۳')).toBe('9401652473116063')
    expect(digitsOnly('٩٤٠١ ٦٥٢٤ ٧٣١١ ٦٠٦٣')).toBe('9401652473116063')
    expect(grouped('9401652473116063')).toBe('9401 - 6524 - 7311 - 6063')
  })
  it('uses the Luhn checksum and rejects short or impossible numbers', () => {
    expect(luhnValid('9401652473116063')).toBe(true)
    // Both orders of the two digit groups pass the checksum, so arithmetic alone cannot
    // decide which one the owner means; only visual confirmation may.
    expect(luhnValid('6063731165249401')).toBe(true)
    expect(luhnValid('940165247311606')).toBe(false)
    expect(luhnValid('1234567890123456')).toBe(false)
  })
  it('refuses a card without the owner confirming the typed digits', () => {
    expect(() => validateCard({ ...card, confirmed: false })).toThrow(AdminError)
    expect(() => validateCard({ ...card, card_number: '1111 1111 1111 1111' })).toThrow(
      'شماره کارت'
    )
    expect(() => validateCard({ ...card, holder: 'ا' })).toThrow('نام صاحب کارت')
    expect(validateCard(card).card_number).toBe('9401652473116063')
  })
})
describe('manual receipt ledger', () => {
  it('accepts a plausible transfer and rejects impossible amounts or dates', () => {
    const row = validateReceipt({
      payer: 'باغدار نمونه',
      amount_toman: 990000,
      paid_at: '2026-10-12',
      reference: '123456',
      note: '',
    })
    expect(row.amount_toman).toBe(990000)
    expect(() => validateReceipt({ ...row, amount_toman: 500 })).toThrow('مبلغ')
    expect(() => validateReceipt({ ...row, amount_toman: 1.5 })).toThrow('مبلغ')
    expect(() => validateReceipt({ ...row, amount_toman: 900_000_000 })).toThrow('مبلغ')
    expect(() => validateReceipt({ ...row, paid_at: 'دیروز' })).toThrow('تاریخ')
    expect(() => validateReceipt({ ...row, payer: 'x' })).toThrow('نام پرداخت‌کننده')
  })
  it('sums the ledger without inventing entries', () => {
    expect(receiptsTotal([])).toBe(0)
    expect(
      receiptsTotal([
        {
          id: '1',
          payer: 'a',
          amount_toman: 1000,
          paid_at: '2026-01-01',
          reference: '',
          note: '',
          created_at: '',
        },
        {
          id: '2',
          payer: 'b',
          amount_toman: 2000,
          paid_at: '2026-01-02',
          reference: '',
          note: '',
          created_at: '',
        },
      ])
    ).toBe(3000)
  })
})
describe('capability board tells the truth about this build', () => {
  const base = {
    keyPresent: false,
    keyVerified: false,
    model: '',
    cardSaved: false,
    receipts: 0,
    orchards: 0,
    reports: 0,
    analyzed: 0,
    labs: 0,
  }
  it('marks device analysis as needing setup until a verified key exists', () => {
    const off = capabilities(base)
    expect(off.filter((c) => c.state === 'setup').map((c) => c.key)).toEqual([
      'vision-photo',
      'vision-lab',
      'sales',
      'ledger',
    ])
    const on = capabilities({
      ...base,
      keyPresent: true,
      keyVerified: true,
      model: 'gemini-2.5-flash',
    })
    expect(on.filter((c) => c.state === 'active').length).toBeGreaterThanOrEqual(6)
  })
  it('never advertises a gateway, sync, weather or iOS build that does not exist', () => {
    const rows = capabilities({ ...base, keyPresent: true, keyVerified: true, cardSaved: true })
    for (const key of ['gateway', 'sync', 'weather', 'ios'])
      expect(rows.find((c) => c.key === key)?.state).toBe('offline-blocked')
    expect(rows.find((c) => c.key === 'ledger')?.state).toBe('active')
    // The paid-package row only turns active once the owner actually set a price.
    expect(rows.find((c) => c.key === 'sales')?.state).toBe('setup')
    const priced = capabilities({
      ...base,
      keyPresent: true,
      keyVerified: true,
      cardSaved: true,
      packagePriced: true,
      freeLeft: 1,
    })
    expect(priced.find((c) => c.key === 'sales')?.state).toBe('active')
    expect(priced.find((c) => c.key === 'sales')?.detail).toContain('تومانی')
    expect(rows.every((c) => c.detail.length > 0)).toBe(true)
  })
})
