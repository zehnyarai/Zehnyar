import { useState } from 'react'
import { FileSearch, Plus, Search, SlidersHorizontal } from 'lucide-react'
import type { AppContext } from '../types'
import { fa } from '../api'
import { Badge, EmptyState, PageTitle } from '../components/ui'
import { ReportRow } from './Dashboard'

export default function Reports({ ctx }: { ctx: AppContext }) {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [orchard, setOrchard] = useState('all')
  const reports = ctx.data.reports.filter(
    (r) =>
      (filter === 'all' || r.data.urgency === filter) &&
      (orchard === 'all' || r.orchard_id === orchard) &&
      [r.data.title, r.orchard_name, r.tree_part, r.data.summary].join(' ').includes(search)
  )
  return (
    <>
      <PageTitle
        eyebrow="دفتر سلامت باغ"
        title="گزارش‌های بررسی"
        subtitle="مشاهدات و قدم‌های بعدی را در کنار هم دنبال کن."
        action={
          <button className="button primary" onClick={() => ctx.startAnalysis()}>
            <Plus size={17} />
            بررسی جدید
          </button>
        }
      />
      <div className="card reports-card">
        <div className="list-toolbar">
          <label className="search-input">
            <Search size={17} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="جستجو در گزارش‌ها…"
              aria-label="جستجوی گزارش"
            />
          </label>
          <select
            value={orchard}
            onChange={(e) => setOrchard(e.target.value)}
            aria-label="فیلتر باغ"
          >
            <option value="all">همه باغ‌ها</option>
            {ctx.data.orchards.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
          <span className="toolbar-count">
            <SlidersHorizontal size={15} />
            {fa(reports.length)} گزارش
          </span>
        </div>
        <div className="tabs">
          {[
            ['all', 'همه بررسی‌ها'],
            ['medium', 'نیازمند بررسی'],
            ['high', 'ارجاع فوری'],
            ['low', 'پیگیری معمول'],
          ].map(([id, label]) => (
            <button
              key={id}
              className={filter === id ? 'active' : ''}
              onClick={() => setFilter(id)}
            >
              {label}
              {filter === id && <Badge tone="gray">{fa(reports.length)}</Badge>}
            </button>
          ))}
        </div>
        <div className="report-table-labels">
          <span>درخت و باغ</span>
          <span>وضعیت پیگیری</span>
          <span>زمان بررسی</span>
        </div>
        {reports.length ? (
          reports.map((r) => <ReportRow key={r.id} report={r} onClick={() => ctx.openReport(r)} />)
        ) : (
          <EmptyState
            icon={<FileSearch size={30} />}
            title={
              ctx.data.reports.length ? 'گزارشی با این فیلتر پیدا نشد' : 'هنوز گزارشی ثبت نشده'
            }
            text="با تغییر فیلتر یا یک بررسی تازه شروع کن."
            action={
              <button className="button secondary" onClick={() => ctx.startAnalysis()}>
                بررسی تصویر
              </button>
            }
          />
        )}
      </div>
      <p className="privacy-inline">
        گزارش‌های نمونه صراحتاً مشخص‌اند. تصویر و گزارش واقعی فقط در حساب صاحب آن قابل مشاهده‌اند.
      </p>
    </>
  )
}
