/** Traceable, dated context; retrieval is NOT verification of a diagnosis or a live search. */
import { RESEARCH } from './research'
import type { ResearchRecord } from './research'
import rules from './data/evidence-rules.json'
import decisionContract from './data/decision-contract.json'

export const SCIENCE_NOTICE =
  'این گزارش بر منابع گزینشیِ تاریخ‌دار تکیه دارد؛ جست‌وجوی زنده و جامعِ تازه‌ترین مقالات یا تأیید کارشناس محلی نیست.'
export interface DecisionReasoning {
  supporting_evidence: string[]
  alternatives: string[]
  discriminating_checks: string[]
  missing_information: string[]
  reassessment: string[]
  referral_triggers: string[]
  research_ids: string[]
  research_claims: { statement: string; source_ids: string[]; application_limit: string }[]
}
export interface ScientificBasis {
  version: 1
  catalog_version: string
  catalog_updated_at: string
  live_search: false
  locally_validated: false
  notice: string
  reasoning: DecisionReasoning
  /** Only records actually supplied AND cited; URLs/dates never come from generated text. */
  sources: ResearchRecord[]
  supplied_source_ids: string[]
}
export function normalizeEvidenceText(text: string): string {
  return text
    .replace(/ي/g, 'ی')
    .replace(/ك/g, 'ک')
    .replace(/[\u200c\u200e\u200f-]/g, ' ')
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim()
}
function valuesText(value: unknown, depth = 0): string {
  if (depth > 8) return ''
  if (typeof value === 'string') return value.slice(0, 12000)
  if (!value || typeof value !== 'object') return ''
  // Structural keys ("water_ec": "") must not manufacture a topic match.
  return Object.entries(value)
    .slice(0, 100)
    .map(([key, item]) =>
      typeof item === 'number' &&
      Number.isFinite(item) &&
      [
        'ec',
        'sar',
        'rsc',
        'boron',
        'sodium',
        'chloride',
        'nitrogen',
        'nitrate',
        'phosphorus',
        'potassium',
        'iron',
        'zinc',
        'organic',
      ].includes(key)
        ? key
        : valuesText(item, depth + 1)
    )
    .join(' ')
}
function contains(text: string, phrase: string): boolean {
  const term = normalizeEvidenceText(phrase).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return new RegExp(`(^|[^\\p{L}\\p{N}_])${term}(?=$|[^\\p{L}\\p{N}_])`, 'u').test(text)
}
export function selectEvidence(context: unknown, limit = 6): ResearchRecord[] {
  const text = normalizeEvidenceText(valuesText(context))
  const scored = RESEARCH.records
    .map((record, index) => {
      const tagMatches = (record.tags ?? []).filter((word) => contains(text, word)).length
      const topicMatches = ((rules.topics as Record<string, string[]>)[record.topic] ?? []).filter(
        (word) => contains(text, word)
      ).length
      return {
        record,
        index,
        score: record.tags?.length && !tagMatches ? 0 : topicMatches + tagMatches * 3,
      }
    })
    .filter((entry) => entry.score > 0)
  scored.sort(
    (a, b) =>
      b.score - a.score ||
      (rules.kind_tiebreak[b.record.kind] ?? 0) - (rules.kind_tiebreak[a.record.kind] ?? 0) ||
      (b.record.year ?? 0) - (a.record.year ?? 0) ||
      a.index - b.index
  )
  // Retrieval heuristics, NOT a scientific quality score. Reserve applicable synthesis/guidance
  // within each matched topic so a novel narrow trial cannot automatically crowd it out.
  const chosen = new Set<string>()
  for (const { record } of scored) {
    if (chosen.has(record.id)) continue
    if (
      [...chosen].some((id) =>
        scored.some((s) => s.record.id === id && s.record.topic === record.topic)
      )
    )
      continue
    chosen.add(record.id)
    const sameTopic = scored.filter(
      (s) => s.record.topic === record.topic && s.record.id !== record.id
    )
    const second =
      (['review', 'extension'].includes(record.kind)
        ? sameTopic.find((s) => !['review', 'extension'].includes(s.record.kind))
        : sameTopic.find((s) => ['review', 'extension'].includes(s.record.kind))) ?? sameTopic[0]
    if (second) chosen.add(second.record.id)
  }
  return scored
    .filter((s) => chosen.has(s.record.id))
    .slice(0, Math.min(8, Math.max(0, limit)))
    .map((s) => s.record)
}
export function evidencePrompt(records: ResearchRecord[]) {
  return {
    catalog_version: RESEARCH.version,
    catalog_updated_at: RESEARCH.as_of,
    live_search: false,
    locally_validated: false,
    notice: SCIENCE_NOTICE,
    records: records.map(
      ({
        id,
        source_title,
        url,
        doi,
        year,
        region,
        kind,
        access,
        checked_at,
        finding,
        application,
        limitations,
        expert_reviewed,
      }) => ({
        id,
        source_title,
        url,
        doi,
        year,
        region,
        kind,
        access,
        checked_at,
        finding,
        application,
        limitations,
        expert_reviewed,
      })
    ),
  }
}
const entries = (value: unknown): string[] =>
  Array.isArray(value)
    ? value
        .filter(
          (v): v is string => typeof v === 'string' && v.trim().length > 0 && v.length <= 1000
        )
        .slice(0, 8)
    : []
export function buildScientificBasis(raw: unknown, supplied: ResearchRecord[]): ScientificBasis {
  const input = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {}
  const allowed = new Set(supplied.map((r) => r.id))
  const claims: DecisionReasoning['research_claims'] = []
  if (Array.isArray(input.research_claims))
    for (const candidate of input.research_claims.slice(0, 6)) {
      if (!candidate || typeof candidate !== 'object') continue
      const claim = candidate as Record<string, unknown>
      const source_ids = [
        ...new Set(
          entries(claim.source_ids)
            .slice(0, 4)
            .filter((id) => allowed.has(id))
        ),
      ]
      if (
        entries([claim.statement]).length &&
        entries([claim.application_limit]).length &&
        source_ids.length
      )
        claims.push({
          statement: claim.statement as string,
          application_limit: claim.application_limit as string,
          source_ids,
        })
    }
  const ids = [...new Set(claims.flatMap((claim) => claim.source_ids))]
  return {
    version: 1,
    catalog_version: RESEARCH.version,
    catalog_updated_at: RESEARCH.as_of,
    live_search: false,
    locally_validated: false,
    notice: SCIENCE_NOTICE,
    reasoning: {
      supporting_evidence: entries(input.supporting_evidence),
      alternatives: entries(input.alternatives),
      discriminating_checks: entries(input.discriminating_checks),
      missing_information: entries(input.missing_information),
      reassessment: entries(input.reassessment),
      referral_triggers: entries(input.referral_triggers),
      research_ids: ids,
      research_claims: claims,
    },
    sources: supplied.filter((r) => ids.includes(r.id)).map((r) => ({ ...r })),
    supplied_source_ids: [...allowed],
  }
}
/** Minimum explainability, not a scientific correctness test. Never silently bill an empty answer. */
export function hasDecisionReasoning(raw: unknown): boolean {
  if (!raw || typeof raw !== 'object') return false
  const input = raw as Record<string, unknown>
  if (
    !Array.isArray(input.research_claims) ||
    input.research_claims.length > 6 ||
    !Array.isArray(input.research_ids)
  )
    return false
  return [
    'supporting_evidence',
    'alternatives',
    'discriminating_checks',
    'missing_information',
    'reassessment',
    'referral_triggers',
  ].every((key) => entries(input[key]).length > 0)
}
export const REASONING_SCHEMA = decisionContract.reasoning_schema
export const DECISION_INSTRUCTIONS = decisionContract.instructions

/** Human-readable export: scientific provenance, never provider keys or internal model names. */
export function scientificBasisText(basis?: ScientificBasis): string {
  if (!basis) return 'پشتوانهٔ پژوهشی متصل برای این گزارش ثبت نشده است.'
  const reasoning = basis.reasoning
  return [
    SCIENCE_NOTICE,
    `نسخهٔ فهرست منابع: ${basis.catalog_version}؛ به‌روزرسانی فهرست: ${basis.catalog_updated_at}`,
    'شواهد پرونده:',
    ...reasoning.supporting_evidence,
    'احتمال‌های جایگزین:',
    ...reasoning.alternatives,
    'بررسی‌های تغییردهندهٔ تصمیم:',
    ...reasoning.discriminating_checks,
    'اطلاعات مفقود:',
    ...reasoning.missing_information,
    'معیار بازنگری:',
    ...reasoning.reassessment,
    'معیار ارجاع:',
    ...reasoning.referral_triggers,
    'ارتباط ادعا و منبع (تطابق معنایی خودکار تأیید نشده است):',
    ...(reasoning.research_claims ?? []).map(
      (c) => `${c.statement} [${c.source_ids.join('، ')}]؛ محدودیت این باغ: ${c.application_limit}`
    ),
    'منابع ارجاع‌شده (ارجاع، اثبات تشخیص نیست):',
    ...basis.sources.map(
      (s) =>
        `${s.source_title} (${s.published_label})\n${s.url}\nبررسی: ${s.checked_at}؛ دامنه: ${s.region}\nمحدودیت: ${s.limitations}`
    ),
  ].join('\n')
}
