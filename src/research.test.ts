import { expect, it } from 'vitest'
import { RESEARCH, searchResearch, EVIDENCE_LABELS, ACCESS_LABELS } from './research'

it('keeps a dated non-exhaustive evidence map separate from validated diagnosis', () => {
  expect(RESEARCH.records).toHaveLength(24)
  expect(RESEARCH.reviewed_by_local_expert).toBe(false)
  expect(RESEARCH.scope).toContain('نه جستجوی جامع')
  expect(new Set(RESEARCH.records.map((r) => r.id)).size).toBe(24)
  for (const r of RESEARCH.records) {
    expect(r.expert_reviewed).toBe(false)
    expect(new URL(r.url).protocol).toBe('https:')
    expect(r.checked_at).toBe(RESEARCH.as_of)
    expect(r.limitations.length).toBeGreaterThan(45)
    expect(EVIDENCE_LABELS[r.kind]).toBeTruthy()
    expect(ACCESS_LABELS[r.access]).toBeTruthy()
    if (r.year !== null) expect(r.year).toBeLessThanOrEqual(2026)
  }
})
it('finds uncertainty alongside aflatoxin image research', () => {
  const rows = searchResearch('آفلاتوکسین')
  expect(rows.length).toBeGreaterThan(1)
  expect(
    rows.some((r) => r.id === 'hsi-aflatoxin' && r.limitations.includes('دقت پستینو نیست'))
  ).toBe(true)
})
it('does not turn a seedling drought trial into an orchard water prescription', () => {
  const r = RESEARCH.records.find((r) => r.id === 'iran-drought-seedlings')!
  expect(r.finding).toContain('دانهال')
  expect(r.limitations).toContain('مجوز کاهش')
  expect(r.kind).toBe('controlled')
})
it('recent filter uses publication year, not the date of search', () => {
  const rows = searchResearch('', 'all', true)
  expect(rows.length).toBeGreaterThan(10)
  expect(rows.every((r) => r.year !== null && r.year >= 2024)).toBe(true)
  expect(rows.some((r) => r.id === 'nitrogen-budget')).toBe(false)
})
it('distinguishes no search match from absence of research worldwide', () => {
  expect(searchResearch('unseen-impossible-token')).toEqual([])
  expect(searchResearch('', 'آب و خاک').every((r) => r.topic === 'آب و خاک')).toBe(true)
})
