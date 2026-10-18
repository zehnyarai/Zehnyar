import { expect, it } from 'vitest'
import { parseMarketNumber, validateField } from './fieldwork'
it('accepts Persian/Arabic phone digits, grouped prices and signed decimal temperatures', () => {
  expect(parseMarketNumber('۲٬۷۵۰٬۰۰۰')).toBe(2750000)
  expect(parseMarketNumber('٢٧٥٠٠٠٠')).toBe(2750000)
  expect(parseMarketNumber('-۱۲٫۵')).toBe(-12.5)
  expect(parseMarketNumber(' 18.25 ')).toBe(18.25)
})
it('never silently removes invalid price characters or bypasses existing price limits', () => {
  for (const value of ['۲,۷۵', '۲۷۵۰ هزار', '1e6', '', 'abc', '1.2.3'])
    expect(() => parseMarketNumber(value)).toThrow()
  expect(() =>
    validateField('prices', { price: parseMarketNumber('0'), currency: 'toman' })
  ).toThrow()
})
