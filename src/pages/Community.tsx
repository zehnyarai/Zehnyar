import { useState } from 'react'
import { MessageSquare, Plus, Search, Trash2, Users } from 'lucide-react'
import type { AppContext } from '../types'
import type { ExperienceInput } from '../fieldwork'
import { EXPERIENCE_CATEGORIES, validateField } from '../fieldwork'
import { errorMessage, persianDate } from '../api'
import { IS_STANDALONE } from '../config'
import { useFieldRecords } from '../useFieldRecords'
import { Badge, InfoBanner, Modal, Spinner } from '../components/ui'

export default function Community({ ctx }: { ctx: AppContext }) {
  const records = useFieldRecords('experiences')
  const [category, setCategory] = useState('همه'),
    [search, setSearch] = useState(''),
    [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  const [form, setForm] = useState<ExperienceInput>({
    title: '',
    category: EXPERIENCE_CATEGORIES[0],
    body: '',
    province: '',
    cultivar: '',
    season: '',
  })
  const update = (key: keyof ExperienceInput, value: string) =>
    setForm((old) => ({ ...old, [key]: value }))
  const filtered = records.records.filter(
    (r) =>
      (category === 'همه' || r.data.category === category) &&
      `${r.data.title} ${r.data.body} ${r.data.province}`.includes(search.trim())
  )
  async function save() {
    setError('')
    try {
      const data = validateField('experiences', form)
      setBusy(true)
      const record = await records.save(data)
      setOpen(false)
      setForm({
        title: '',
        category: EXPERIENCE_CATEGORIES[0],
        body: '',
        province: '',
        cultivar: '',
        season: '',
      })
      ctx.notify(
        record.visibility === 'private'
          ? 'تجربه فقط در دفتر همین دستگاه ذخیره شد؛ به دیگران ارسال نشده است.'
          : 'تجربه ثبت شد؛ انتشار عمومی نیاز به بررسی مدیر دارد.',
        'success'
      )
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <div className="reference-page community-page" inert={open}>
        <div className="reference-heading">
          <span className="feature-icon blue">
            <Users size={29} />
          </span>
          <div>
            <h1>دیوار تجربه</h1>
            <p>تجارب عملی و بومی باغداران پسته — یاد بگیرید و به اشتراک بگذارید.</p>
          </div>
          <button
            className="button primary"
            onClick={() => {
              setOpen(true)
              setError('')
            }}
          >
            <Plus size={19} />
            ثبت تجربه
          </button>
        </div>
        <p className="community-scope">
          {IS_STANDALONE
            ? 'تجربه‌ها خصوصی و روی همین دستگاه می‌مانند. تجربهٔ شخصی جای پژوهش یا نظر کارشناس را نمی‌گیرد.'
            : 'تجربه‌های منتشرشده پس از بررسی مدیر و نوشته‌های خودتان؛ تجربهٔ شخصی جای پژوهش یا نسخه کارشناس نیست.'}
        </p>
        <div className="community-toolbar">
          <div className="category-filters">
            {['همه', ...EXPERIENCE_CATEGORIES].map((c) => (
              <button
                key={c}
                className={`${category === c ? 'active' : ''} ${c === 'سایر' ? 'other-category' : ''}`}
                onClick={() => setCategory(c)}
              >
                {c}
              </button>
            ))}
          </div>
          <label className="community-search">
            <Search size={18} />
            <input
              placeholder="جستجوی تجربه‌ها…"
              aria-label="جستجوی تجربه‌ها"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
        </div>
        {records.error && <InfoBanner tone="warning">{records.error}</InfoBanner>}
        {records.loading ? (
          <div className="reference-card loading-inline">
            <Spinner />
          </div>
        ) : filtered.length ? (
          <div className="experience-grid">
            {filtered.map((r) => (
              <article className="reference-card experience-card" key={r.id}>
                <header>
                  <Badge tone="blue">{r.data.category}</Badge>
                  <Badge tone={r.visibility === 'published' ? 'green' : 'gray'}>
                    {r.visibility === 'published'
                      ? 'تجربه منتشرشده'
                      : r.visibility === 'pending'
                        ? 'در انتظار بررسی'
                        : 'خصوصی روی دستگاه'}
                  </Badge>
                </header>
                <h2>{r.data.title}</h2>
                <p className="experience-body">{r.data.body}</p>
                <div className="experience-context">
                  <span>{r.data.province}</span>
                  {r.data.cultivar && <span>{r.data.cultivar}</span>}
                  {r.data.season && <span>{r.data.season}</span>}
                </div>
                <footer>
                  <span>
                    {r.author} · {persianDate(r.created_at)}
                  </span>
                  {r.visibility !== 'published' && (
                    <button
                      className="icon-button"
                      aria-label="حذف تجربه"
                      onClick={() => {
                        if (confirm('این تجربه حذف شود؟'))
                          void records
                            .remove(r.id)
                            .catch((e) => ctx.notify(errorMessage(e), 'error'))
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </footer>
              </article>
            ))}
          </div>
        ) : (
          <section className="reference-card reference-empty">
            <MessageSquare size={52} />
            <p>
              {category === 'همه' && !search
                ? 'هنوز تجربه‌ای ثبت نشده است.'
                : 'تجربه‌ای با این فیلتر پیدا نشد.'}
            </p>
            <button className="button secondary" onClick={() => setOpen(true)}>
              <Plus size={18} />
              اولین تجربه را ثبت کنید
            </button>
          </section>
        )}
      </div>
      {open && (
        <Modal
          title="ثبت تجربه باغداری"
          subtitle="زمینه، مشاهده و نتیجه را جدا بنویسید؛ بدون وعده درمان یا تبلیغ سم."
          onClose={() => {
            if (!busy) setOpen(false)
          }}
          wide
        >
          <form
            onSubmit={(e) => {
              e.preventDefault()
              void save()
            }}
          >
            <div className="reference-form-grid">
              <label>
                عنوان تجربه *
                <input
                  value={form.title}
                  maxLength={160}
                  minLength={3}
                  onChange={(e) => update('title', e.target.value)}
                  required
                />
              </label>
              <label>
                دسته تجربه
                <select value={form.category} onChange={(e) => update('category', e.target.value)}>
                  {EXPERIENCE_CATEGORIES.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </label>
              <label>
                استان / منطقه *
                <input
                  value={form.province}
                  maxLength={60}
                  minLength={2}
                  onChange={(e) => update('province', e.target.value)}
                  required
                />
              </label>
              <label>
                رقم و پایه
                <input
                  value={form.cultivar}
                  maxLength={60}
                  onChange={(e) => update('cultivar', e.target.value)}
                />
              </label>
              <label>
                سال و مرحله رشد
                <input
                  value={form.season}
                  maxLength={60}
                  placeholder="مثلاً برداشت ۱۴۰۵"
                  onChange={(e) => update('season', e.target.value)}
                />
              </label>
            </div>
            <label className="full-label">
              شرح تجربه و نتیجه مشاهده‌شده *
              <textarea
                rows={7}
                value={form.body}
                minLength={20}
                maxLength={4000}
                placeholder="چه مسئله‌ای داشتید؟ چه شواهدی بود؟ چه کاری و با نظر چه کسی انجام شد؟ نتیجه چه بود و چه محدودیتی داشت؟ اطلاعات تماس، تبلیغ و نسخه سم/کود وارد نکنید."
                onChange={(e) => update('body', e.target.value)}
                required
              />
            </label>
            <InfoBanner>
              {IS_STANDALONE
                ? 'این نوشته فقط روی دستگاه ذخیره می‌شود و در پشتیبان قرار می‌گیرد؛ به سایر باغداران ارسال نمی‌شود.'
                : 'نوشته در انتظار بررسی مدیر قرار می‌گیرد؛ انتشار عمومی خودکار نیست.'}
            </InfoBanner>
            {error && (
              <div className="form-error" role="alert">
                {error}
              </div>
            )}
            <div className="modal-actions">
              <button className="button primary" type="submit" disabled={busy}>
                {busy ? (
                  <Spinner />
                ) : (
                  <>
                    <Plus size={18} />
                    ثبت تجربه
                  </>
                )}
              </button>
              <button
                type="button"
                className="button secondary"
                onClick={() => setOpen(false)}
                disabled={busy}
              >
                انصراف
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
