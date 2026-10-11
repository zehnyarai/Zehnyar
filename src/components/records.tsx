import { assetUrl } from '../config'
import { useState } from 'react'
import { ArrowLeft, BookOpen, Check, ChevronLeft } from 'lucide-react'
import type { AppContext, Article, Report, Task } from '../types'
import { api, dueLabel, errorMessage, fa, relativeDate, today } from '../api'
import { Badge } from './ui'
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
  const record = ['local-storage', 'photo-storage'].includes(report.data.provider)
  const identified = report.data.is_pistachio === true
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
          record || !identified
            ? 'gray'
            : urgency === 'high'
              ? 'red'
              : urgency === 'medium'
                ? 'amber'
                : 'green'
        }
      >
        {record
          ? 'ثبت عکس · بدون تحلیل'
          : !identified
            ? 'بررسی شناسایی'
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
