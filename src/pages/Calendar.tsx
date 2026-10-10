import { useState } from 'react'
import { CalendarDays, Check, ChevronLeft, ChevronRight, Plus, Trash2 } from 'lucide-react'
import type { AppContext } from '../types'
import { api, errorMessage, fa, persianDate, today } from '../api'
import { Badge, EmptyState, PageTitle } from '../components/ui'
import { TaskRow } from './Dashboard'

function shifted(day: string, delta: number) {
  const date = new Date(day + 'T12:00:00Z')
  date.setUTCDate(date.getUTCDate() + delta)
  return date.toISOString().slice(0, 10)
}
export default function CalendarPage({ ctx }: { ctx: AppContext }) {
  const [week, setWeek] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [showDone, setShowDone] = useState(false)
  const [orchard, setOrchard] = useState('all')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const start = shifted(
    today(),
    (-(new Date(today() + 'T12:00:00Z').getUTCDay() + 1) % 7) + week * 7
  )
  const days = Array.from({ length: 7 }, (_, i) => shifted(start, i))
  const tasks = ctx.data.tasks.filter(
    (t) =>
      (showDone || !t.done) &&
      (orchard === 'all' || t.orchard_id === orchard) &&
      (!selected || t.due_date === selected)
  )
  async function remove() {
    if (!deleteId) return
    setBusy(true)
    try {
      await api(`/tasks/${deleteId}`, { method: 'DELETE' })
      await ctx.refresh()
      setDeleteId(null)
      ctx.notify('یادآور حذف شد.')
    } catch (e) {
      ctx.notify(errorMessage(e), 'error')
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="مراقبت به‌موقع، رشد ماندگار"
        title="تقویم مراقبت"
        subtitle="بازدید، آزمایش و کارهای باغ را به یاد بسپار."
        action={
          <button className="button primary" onClick={ctx.openTask}>
            <Plus size={17} />
            یادآور جدید
          </button>
        }
      />
      <div className="card calendar-week">
        <header>
          <div>
            <CalendarDays size={20} />
            <h2>{persianDate(start, { month: 'long', year: 'numeric', day: undefined })}</h2>
          </div>
          <div>
            <button
              className="icon-button"
              onClick={() => {
                setWeek(week - 1)
                setSelected(null)
              }}
              aria-label="هفته قبل"
            >
              <ChevronRight size={19} />
            </button>
            <button
              className="button secondary small"
              onClick={() => {
                setWeek(0)
                setSelected(today())
              }}
            >
              امروز
            </button>
            <button
              className="icon-button"
              onClick={() => {
                setWeek(week + 1)
                setSelected(null)
              }}
              aria-label="هفته بعد"
            >
              <ChevronLeft size={19} />
            </button>
          </div>
        </header>
        <div className="week-days">
          {days.map((d) => (
            <button
              key={d}
              className={`${d === today() ? 'today' : ''} ${selected === d ? 'selected' : ''}`}
              onClick={() => setSelected(selected === d ? null : d)}
            >
              <span>{persianDate(d, { weekday: 'short', day: undefined, month: undefined })}</span>
              <strong>{persianDate(d, { month: undefined, day: 'numeric' })}</strong>
              <div className="calendar-dots">
                {ctx.data.tasks
                  .filter((t) => t.due_date === d && !t.done)
                  .slice(0, 3)
                  .map((t) => (
                    <span key={t.id} />
                  ))}
              </div>
            </button>
          ))}
        </div>
      </div>
      <div className="card calendar-list">
        <div className="list-toolbar">
          <h2>
            {selected ? `کارهای ${persianDate(selected)}` : 'همه یادآورها'}
            <Badge tone="gray">{fa(tasks.length)}</Badge>
          </h2>
          <select
            value={orchard}
            onChange={(e) => setOrchard(e.target.value)}
            aria-label="انتخاب باغ در تقویم"
          >
            <option value="all">همه باغ‌ها</option>
            {ctx.data.orchards.map((o) => (
              <option value={o.id} key={o.id}>
                {o.name}
              </option>
            ))}
          </select>
          <button
            className={`button secondary small ${showDone ? 'selected-button' : ''}`}
            onClick={() => setShowDone(!showDone)}
          >
            <Check size={14} />
            {showDone ? 'فقط کارهای پیش‌رو' : 'نمایش انجام‌شده‌ها'}
          </button>
          {selected && (
            <button className="text-button" onClick={() => setSelected(null)}>
              همه روزها
            </button>
          )}
        </div>
        {tasks.length ? (
          tasks.map((t) => (
            <div className="calendar-task-row" key={t.id}>
              <TaskRow task={t} ctx={ctx} />
              <button
                className="icon-button delete-button"
                aria-label={`حذف ${t.title}`}
                onClick={() => setDeleteId(t.id)}
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))
        ) : (
          <EmptyState
            icon={<CalendarDays size={28} />}
            title="کاری در این بخش نداری"
            text="با یک یادآور کوچک، مراقبت بعدی را برنامه‌ریزی کن."
            action={
              <button className="button secondary" onClick={ctx.openTask}>
                <Plus size={15} />
                افزودن یادآور
              </button>
            }
          />
        )}
      </div>
      <p className="privacy-inline">
        یادآورها داخل اپ نمایش داده می‌شوند. ارسال پیامک یا اعلان بیرونی در این نسخه فعال نیست.
      </p>
      {deleteId && (
        <div className="inline-confirm card">
          <span>این یادآور حذف شود؟</span>
          <button
            className="button danger small"
            onClick={() => {
              void remove()
            }}
            disabled={busy}
          >
            بله، حذف کن
          </button>
          <button className="button secondary small" onClick={() => setDeleteId(null)}>
            انصراف
          </button>
        </div>
      )}
    </>
  )
}
