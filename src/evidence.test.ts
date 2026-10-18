import { describe, expect, it } from 'vitest'
import cases from '../tests/fixtures/evidence-cases.json'
import reasoning from '../tests/fixtures/decision-reasoning.json'
import {
  selectEvidence,
  buildScientificBasis,
  evidencePrompt,
  hasDecisionReasoning,
  scientificBasisText,
} from './evidence'
import { RESEARCH } from './research'

describe('case-bound dated scientific context', () => {
  for (const row of cases)
    it(`shares deterministic selection with server: ${row.name}`, () => {
      expect(selectEvidence(row.context).map((r) => r.id)).toEqual(row.ids)
    })
  it('does not pad a small or empty evidence packet with irrelevant papers', () => {
    expect(selectEvidence({})).toEqual([])
    expect(selectEvidence({ tree_part: 'برگ', notes: 'لکه' })).toHaveLength(1)
    expect(selectEvidence({ notes: 'پسیل و عسلک' }, 0)).toEqual([])
    expect(
      selectEvidence({ notes: 'آبیاری شوری پایه پسیل آفلاتوکسین نیتروژن گل' }, 100).length
    ).toBeLessThanOrEqual(8)
  })
  it('does not let a novel trap trial crowd out applicable IPM guidance', () => {
    const pack = selectEvidence({ notes: 'پسیل و عسلک' })
    expect(pack.some((r) => r.kind === 'extension')).toBe(true)
    expect(pack.some((r) => r.id === 'psylla-overwintering-2025')).toBe(true)
    expect(pack.find((r) => r.id === 'psylla-overwintering-2025')!.limitations).toContain(
      'کاهش خسارت'
    )
  })
  it('sends real measurements and dates/access/transfer limits, not JSON field-name matches', () => {
    const pack = selectEvidence({ sample: { values: { ec: 0 } } })
    expect(pack.map((r) => r.id)).toContain('iran-water-quality')
    const prompt = evidencePrompt(pack)
    expect(prompt.live_search).toBe(false)
    expect(prompt.records[0]).toMatchObject({
      url: expect.stringContaining('https://'),
      checked_at: expect.any(String),
      access: expect.any(String),
      limitations: expect.any(String),
    })
    expect(selectEvidence({ values: { ec: '' } })).toEqual([])
  })
  it('only resolves references actually supplied; generated URLs/dates/approval cannot replace registry metadata', () => {
    const pack = selectEvidence({ notes: 'خشکیدگی تنه' })
    const basis = buildScientificBasis(
      {
        ...reasoning,
        research_ids: [pack[0].id, pack[0].id, 'pgpr-salinity-2026', 'made-up'],
        research_claims: [
          {
            statement: 'آزمون بیماری‌زایی جای مشاهده عکس را نمی‌گیرد.',
            source_ids: [pack[0].id, 'made-up'],
            application_limit: 'این باغ در مطالعه نبوده است.',
          },
        ],
        url: 'https://fake.invalid',
        checked_at: '2099-01-01',
        expert_reviewed: true,
      },
      pack
    )
    expect(basis.sources).toEqual([pack[0]])
    expect(basis.reasoning.research_ids).toEqual([pack[0].id])
    expect(basis.locally_validated).toBe(false)
    expect(basis.sources[0].checked_at).not.toBe('2099-01-01')
    expect(scientificBasisText(basis)).toContain(pack[0].url)
    expect(scientificBasisText(basis)).not.toContain('fake.invalid')
  })
  it('reports an evidence gap rather than making an uncited source a citation', () => {
    const pack = selectEvidence({ notes: 'پسیل' })
    const basis = buildScientificBasis(reasoning, pack)
    expect(basis.supplied_source_ids.length).toBeGreaterThan(0)
    expect(basis.sources).toEqual([])
    expect(basis.reasoning.research_ids).toEqual([])
    expect(basis.live_search).toBe(false)
  })
  it('keeps old review dates honest after a selective update', () => {
    expect(RESEARCH.as_of).toBe('2026-10-18')
    expect(RESEARCH.records.find((r) => r.id === 'rootstock-review')!.checked_at).toBe('2026-10-12')
    expect(RESEARCH.records.find((r) => r.id === 'iran-trunk-pathogens-2026')!.access).toBe(
      'publisher-abstract'
    )
    expect(RESEARCH.records.filter((r) => r.id === 'spain-water-five-year')).toHaveLength(1)
  })
  it('requires every reasoning dimension, bounds hostile lists, and does not equate structure with truth', () => {
    expect(hasDecisionReasoning(reasoning)).toBe(true)
    expect(hasDecisionReasoning({ ...reasoning, alternatives: [] })).toBe(false)
    expect(hasDecisionReasoning(null)).toBe(false)
    const basis = buildScientificBasis(
      {
        ...reasoning,
        reassessment: Array(40).fill('پایش'),
        alternatives: [null, {}, 'a'.repeat(1001)],
      },
      []
    )
    expect(basis.reasoning.reassessment).toHaveLength(8)
    expect(basis.reasoning.alternatives).toEqual([])
    expect(basis.locally_validated).toBe(false)
  })
})
