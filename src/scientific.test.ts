import { describe, expect, it } from 'vitest'
import {
  EMPTY_CONTEXT,
  careChecklist,
  interpretLab,
  parseLabValues,
  validateContext,
} from './scientific'
import { validateField } from './fieldwork'

describe('measured lab values, not invented diagnosis', () => {
  it('keeps missing distinct from zero and rejects empty/invalid measurements', () => {
    expect(parseLabValues('soil', { ph: '7.8', ec: '', organic: '0' })).toEqual({
      ph: 7.8,
      organic: 0,
    })
    expect(() => parseLabValues('soil', { ec: '' })).toThrow('حداقل')
    for (const ph of ['NaN', 'Infinity', '-1', '15'])
      expect(() => parseLabValues('soil', { ph })).toThrow('معتبر')
  })
  it('does not apply ECe thresholds to diluted/unknown extraction', () => {
    for (const method of ['unknown', '1:5', '1:2.5'])
      expect(interpretLab('soil', { ec: 7 }, method).findings[0].title).toContain('روش')
    expect(interpretLab('soil', { ec: 7 }, 'saturated').findings[0].title).toContain('ECe')
    expect(interpretLab('soil', { ec: 7 }, 'saturated').findings[0].basis).toContain(
      'آستانه افت محصول پسته نیست'
    )
  })
  it.each([
    [0.69, 'neutral'],
    [0.7, 'caution'],
    [3, 'caution'],
    [3.01, 'caution'],
  ])('states the generic FAO scope for ECw=%s', (ec, tone) => {
    const f = interpretLab('water', { ec: ec as number }, 'water').findings[0]
    expect(f.tone).toBe(tone)
    expect(f.basis).toContain('نه آستانه اختصاصی پسته')
  })
  it('calculates SAR and RSC only from provided mg/L, with explicit conversions', () => {
    const report = interpretLab(
      'water',
      { sodium: 229.898, calcium: 40.078, magnesium: 24.305, bicarbonate: 122.0336, carbonate: 0 },
      'water'
    )
    expect(report.calculations[0].value).toBeCloseTo(10 / Math.sqrt(2), 6)
    expect(report.calculations[1].value).toBeCloseTo(-2, 6)
    expect(report.calculations[0].formula).toContain('meq/L')
  })
  it('never substitutes missing ions or divides by zero', () => {
    expect(interpretLab('water', { sodium: 230, calcium: 20 }, 'water').calculations).toEqual([])
    const report = interpretLab('water', { sodium: 230, calcium: 0, magnesium: 0 }, 'water')
    expect(report.calculations).toEqual([])
    expect(report.findings[0].title).toContain('قابل محاسبه نیست')
  })
  it('does not infer nutrient deficiency or application doses from ppm values', () => {
    const report = interpretLab('soil', { nitrogen: 15, iron: 1, potassium: 100 }, 'unknown')
    expect(report.findings[0].text).toContain('برچسب کمبود یا برنامه کوددهی تولید نمی‌شود')
    expect(report.limitations.join(' ')).toContain('نسخه کود و سم')
  })
  it('rejects unknown lab keys and mismatched sample methods', () => {
    const input = {
      kind: 'soil',
      values: { ph: 8 },
      method: 'water',
      sample_date: '2026-10-11',
      depth: '',
      orchard_id: null,
      notes: '',
    }
    expect(() => validateField('labs', input)).toThrow('سازگار')
    expect(() => interpretLab('soil', { secret: 1 }, 'unknown')).toThrow('معتبر')
  })
})
describe('contextual care is not image inference', () => {
  it('validates reported numbers/symptoms and never produces a confidence score', () => {
    const c = validateContext({ ...EMPTY_CONTEXT, symptoms: ['sticky', 'yield'] })
    expect(careChecklist(c).guides).toContain('psylla')
    expect(careChecklist(c).guides).toContain('pollination')
    expect(JSON.stringify(careChecklist(c))).not.toContain('confidence')
    expect(() => validateContext({ ...c, affected_percent: '101' })).toThrow('معتبر')
    expect(() => validateContext({ ...c, symptoms: ['invented'] })).toThrow('نشانه')
  })
  it('requires dated sourced prices and correctly ordered weather observations', () => {
    const price = {
      cultivar: 'اکبری',
      price: 100,
      currency: 'toman',
      province: 'کرمان',
      source: 'بازار محلی',
      observed_date: '2026-02-31',
      grade: '',
    }
    expect(() => validateField('prices', price)).toThrow('تاریخ')
    const climate = {
      province: 'کرمان',
      observed_date: '2026-10-11',
      minimum: 15,
      maximum: 5,
      humidity: null,
      wind: null,
      stage: '',
      source: 'دماسنج باغ',
    }
    expect(() => validateField('climate', climate)).toThrow('کمینه')
  })
})
