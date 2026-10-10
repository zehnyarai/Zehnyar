import { useState } from 'react'
import {
  ArrowLeft,
  Droplets,
  Leaf,
  MapPin,
  Pencil,
  Plus,
  Search,
  Sprout,
  Trees,
} from 'lucide-react'
import type { AppContext, Orchard } from '../types'
import { fa } from '../api'
import { Badge, EmptyState, Modal, PageTitle } from '../components/ui'

export default function Orchards({ ctx }: { ctx: AppContext }) {
  const [search, setSearch] = useState('')
  const [detail, setDetail] = useState<Orchard | null>(null)
  const orchards = ctx.data.orchards.filter((o) =>
    [o.name, o.city, o.cultivar, o.province].join(' ').includes(search)
  )
  return (
    <>
      <PageTitle
        eyebrow="ریشه‌های سبز شما"
        title="باغ‌های من"
        subtitle="اطلاعات هر باغ، پایه یک مراقبت دقیق‌تر است."
        action={
          <button className="button primary" onClick={() => ctx.openOrchard()}>
            <Plus size={17} />
            ثبت باغ جدید
          </button>
        }
      />
      <div className="orchard-summary-strip">
        <Trees size={22} />
        <span>
          <strong>{fa(ctx.data.orchards.length)}</strong> باغ
        </span>
        <div />
        <span>
          <strong>{fa(ctx.data.orchards.reduce((n, o) => n + o.area, 0))}</strong> هکتار
        </span>
        <div />
        <span>
          <strong>{fa(ctx.data.orchards.reduce((n, o) => n + o.trees, 0))}</strong> درخت
        </span>
        <label className="search-input">
          <Search size={16} />
          <input
            placeholder="جستجوی نام باغ، شهر یا رقم…"
            aria-label="جستجوی باغ"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>
      <div className="orchards-grid">
        {orchards.map((o, i) => (
          <article className="orchard-card card" key={o.id}>
            <div className={`orchard-cover cover-${i % 2}`}>
              <img src="/images/pistachio-orchard.jpg" alt="تصویر آموزشی باغ پسته" />
              <div className="orchard-cover-shade" />
              <div className="orchard-cover-top">
                <Badge tone="gray">{o.is_sample ? 'باغ نمونه' : 'ثبت‌شده توسط شما'}</Badge>
                <button
                  className="icon-button"
                  aria-label={`ویرایش ${o.name}`}
                  onClick={() => ctx.openOrchard(o)}
                >
                  <Pencil size={16} />
                </button>
              </div>
              <div className="orchard-cover-name">
                <h2>{o.name}</h2>
                <span>
                  <MapPin size={14} />
                  {o.province}، {o.city}
                </span>
              </div>
            </div>
            <div className="orchard-info-grid">
              <div>
                <Trees size={17} />
                <span>تعداد درخت</span>
                <strong>{fa(o.trees)} درخت</strong>
              </div>
              <div>
                <Sprout size={17} />
                <span>مساحت باغ</span>
                <strong>{fa(o.area)} هکتار</strong>
              </div>
              <div>
                <Leaf size={17} />
                <span>رقم پسته</span>
                <strong>{o.cultivar}</strong>
              </div>
              <div>
                <Droplets size={17} />
                <span>نوع آبیاری</span>
                <strong>{o.irrigation}</strong>
              </div>
            </div>
            <div className="orchard-card-footer">
              <button className="text-button" onClick={() => setDetail(o)}>
                جزئیات باغ
                <ArrowLeft size={15} />
              </button>
              <button
                className="button secondary small"
                onClick={() => ctx.startAnalysis(undefined, o.id)}
              >
                بررسی درخت
              </button>
            </div>
          </article>
        ))}
      </div>
      {!orchards.length && (
        <div className="card">
          <EmptyState
            icon={<Trees size={32} />}
            title={search ? 'باغی پیدا نشد' : 'اولین باغت را ثبت کن'}
            text={
              search
                ? 'نام، شهر یا رقم دیگری را جستجو کن.'
                : 'از نام باغ، موقعیت و رقم درخت‌ها شروع کن.'
            }
            action={
              !search && (
                <button className="button primary" onClick={() => ctx.openOrchard()}>
                  <Plus size={16} />
                  ثبت باغ
                </button>
              )
            }
          />
        </div>
      )}
      <div className="privacy-inline">
        <MapPin size={16} />
        فقط شهر و استان ثبت می‌شود؛ دریافت موقعیت دقیق GPS در این نسخه فعال نیست.
      </div>
      {detail && (
        <Modal
          title={detail.name}
          subtitle={`${detail.province}، ${detail.city}${detail.is_sample ? ' · اطلاعات نمونه' : ''}`}
          onClose={() => setDetail(null)}
        >
          <div className="detail-facts">
            {[
              ['رقم', detail.cultivar],
              ['سن درختان', `${fa(detail.age)} سال`],
              ['تعداد درخت', fa(detail.trees)],
              ['مساحت', `${fa(detail.area)} هکتار`],
              ['آبیاری', detail.irrigation],
            ].map(([a, b]) => (
              <div key={a}>
                <span>{a}</span>
                <strong>{b}</strong>
              </div>
            ))}
          </div>
          <h3 className="section-subtitle">تاریخچه بررسی این باغ</h3>
          {ctx.data.reports.filter((r) => r.orchard_id === detail.id).length ? (
            ctx.data.reports
              .filter((r) => r.orchard_id === detail.id)
              .map((r) => (
                <button
                  className="detail-report-link"
                  key={r.id}
                  onClick={() => {
                    setDetail(null)
                    ctx.openReport(r)
                  }}
                >
                  <Leaf size={17} />
                  {r.data.title}
                  <ArrowLeft size={16} />
                </button>
              ))
          ) : (
            <p className="muted">هنوز گزارشی برای این باغ ثبت نشده است.</p>
          )}
          <div className="modal-actions">
            <button
              className="button primary"
              onClick={() => {
                const id = detail.id
                setDetail(null)
                ctx.startAnalysis(undefined, id)
              }}
            >
              بررسی تصویر درخت
              <ArrowLeft size={15} />
            </button>
            <button
              className="button secondary"
              onClick={() => {
                const o = detail
                setDetail(null)
                ctx.openOrchard(o)
              }}
            >
              <Pencil size={15} />
              ویرایش اطلاعات
            </button>
          </div>
        </Modal>
      )}
    </>
  )
}
