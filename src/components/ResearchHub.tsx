import { useState } from 'react'
import { BookOpen, Download, ExternalLink, FlaskConical, Search } from 'lucide-react'
import { downloadText, errorMessage, fa, persianDate } from '../api'
import { ACCESS_LABELS, EVIDENCE_LABELS, RESEARCH, searchResearch } from '../research'
import type { AppContext } from '../types'
import { Badge, EmptyState, InfoBanner } from './ui'

export default function ResearchHub({ ctx }: { ctx: AppContext }) {
  const [query, setQuery] = useState(''),
    [topic, setTopic] = useState('all'),
    [recent, setRecent] = useState(false)
  const rows = searchResearch(query, topic, recent)
  const topics = [...new Set(RESEARCH.records.map((r) => r.topic))]
  async function exportReport() {
    const text = [
      'پستینو — نقشه پژوهش پسته',
      `مرور: ${RESEARCH.as_of} · نسخه: ${RESEARCH.version}`,
      RESEARCH.scope,
      'خلاصه‌ها تأیید کارشناس محلی یا نسخه سم/کود نیستند.',
      ...rows.map((r) =>
        [
          r.title,
          `${r.published_label} · ${EVIDENCE_LABELS[r.kind]} · ${r.region}`,
          r.source_title,
          r.authors,
          r.doi && `DOI: ${r.doi}`,
          r.url,
          `یافته: ${r.finding}`,
          `کاربرد محتاطانه: ${r.application}`,
          `حدود: ${r.limitations}`,
          `دسترسی: ${ACCESS_LABELS[r.access]}`,
          `مرور منبع: ${r.checked_at}`,
        ]
          .filter(Boolean)
          .join('\n')
      ),
    ].join('\n\n')
    try {
      await downloadText(`pestino-research-${RESEARCH.as_of}.txt`, text)
    } catch (e) {
      ctx.notify(errorMessage(e), 'error')
    }
  }
  return (
    <section className="research-hub" aria-label="پژوهش و نوآوری پسته">
      <div className="research-intro reference-card">
        <div>
          <FlaskConical size={29} />
          <h2>پژوهش و نوآوری پسته</h2>
        </div>
        <p>یافته‌ها، فناوری‌ها و محدودیت شواهد — برای تصمیم باغ، نه ادعای تأیید علمی اپ.</p>
        <div className="research-summary">
          <Badge tone="gray">{fa(RESEARCH.records.length)} رکورد منبع‌دار</Badge>
          <Badge tone="gray">مرور {persianDate(RESEARCH.as_of, { year: 'numeric' })}</Badge>
          <button className="button secondary small" onClick={() => void exportReport()}>
            <Download size={16} /> دریافت فهرست پژوهش‌ها
          </button>
        </div>
      </div>
      <InfoBanner tone="warning">
        {RESEARCH.scope}. چکیده، خبر، گزارش پروژه و مقاله پژوهشی هم‌ارز نیستند. تاریخ مرور با تاریخ
        انتشار فرق دارد؛ یافته خارجی یا آزمایش دانهال، نسخه عمومی برای باغ ایران نیست. این فهرست
        پایگاه داده تشخیص عکس یا به‌روزرسانی زنده نیست.
      </InfoBanner>
      <div className="research-search reference-card">
        <label className="search-input">
          <Search size={19} />
          <input
            aria-label="جستجوی پژوهش پسته"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="شوری، پایه، برداشت، حسگر، آفلاتوکسین…"
          />
        </label>
        <label>
          موضوع پژوهش
          <select aria-label="موضوع پژوهش" value={topic} onChange={(e) => setTopic(e.target.value)}>
            <option value="all">همه موضوع‌ها</option>
            {topics.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </label>
        <label className="consent-check">
          <input type="checkbox" checked={recent} onChange={(e) => setRecent(e.target.checked)} />
          <span>فقط منابع با سال انتشار ۲۰۲۴ تا ۲۰۲۶</span>
        </label>
      </div>
      <p className="section-description">
        {fa(rows.length)} رکورد؛ «تازه‌تر» الزاماً «قابل اجرای فوری» نیست. برای نسخه اجرایی،
        رقم/پایه، اقلیم، نمونه آزمایش و تأیید متخصص لازم‌اند.
      </p>
      <div className="research-grid">
        {rows.map((r) => (
          <article className="reference-card research-card" key={r.id}>
            <div className="research-card-badges">
              <Badge tone={r.kind === 'news' || r.kind === 'project' ? 'amber' : 'gray'}>
                {EVIDENCE_LABELS[r.kind]}
              </Badge>
              <Badge tone="gray">{r.published_label}</Badge>
            </div>
            <small>
              {r.topic} · {r.region}
            </small>
            <h3>{r.title}</h3>
            <p>{r.finding}</p>
            <details>
              <summary>کاربرد در باغ، حدود شواهد و منبع</summary>
              <h4>کاربرد محتاطانه در پستینو</h4>
              <p>{r.application}</p>
              <h4>چرا نباید بیش از شواهد نتیجه گرفت؟</h4>
              <p>{r.limitations}</p>
              <p className="research-citation">
                <BookOpen size={17} />
                {r.source_title}
                {r.authors && <> — {r.authors}</>}
              </p>
              {r.doi && <p dir="ltr">DOI: {r.doi}</p>}
              <p>
                {ACCESS_LABELS[r.access]} · مرور {persianDate(r.checked_at, { year: 'numeric' })}
              </p>
              <a href={r.url} target="_blank" rel="noreferrer" className="text-button">
                <ExternalLink size={15} />
                {r.search_id !== null ? `[${r.search_id}]` : 'منبع رسمی'} مشاهده منبع اصلی
              </a>
              <p className="section-description">
                خلاصه توسط ابزار هوشمند گردآوری شده؛ تأیید متخصص محلی انجام نشده است. منبع خارجی جای
                مقررات مصرف ایران را نمی‌گیرد.
              </p>
            </details>
          </article>
        ))}
      </div>
      {!rows.length && (
        <EmptyState
          icon={<Search size={26} />}
          title="پژوهشی با این جستجو در فهرست نیست"
          text="این نتیجه نبودن پژوهش در جهان را نشان نمی‌دهد؛ فقط محدوده فهرست فعلی است."
        />
      )}
    </section>
  )
}
