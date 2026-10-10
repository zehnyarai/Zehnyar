import { IS_STANDALONE, assetUrl } from '../config'
import { useRef, useState } from 'react'
import {
  ArrowLeft,
  BookOpen,
  CalendarDays,
  Camera,
  Check,
  ChevronLeft,
  ClipboardList,
  CloudSun,
  FileSearch,
  Leaf,
  MapPin,
  Plus,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Sprout,
  Trees,
  Upload,
} from 'lucide-react'
import type { AppContext, Article, Report, Task } from '../types'
import { api, checkImage, dueLabel, errorMessage, fa, relativeDate, takePhoto, today } from '../api'
import { Badge, CardHeader, EmptyState, PageTitle } from '../components/ui'

export function ArticleCard({ article, onClick }: { article: Article; onClick: () => void }) {
  return (
    <button className="article-card" onClick={onClick}>
      <div className="article-image">
        <img src={article.image} alt="تصویر آموزشی پسته" loading="lazy" />
        <span className="article-category">{article.category_label}</span>
      </div>
      <div className="article-card-body">
        <h3>{article.title}</h3>
        <p>{article.summary}</p>
        <div className="article-meta">
          <span>
            <BookOpen size={13} />
            {fa(article.reading_minutes)} دقیقه مطالعه
          </span>
          <ArrowLeft size={16} />
        </div>
      </div>
    </button>
  )
}

export function ReportRow({ report, onClick }: { report: Report; onClick: () => void }) {
  const urgency = report.data.urgency
  const record = report.data.provider === 'local-storage'
  return (
    <button className="report-row" onClick={onClick}>
      <img src={report.image_url ?? assetUrl('/images/pistachio-leaves.jpg')} alt="تصویر گزارش" />
      <div className="report-row-title">
        <strong>{report.data.title}</strong>
        <span>
          {report.orchard_name ?? 'بدون باغ مشخص'}
          {report.is_sample ? ' · نمونه نمایشی' : ''}
        </span>
      </div>
      <Badge
        tone={
          record ? 'gray' : urgency === 'high' ? 'red' : urgency === 'medium' ? 'amber' : 'green'
        }
      >
        {record
          ? 'ثبت عکس · بدون تحلیل'
          : urgency === 'high'
            ? 'ارجاع فوری'
            : urgency === 'medium'
              ? 'نیازمند بررسی'
              : 'پیگیری معمول'}
      </Badge>
      <span className="report-date">{relativeDate(report.created_at)}</span>
      <ChevronLeft className="row-arrow" size={16} />
    </button>
  )
}

export function TaskRow({ task, ctx }: { task: Task; ctx: AppContext }) {
  const [busy, setBusy] = useState(false)
  async function toggle() {
    if (busy) return
    setBusy(true)
    try {
      await api(`/tasks/${task.id}`, { method: 'PUT', body: JSON.stringify({ done: !task.done }) })
      await ctx.refresh()
    } catch (e) {
      ctx.notify(errorMessage(e), 'error')
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className={`task-row ${task.done ? 'task-completed' : ''}`}>
      <button
        className="task-check"
        aria-label={`${task.done ? 'بازگرداندن' : 'انجام'} ${task.title}`}
        onClick={toggle}
        disabled={busy}
      >
        {!!task.done && <Check size={13} />}
      </button>
      <div className="task-content">
        <strong>{task.title}</strong>
        <span>{task.orchard_name ?? 'همه باغ‌ها'}</span>
      </div>
      <span className={`due-label ${task.due_date === today() && !task.done ? 'due-today' : ''}`}>
        {task.done ? 'انجام شد' : dueLabel(task.due_date)}
      </span>
    </div>
  )
}

export default function Dashboard({ ctx }: { ctx: AppContext }) {
  const [orchardFilter, setOrchardFilter] = useState('all')
  const [dragging, setDragging] = useState(false)
  const upload = useRef<HTMLInputElement>(null)
  const camera = useRef<HTMLInputElement>(null)
  const { data, knowledge } = ctx
  const orchards = data.orchards.filter((o) => orchardFilter === 'all' || o.id === orchardFilter)
  const reports = data.reports.filter(
    (r) => orchardFilter === 'all' || r.orchard_id === orchardFilter
  )
  const tasks = data.tasks.filter((t) => orchardFilter === 'all' || t.orchard_id === orchardFilter)
  const pending = tasks.filter((t) => !t.done)
  function accept(file?: File) {
    if (!file) return
    const error = checkImage(file)
    if (error) ctx.notify(error, 'error')
    else ctx.startAnalysis(file, orchardFilter === 'all' ? undefined : orchardFilter)
  }
  const articles = knowledge.articles.filter((a) =>
    ['psylla', 'irrigation', 'harvest'].includes(a.id)
  )
  const stats = [
    {
      label: 'باغ‌های من',
      value: orchards.length,
      detail: 'باغ ثبت‌شده در پستینو',
      icon: Trees,
      page: 'orchards' as const,
      className: 'sage',
    },
    {
      label: 'درختان ثبت‌شده',
      value: orchards.reduce((n, o) => n + o.trees, 0),
      detail: 'بر اساس اطلاعات باغ‌ها',
      icon: Sprout,
      page: 'orchards' as const,
      className: 'olive',
    },
    {
      label: IS_STANDALONE ? 'عکس‌های ثبت‌شده' : 'گزارش‌های بررسی',
      value: reports.length,
      detail: IS_STANDALONE
        ? 'عکس و یادداشت محلی، بدون تحلیل'
        : data.user?.is_demo
          ? 'شامل گزارش‌های نمونه'
          : 'بررسی‌های ذخیره‌شده شما',
      icon: FileSearch,
      page: 'reports' as const,
      className: 'sand',
    },
    {
      label: 'کارهای پیش‌رو',
      value: pending.length,
      detail: `${fa(pending.filter((t) => t.due_date === today()).length)} یادآور برای امروز`,
      icon: CalendarDays,
      page: 'calendar' as const,
      className: 'blue',
    },
  ]
  return (
    <>
      <PageTitle
        eyebrow="یک روز تازه، یک فرصت تازه"
        title="باغ سالم، خیال آسوده"
        subtitle="وضعیت باغت را ببین و قدم بعدی را آگاهانه بردار."
        action={
          <>
            <select
              className="orchard-filter"
              aria-label="انتخاب باغ"
              value={orchardFilter}
              onChange={(e) => setOrchardFilter(e.target.value)}
            >
              <option value="all">همه باغ‌های من</option>
              {data.orchards.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
            <button className="button primary" onClick={() => ctx.startAnalysis()}>
              <Plus size={17} />
              {IS_STANDALONE ? 'ثبت عکس جدید' : 'تحلیل جدید'}
            </button>
          </>
        }
      />
      <div className="hero-grid">
        <section className="orchard-hero">
          <img
            src={assetUrl('/images/pistachio-orchard.jpg')}
            alt="باغ پسته در نور صبح"
            className="hero-photo"
            fetchPriority="high"
          />
          <div className="hero-shade" />
          <div className="hero-copy">
            <span className="hero-eyebrow">
              <span className="tiny-sparkle">
                <Sparkles size={13} />
              </span>
              از ریشه تا برداشت، کنار شماییم
            </span>
            <h2>
              آینده‌ی باغت،
              <br />
              <span>از امروز سبزتر است.</span>
            </h2>
            <p>
              شناخت بهتر درخت‌ها، مراقبت به‌موقع و تصمیم‌های
              <br className="desktop-br" /> مطمئن‌تر؛ همه در یک همراه هوشمند.
            </p>
            <button className="button hero-button" onClick={() => ctx.navigate('orchards')}>
              به باغ‌های من برو
              <ArrowLeft size={16} />
            </button>
          </div>
          <span className="hero-caption">
            <MapPin size={13} />
            همراه باغداران ایران
          </span>
        </section>
        <section
          className={`quick-analysis ${dragging ? 'is-dragging' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault()
            setDragging(false)
            accept(e.dataTransfer.files[0])
          }}
        >
          <div className="quick-card-heading">
            <div className="quick-icon">
              <ScanLine size={21} />
            </div>
            <div>
              <h2>درختت چی می‌گه؟</h2>
              <p>
                {IS_STANDALONE
                  ? 'عکس و یادداشت را روی گوشی نگه دار.'
                  : 'با یک عکس، بررسی را شروع کن.'}
              </p>
            </div>
            <Badge tone="gray">{IS_STANDALONE ? 'ثبت محلی' : 'هوشمند'}</Badge>
          </div>
          <button className="quick-dropzone" onClick={() => upload.current?.click()}>
            <div className="scan-illustration">
              <span className="scan-corner c1" />
              <span className="scan-corner c2" />
              <span className="scan-corner c3" />
              <span className="scan-corner c4" />
              <Leaf size={31} strokeWidth={1.5} />
              <span className="scan-line" />
            </div>
            <strong>عکس درخت را اینجا رها کن</strong>
            <span>برگ، میوه، شاخه یا کل درخت · تا ۸ مگابایت</span>
          </button>
          <div className="quick-actions">
            <button className="button primary" onClick={() => upload.current?.click()}>
              <Upload size={15} />
              بارگذاری عکس
            </button>
            <button
              className="button secondary"
              onClick={() => {
                void takePhoto(() => camera.current?.click(), accept).catch(() =>
                  ctx.notify('عکس دریافت نشد. می‌توانید از گالری انتخاب کنید.', 'info')
                )
              }}
            >
              <Camera size={16} />
              گرفتن عکس
            </button>
          </div>
          <input
            ref={upload}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            onChange={(e) => {
              accept(e.target.files?.[0])
              e.target.value = ''
            }}
          />
          <input
            ref={camera}
            type="file"
            accept="image/*"
            capture="environment"
            hidden
            onChange={(e) => {
              accept(e.target.files?.[0])
              e.target.value = ''
            }}
          />
          <div className="analysis-footnote">
            <ShieldCheck size={13} />
            {IS_STANDALONE
              ? 'عکس ثبت می‌شود؛ تشخیص خودکار انجام نمی‌شود'
              : data.services.vision_configured
                ? 'بررسی اولیه؛ جایگزین تشخیص کارشناس نیست'
                : 'حالت آزمایشی · سرویس تحلیل هنوز متصل نیست'}
          </div>
        </section>
      </div>
      <div className="stats-grid">
        {stats.map((stat) => (
          <button className="stat-card" key={stat.label} onClick={() => ctx.navigate(stat.page)}>
            <div className="stat-top">
              <span>{stat.label}</span>
              <span className={`stat-icon ${stat.className}`}>
                <stat.icon size={20} strokeWidth={1.8} />
              </span>
            </div>
            <strong>{fa(stat.value)}</strong>
            <p>
              <span className="stat-dot" />
              {stat.detail}
            </p>
          </button>
        ))}
      </div>
      <div className="dashboard-panels">
        <section className="card recent-reports">
          <CardHeader
            title={IS_STANDALONE ? 'آخرین عکس‌ها و یادداشت‌ها' : 'آخرین بررسی‌های درختان'}
            subtitle="از مشاهده تا اقدام، یک مسیر روشن"
            action="همه گزارش‌ها"
            onClick={() => ctx.navigate('reports')}
          />
          <div className="report-table-labels">
            <span>درخت و باغ</span>
            <span>وضعیت پیگیری</span>
            <span>زمان بررسی</span>
          </div>
          {reports.length ? (
            reports
              .slice(0, 3)
              .map((r) => <ReportRow key={r.id} report={r} onClick={() => ctx.openReport(r)} />)
          ) : (
            <EmptyState
              icon={<FileSearch size={26} />}
              title="هنوز گزارشی نداری"
              text="اولین بررسی را با یک عکس شروع کن."
              action={
                <button className="text-button" onClick={() => ctx.startAnalysis()}>
                  {IS_STANDALONE ? 'ثبت عکس' : 'بررسی تصویر'}
                  <ArrowLeft size={14} />
                </button>
              }
            />
          )}
          <div className="report-card-footer">
            <ShieldCheck size={13} />
            تشخیص قطعی بیماری و کمبود، ممکن است به آزمایش نیاز داشته باشد.
          </div>
        </section>
        <section className="card care-plan">
          <CardHeader
            title="برنامه مراقبت باغ"
            action="تقویم"
            onClick={() => ctx.navigate('calendar')}
          />
          {pending.length ? (
            pending.slice(0, 3).map((t) => <TaskRow key={t.id} task={t} ctx={ctx} />)
          ) : (
            <EmptyState
              icon={<ClipboardList size={24} />}
              title="کارهای امروز انجام شده"
              text="برای مراقبت بعدی یک یادآور بساز."
            />
          )}
          <button className="add-task-button" onClick={ctx.openTask}>
            <Plus size={15} />
            افزودن یادآور
          </button>
        </section>
      </div>
      <section className="seasonal-tip">
        <div className="seasonal-icon">
          <CloudSun size={26} strokeWidth={1.6} />
        </div>
        <div>
          <span>یک نکته برای مراقبت آگاهانه</span>
          <h3>زردی برگ همیشه به معنی کمبود کود نیست.</h3>
          <p>قبل از تصمیم، وضعیت آب، خاک و ریشه را هم بررسی کن.</p>
        </div>
        <button
          className="text-button"
          onClick={() => {
            const a = knowledge.articles.find((a) => a.id === 'nutrition')
            if (a) ctx.openArticle(a)
          }}
        >
          راهنمای تغذیه
          <ArrowLeft size={15} />
        </button>
      </section>
      <section className="dashboard-knowledge">
        <CardHeader
          title="دانش کوچک، تفاوت بزرگ"
          subtitle="چند راهنما برای تصمیم‌های بهتر در باغ"
          action="ورود به دانشنامه"
          onClick={() => ctx.navigate('knowledge')}
        />
        <div className="articles-grid">
          {articles.map((a) => (
            <ArticleCard article={a} key={a.id} onClick={() => ctx.openArticle(a)} />
          ))}
        </div>
      </section>
    </>
  )
}
