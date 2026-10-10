import { useMemo, useState } from 'react'
import { Bookmark, BookOpen, Search, ShieldCheck, X } from 'lucide-react'
import type { AppContext } from '../types'
import { fa } from '../api'
import { Badge, EmptyState, InfoBanner, PageTitle } from '../components/ui'
import { ArticleCard } from './Dashboard'

export default function KnowledgePage({
  ctx,
  initialSearch = '',
}: {
  ctx: AppContext
  initialSearch?: string
}) {
  const [search, setSearch] = useState(initialSearch)
  const [category, setCategory] = useState('all')
  const [onlySaved, setOnlySaved] = useState(false)
  const storageKey = `pesteyar-bookmarks:${ctx.data.user?.id ?? 'guest'}`
  const [saved, setSaved] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(storageKey) ?? '[]') as string[]
    } catch {
      return []
    }
  })
  const normalize = (s: string) => s.replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/‌/g, ' ').trim()
  const articles = useMemo(
    () =>
      ctx.knowledge.articles.filter(
        (a) =>
          (category === 'all' || a.category === category) &&
          (!onlySaved || saved.includes(a.id)) &&
          normalize([a.title, a.keywords, a.summary].join(' ')).includes(normalize(search))
      ),
    [ctx.knowledge.articles, category, onlySaved, saved, search]
  )
  function toggle(id: string) {
    const next = saved.includes(id) ? saved.filter((s) => s !== id) : [...saved, id]
    setSaved(next)
    localStorage.setItem(storageKey, JSON.stringify(next))
    ctx.notify(next.includes(id) ? 'راهنما روی این دستگاه نشان‌گذاری شد.' : 'نشان راهنما حذف شد.')
  }
  return (
    <>
      <PageTitle
        eyebrow="دانش، ریشه یک باغ پربار"
        title="دانشنامه پسته"
        subtitle="از آفات و بیماری‌ها تا آب، تغذیه و برداشت؛ راهنماهای قابل پیگیری."
        action={
          <Badge tone="gray">
            <BookOpen size={14} />
            {fa(ctx.knowledge.articles.length)} راهنمای اولیه
          </Badge>
        }
      />
      <div className="knowledge-search-hero">
        <div className="knowledge-hero-icon">
          <BookOpen size={35} strokeWidth={1.5} />
        </div>
        <div>
          <h2>پاسخ را از شناخت بهتر شروع کن.</h2>
          <p>نام آفت، نشانه یا موضوعی مثل «زردی برگ» را جستجو کن.</p>
        </div>
        <label className="search-input">
          <Search size={19} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="جستجوی دانشنامه"
            placeholder="چه چیزی درباره پسته می‌خواهی بدانی؟"
          />
          {search && (
            <button
              className="icon-button"
              onClick={() => setSearch('')}
              aria-label="پاک کردن جستجو"
            >
              <X size={15} />
            </button>
          )}
        </label>
      </div>
      <div className="knowledge-filters">
        <div className="filter-pills">
          {ctx.knowledge.categories.map((c) => (
            <button
              key={c.id}
              className={category === c.id ? 'active' : ''}
              onClick={() => setCategory(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>
        <button
          className={`saved-filter ${onlySaved ? 'active' : ''}`}
          onClick={() => setOnlySaved(!onlySaved)}
        >
          <Bookmark size={16} />
          {onlySaved ? 'نمایش همه' : 'نشان‌شده‌ها'}
        </button>
      </div>
      <div className="knowledge-count">
        <span>
          {fa(articles.length)} مطلب{search && ` برای «${search}»`}
        </span>
        <span>
          <ShieldCheck size={14} />
          منابع و محدودیت‌ها در هر راهنما
        </span>
      </div>
      {articles.length ? (
        <div className="articles-grid knowledge-grid">
          {articles.map((a) => (
            <div className="bookmark-card" key={a.id}>
              <ArticleCard article={a} onClick={() => ctx.openArticle(a)} />
              <button
                className={`bookmark-button ${saved.includes(a.id) ? 'bookmarked' : ''}`}
                aria-label={`${saved.includes(a.id) ? 'حذف نشان' : 'نشان‌گذاری'} ${a.title}`}
                onClick={() => toggle(a.id)}
              >
                <Bookmark size={16} fill={saved.includes(a.id) ? 'currentColor' : 'none'} />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="card">
          <EmptyState
            icon={<Search size={28} />}
            title="راهنمایی پیدا نشد"
            text={
              onlySaved
                ? 'هنوز راهنمایی در این دسته نشان نکرده‌ای.'
                : 'واژه یا دسته دیگری را انتخاب کن.'
            }
            action={
              <button
                className="button secondary"
                onClick={() => {
                  setSearch('')
                  setCategory('all')
                  setOnlySaved(false)
                }}
              >
                نمایش همه راهنماها
              </button>
            }
          />
        </div>
      )}
      <InfoBanner tone="warning">
        {ctx.knowledge.notice} این مجموعه هنوز پوشش جامع همه آفات ایران نیست. تصاویر آموزشی
        تولیدشده‌اند و نمونه تشخیصی واقعی نیستند.
      </InfoBanner>
    </>
  )
}
