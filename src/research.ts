import data from './data/research.json'

export type EvidenceKind =
  | 'review'
  | 'primary'
  | 'field'
  | 'observational'
  | 'controlled'
  | 'prototype'
  | 'project'
  | 'extension'
  | 'news'
export interface ResearchRecord {
  id: string
  title: string
  topic: string
  year: number | null
  published_label: string
  kind: EvidenceKind
  region: string
  access: string
  source_title: string
  url: string
  search_id: number | null
  doi: string
  authors: string
  finding: string
  application: string
  limitations: string
  checked_at: string
  expert_reviewed: boolean
}
export const RESEARCH = data as {
  version: string
  as_of: string
  scope: string
  reviewed_by_local_expert: boolean
  records: ResearchRecord[]
}
export const EVIDENCE_LABELS: Record<EvidenceKind, string> = {
  review: 'مرور پژوهش‌ها',
  primary: 'مقاله پژوهشی',
  field: 'آزمون/ارزیابی باغی',
  observational: 'مطالعه مشاهده‌ای',
  controlled: 'آزمایش کنترل‌شده',
  prototype: 'نمونه فناوری / امکان‌سنجی',
  project: 'گزارش پروژه پژوهشی',
  extension: 'راهنمای ترویجی',
  news: 'خبر آزمون سازگاری',
}
export const ACCESS_LABELS: Record<string, string> = {
  'full-section': 'بخش‌های صفحه/متن در دسترس مرور شد',
  'publisher-abstract': 'چکیده ناشر مرور شد',
  'indexed-abstract': 'چکیده نمایه‌شده؛ نه متن کامل',
  'indexed-summary': 'خلاصه نمایه‌شده؛ دسترسی کامل تأیید نشد',
}
export function searchResearch(query: string, topic = 'all', recent = false) {
  const normal = (s: string) =>
    s.replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/‌/g, ' ').toLowerCase().trim()
  const tokens = normal(query).split(/\s+/).filter(Boolean)
  return RESEARCH.records.filter(
    (r) =>
      (topic === 'all' || r.topic === topic) &&
      (!recent || (r.year !== null && r.year >= 2024)) &&
      tokens.every((t) =>
        normal(
          [r.title, r.topic, r.region, r.finding, r.application, r.source_title].join(' ')
        ).includes(t)
      )
  )
}
