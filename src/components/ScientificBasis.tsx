import { BookOpen, ExternalLink } from 'lucide-react'
import type { ScientificBasis as Basis } from '../evidence'
import { SCIENCE_NOTICE } from '../evidence'
import { RESEARCH, ACCESS_LABELS, EVIDENCE_LABELS } from '../research'
import { fa, persianDate } from '../api'
import { CheckList } from './ui'

const SECTIONS = [
  ['supporting_evidence', 'دلیل این برداشت از شواهد پرونده'],
  ['alternatives', 'احتمال‌های جایگزین و شواهد مخالف'],
  ['discriminating_checks', 'چه بررسی‌ای تصمیم را تغییر می‌دهد؟'],
  ['missing_information', 'اطلاعات ضروریِ مفقود'],
  ['reassessment', 'معیار پیگیری و بازنگری'],
  ['referral_triggers', 'چه زمانی به کارشناس ارجاع دهیم؟'],
] as const

/** Progressive disclosure: the short answer stays short, provenance is one tap away. */
const safeDate = (value: unknown) =>
  typeof value === 'string' &&
  /^\d{4}-\d{2}-\d{2}$/.test(value) &&
  Number.isFinite(Date.parse(value))
    ? persianDate(value, { year: 'numeric' })
    : 'نامشخص'

export default function ScientificBasis({ basis }: { basis?: Basis }) {
  if (!basis || typeof basis !== 'object')
    return (
      <p className="muted">
        برای این گزارش، پشتوانهٔ پژوهشی متصل و قابل‌پیگیری ثبت نشده؛ جدیدترین یافته‌ها برای آن تأیید
        نشده‌اند.
      </p>
    )
  // Backups are user-supplied. Never turn a forged source URL into a clickable link.
  const sources = Array.isArray(basis.sources)
    ? basis.sources.filter(
        (source) =>
          source &&
          [
            'source_title',
            'url',
            'published_label',
            'region',
            'finding',
            'limitations',
            'checked_at',
          ].every(
            (key) => typeof (source as unknown as Record<string, unknown>)[key] === 'string'
          ) &&
          RESEARCH.records.some((r) => r.id === source.id && r.url === source.url)
      )
    : []
  return (
    <details className="scientific-basis quiet-details">
      <summary>
        <BookOpen size={17} /> منطق بررسی و پشتوانهٔ علمی ({fa(sources.length)} منبع ارجاع‌شده)
      </summary>
      <p className="muted">{SCIENCE_NOTICE}</p>
      <p className="muted">
        نسخهٔ منابع این گزارش:{' '}
        <bdi>{typeof basis.catalog_version === 'string' ? basis.catalog_version : 'نامشخص'}</bdi> ·
        آخرین به‌روزرسانی فهرست: {safeDate(basis.catalog_updated_at)}؛ تاریخ بررسی هر منبع جداست.
      </p>
      {SECTIONS.map(([key, title]) => {
        const items = basis.reasoning?.[key]
        return Array.isArray(items) && items.length > 0 ? (
          <section key={key}>
            <h4>{title}</h4>
            <CheckList items={items.filter((v) => typeof v === 'string')} />
          </section>
        ) : null
      })}
      {Array.isArray(basis.reasoning?.research_claims) &&
        basis.reasoning.research_claims.length > 0 && (
          <section>
            <h4>ارتباط یافتهٔ پژوهشی با این پرونده</h4>
            <p className="muted">
              این ارتباط برای بررسی شما ارائه شده؛ تطابق معنایی ادعا و مقاله یا درستی تشخیص به‌طور
              مستقل تأیید نشده است.
            </p>
            {basis.reasoning.research_claims
              .filter(
                (claim) =>
                  claim &&
                  typeof claim.statement === 'string' &&
                  typeof claim.application_limit === 'string' &&
                  Array.isArray(claim.source_ids)
              )
              .map((claim, index) => (
                <article className="evidence-source" key={index}>
                  <p>{claim.statement}</p>
                  <p>
                    <strong>حد کاربرد در این باغ: </strong>
                    {claim.application_limit}
                  </p>
                  <small>
                    منابع:{' '}
                    {sources
                      .filter((s) => claim.source_ids.includes(s.id))
                      .map((s) => s.source_title)
                      .join('؛ ') || 'ارجاع معتبر ثبت نشده'}
                  </small>
                </article>
              ))}
          </section>
        )}
      <h4>منابع ارجاع‌شده در بررسی</h4>
      {!sources.length && (
        <p>
          برای این پاسخ، ارجاع قابل‌پیگیری به منبع ارائه نشده است. این خلأ شواهد است، نه اثبات نبود
          پژوهش در جهان.
        </p>
      )}
      {sources.map((source) => (
        <article className="evidence-source" key={source.id}>
          <a href={source.url} target="_blank" rel="noreferrer">
            {source.source_title} <ExternalLink size={14} />
          </a>
          <p>
            {source.published_label} · {EVIDENCE_LABELS[source.kind]} · {source.region}
          </p>
          <small>
            {ACCESS_LABELS[source.access] ?? 'دامنهٔ دسترسی نامشخص'} · بررسی بخش‌های در دسترس:{' '}
            {safeDate(source.checked_at)}
          </small>
          <p>
            <strong>یافتهٔ گزارش‌شده: </strong>
            {source.finding}
          </p>
          <p>
            <strong>محدودیت کاربرد: </strong>
            {source.limitations}
          </p>
          <small>ارجاع به این مقاله، تأیید تشخیص این باغ یا تأیید کارشناس محلی نیست.</small>
        </article>
      ))}
    </details>
  )
}
