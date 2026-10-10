import { useState } from 'react'
import {
  ArrowLeft,
  BookOpen,
  ChevronLeft,
  CircleAlert,
  Download,
  ExternalLink,
  Eye,
  FileSearch,
  FlaskConical,
  Leaf,
  ListChecks,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import type { AppContext, Article, Report } from '../types'
import { api, downloadText, errorMessage, fa, persianDate } from '../api'
import { Badge, CheckList, InfoBanner, Modal, Spinner } from './ui'

export function ArticleDetail({ article, onClose }: { article: Article; onClose: () => void }) {
  return (
    <Modal
      title="راهنمای مراقبت پسته"
      subtitle={`${article.category_label} · ${fa(article.reading_minutes)} دقیقه مطالعه`}
      onClose={onClose}
      wide
    >
      <article className="article-detail">
        <div className="article-detail-cover">
          <img src={article.image} alt="تصویر آموزشی تولیدشده از پسته" />
          <span>تصویر آموزشی تولیدشده؛ نمونه تشخیصی نیست</span>
        </div>
        <div className="article-detail-heading">
          <Badge>{article.category_label}</Badge>
          <span>
            <BookOpen size={14} />
            {fa(article.reading_minutes)} دقیقه
          </span>
        </div>
        <h1>{article.title}</h1>
        <p className="article-lead">{article.summary}</p>
        {article.sections.map((s, i) => (
          <section className="article-section" key={s.heading}>
            <span className="article-section-number">{fa(i + 1)}</span>
            <div>
              <h2>{s.heading}</h2>
              <p>{s.body}</p>
            </div>
          </section>
        ))}
        <InfoBanner tone="warning">{article.disclaimer}</InfoBanner>
        <div className="source-box">
          <h3>
            <ShieldCheck size={18} />
            منابع مطالعه و دامنه کاربرد
          </h3>
          {article.sources.map((source) => (
            <div key={source.url}>
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.title}
                <ExternalLink size={14} />
              </a>
              <p>{source.scope}</p>
            </div>
          ))}
          <small>
            نسخه گردآوری: {article.version} · {persianDate(article.updated_at, { year: 'numeric' })}
            <br />
            {article.review_status}. تاریخ گردآوری به معنی بررسی زنده یا انتشار جدید منبع نیست.
          </small>
        </div>
      </article>
    </Modal>
  )
}

export function ReportDetail({
  report,
  ctx,
  onClose,
}: {
  report: Report
  ctx: AppContext
  onClose: () => void
}) {
  const [tab, setTab] = useState('observations')
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const d = report.data
  function download() {
    const text = [
      report.is_sample ? 'گزارش نمونه — تحلیل عکس شما نیست' : 'پستینو — گزارش غربالگری تصویر',
      d.title,
      report.orchard_name ?? '',
      persianDate(report.created_at, { year: 'numeric' }),
      d.summary,
      '\nمشاهدات:',
      ...d.observations,
      '\nفرضیه‌های احتمالی:',
      ...d.hypotheses.map(
        (h) =>
          `${h.name} — امتیاز غیرکالیبره مدل: ${fa(h.confidence * 100)}٪\n${h.evidence}\n${h.next_step}`
      ),
      '\nاقدام بعدی:',
      ...d.actions,
      '\nبررسی تکمیلی:',
      ...d.needed_tests,
      '\nپرسش‌ها:',
      ...d.follow_up_questions,
      d.disclaimer,
      `نسخه دانشنامه: ${d.knowledge_version}`,
    ].join('\n')
    downloadText(`pestino-${report.is_sample ? 'SAMPLE-' : ''}${report.id.slice(0, 8)}.txt`, text)
    ctx.notify('نسخه متنی گزارش دریافت شد.')
  }
  async function remove() {
    setBusy(true)
    try {
      await api(`/reports/${report.id}`, { method: 'DELETE' })
      await ctx.refresh()
      onClose()
      ctx.notify('تصویر و محتوای گزارش حذف شد. اعتبار مصرف‌شده بازنمی‌گردد.')
    } catch (e) {
      ctx.notify(errorMessage(e), 'error')
    } finally {
      setBusy(false)
    }
  }
  const related = ctx.knowledge.articles.filter((a) => d.knowledge_ids.includes(a.id))
  return (
    <Modal
      title={d.title}
      subtitle={`${report.orchard_name ?? 'باغ مشخص نشده'} · ${report.tree_part} · ${persianDate(report.created_at, { year: 'numeric' })}`}
      onClose={onClose}
      wide
    >
      <div className="report-detail">
        {!!report.is_sample && (
          <InfoBanner tone="warning">
            <strong>گزارش نمونه؛ این نتیجه تحلیل عکس شما نیست.</strong> متن و امتیاز اطمینان صرفاً
            برای نمایش امکانات‌اند.
          </InfoBanner>
        )}
        <div className="report-summary">
          <div className="report-detail-image">
            <img src={report.image_url ?? '/images/pistachio-leaves.jpg'} alt="تصویر گزارش" />
            {!!report.is_sample && <span>تصویر آموزشی تولیدشده</span>}
          </div>
          <div>
            <div className="report-summary-badges">
              <Badge
                tone={d.urgency === 'high' ? 'red' : d.urgency === 'medium' ? 'amber' : 'green'}
              >
                {d.urgency === 'high'
                  ? 'ارجاع فوری به کارشناس'
                  : d.urgency === 'medium'
                    ? 'نیازمند بررسی تکمیلی'
                    : 'پیگیری معمول'}
              </Badge>
              {!!report.is_sample && <Badge tone="gray">نمونه نمایشی</Badge>}
            </div>
            <h3>خلاصه بررسی اولیه</h3>
            <p>{d.summary}</p>
            <div className="report-quality">
              <Eye size={14} />
              کیفیت / محدودیت تصویر: {d.quality}
            </div>
          </div>
        </div>
        <div className="tabs report-tabs">
          {[
            ['observations', 'مشاهدات و احتمال‌ها', FileSearch],
            ['actions', 'اقدام و بررسی تکمیلی', ListChecks],
            ['sources', 'راهنماهای مرتبط', BookOpen],
          ].map(([id, label, Icon]) => {
            const TabIcon = Icon as typeof BookOpen
            return (
              <button
                className={tab === id ? 'active' : ''}
                onClick={() => setTab(id as string)}
                key={id as string}
              >
                <TabIcon size={16} />
                {label as string}
              </button>
            )
          })}
        </div>
        {tab === 'observations' && (
          <div className="report-tab-content">
            <h3>
              <Eye size={18} />
              چه چیزی قابل مشاهده است؟
            </h3>
            <ul className="observation-list">
              {d.observations.map((o, i) => (
                <li key={i}>{o}</li>
              ))}
            </ul>
            <h3>
              <CircleAlert size={18} />
              فرضیه‌های محتمل، نه تشخیص قطعی
            </h3>
            {d.hypotheses.length ? (
              d.hypotheses.map((h) => (
                <div className="hypothesis" key={h.name}>
                  <header>
                    <strong>{h.name}</strong>
                    <span>
                      {fa(Math.round(h.confidence * 100))}٪ <small>امتیاز مدل</small>
                    </span>
                  </header>
                  <div className="confidence-track">
                    <div style={{ width: `${h.confidence * 100}%` }} />
                  </div>
                  <p>{h.evidence}</p>
                  <div className="hypothesis-next">
                    <ChevronLeft size={15} />
                    {h.next_step}
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">از این تصویر نمی‌توان فرضیه تشخیصی قابل اتکا ارائه کرد.</p>
            )}
            <p className="confidence-disclaimer">
              امتیاز مدل کالیبره نشده است و احتمال واقعی بیماری یا دقت اندازه‌گیری‌شده نیست.
            </p>
          </div>
        )}
        {tab === 'actions' && (
          <div className="report-tab-content">
            <h3>
              <ListChecks size={18} />
              قدم‌های بعدی و کم‌خطر
            </h3>
            <CheckList items={d.actions} />
            <h3>
              <FlaskConical size={18} />
              چه بررسی‌هایی کم داریم؟
            </h3>
            <ul className="observation-list">
              {d.needed_tests.length ? (
                d.needed_tests.map((t, i) => <li key={i}>{t}</li>)
              ) : (
                <li>نیاز به آزمایش با نظر کارشناس و زمینه باغ تعیین می‌شود.</li>
              )}
            </ul>
            <h3>برای دقیق‌تر شدن بررسی</h3>
            <ul className="observation-list">
              {d.follow_up_questions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
            <button
              className="button secondary"
              onClick={() => {
                onClose()
                ctx.openTask()
              }}
            >
              ثبت یادآور برای پیگیری
              <ArrowLeft size={16} />
            </button>
          </div>
        )}
        {tab === 'sources' && (
          <div className="report-tab-content">
            <p className="muted">
              راهنماها آموزشی‌اند. نسخه دانشنامه استفاده‌شده: {d.knowledge_version}
            </p>
            {related.map((a) => (
              <button
                className="related-guide"
                key={a.id}
                onClick={() => {
                  onClose()
                  ctx.openArticle(a)
                }}
              >
                <span>
                  <Leaf size={18} />
                </span>
                <div>
                  <strong>{a.title}</strong>
                  <small>
                    {a.category_label} · {fa(a.reading_minutes)} دقیقه مطالعه
                  </small>
                </div>
                <ArrowLeft size={17} />
              </button>
            ))}
          </div>
        )}
        <div className="report-disclaimer">
          <ShieldCheck size={18} />
          <p>{d.disclaimer}</p>
        </div>
        <div className="modal-actions">
          <button className="button primary" onClick={download}>
            <Download size={16} />
            دریافت گزارش متنی
          </button>
          {report.id !== 'example' && (
            <button className="button danger ghost" onClick={() => setConfirm(!confirm)}>
              <Trash2 size={15} />
              حذف گزارش و تصویر
            </button>
          )}
        </div>
        {confirm && (
          <div className="delete-confirm">
            <p>
              تصویر و محتوای گزارش حذف می‌شود. برای جلوگیری از تغییر سقف اعتبار، سابقه مصرف بدون متن
              و تصویر نگه داشته می‌شود.
            </p>
            <button
              className="button danger small"
              disabled={busy}
              onClick={() => {
                void remove()
              }}
            >
              {busy ? <Spinner /> : 'تأیید حذف'}
            </button>
            <button className="text-button" disabled={busy} onClick={() => setConfirm(false)}>
              انصراف
            </button>
          </div>
        )}
      </div>
    </Modal>
  )
}

export function HelpModal({
  onClose,
  privacy = false,
}: {
  onClose: () => void
  privacy?: boolean
}) {
  return (
    <Modal
      title={privacy ? 'حریم خصوصی و حدود استفاده' : 'از یک عکس، تا یک قدم آگاهانه'}
      subtitle={
        privacy
          ? 'پیش‌نویس سیاست نسخه آزمایشی؛ نیازمند بررسی پیش از انتشار'
          : 'راهنمای شروع کار با پستینو'
      }
      onClose={onClose}
    >
      {privacy ? (
        <div className="legal-copy">
          <h3>اطلاعاتی که ذخیره می‌شود</h3>
          <p>
            اطلاعات حساب، مشخصات باغ، یادآورها و گزارش‌های شما در سرور ذخیره می‌شوند. در این نسخه
            موقعیت دقیق GPS دریافت نمی‌شود. عکس واقعی فقط برای صاحب حساب قابل دریافت است.
          </p>
          <h3>ارسال تصویر با رضایت شما</h3>
          <p>
            پس از تأیید شما، تصویر به سرویس بینایی تنظیم‌شده توسط مدیر ارسال می‌شود. اطلاعات EXIF و
            موقعیت فایل پیش از ذخیره و ارسال حذف می‌شوند. شرایط نگهداری سرویس خارجی باید پیش از عرضه
            عمومی اعلام و بررسی شود.
          </p>
          <h3>حذف عکس و گزارش</h3>
          <p>
            از داخل گزارش می‌توانید تصویر و محتوای آن را حذف کنید. یک سابقه بدون محتوا برای محاسبه
            اعتبار نگه داشته می‌شود. سوابق پرداخت و رویدادهای امنیتی جدا هستند. حذف کامل حساب و
            سیاست نگهداری پشتیبان‌ها باید پیش از عرضه عمومی تکمیل شود.
          </p>
          <h3>محدودیت علمی</h3>
          <p>
            این ابزار غربالگری احتمالی است. هیچ عکس یا امتیاز اطمینانی جای آزمایش، بازدید کارشناس،
            بررسی مجوز سم و ارزیابی ایمنی محصول را نمی‌گیرد. دانشنامه اولیه هنوز تأیید تخصصی محلی
            ندارد.
          </p>
          <h3>حالت آزمایشی</h3>
          <p>
            باغ‌ها، گزارش‌ها و تراکنش‌های نمونه مشخص هستند. تا تنظیم درگاه و سرویس، پرداخت و تحلیل
            واقعی انجام نمی‌شود. تصاویر آموزشی برنامه تولیدشده‌اند و مدرک تشخیص نیستند.
          </p>
        </div>
      ) : (
        <>
          <div className="help-intro">
            <Leaf size={32} />
            <h3>همراه باغت باش، نه فقط موقع برداشت.</h3>
            <p>پستینو مشاهده‌ها و برنامه مراقبت را یک‌جا نگه می‌دارد.</p>
          </div>
          {[
            [
              '۱',
              'باغت را بشناسان',
              'شهر، رقم، سن درخت‌ها و نوع آبیاری را ثبت کن. داده‌های نمونه جای اطلاعات باغ واقعی نیستند.',
            ],
            [
              '۲',
              'عکس روشن بگیر',
              'برای شروع، یک عکس نزدیک و بدون فیلتر از بخش مورد نظر بفرست. توضیح کوتاه از زمان شروع علائم مفید است.',
            ],
            [
              '۳',
              'با احتیاط نتیجه را دنبال کن',
              'مشاهدات را از احتمال‌ها جدا ببین. برای سم، کود یا آسیب جدی، از کارشناس محلی و آزمایش کمک بگیر.',
            ],
            [
              '۴',
              'پیگیری را فراموش نکن',
              'در تقویم یادآور بساز و تصاویر بعدی را با تاریخچه مقایسه کن.',
            ],
          ].map(([n, title, text]) => (
            <div className="help-step" key={n}>
              <span>{n}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            </div>
          ))}
          <InfoBanner tone="warning">
            این نسخه یک پایلوت قابل توسعه است؛ سرویس‌ها، تأیید علمی و مراحل انتشار اندروید هنوز نیاز
            به تکمیل دارند.
          </InfoBanner>
        </>
      )}
    </Modal>
  )
}
