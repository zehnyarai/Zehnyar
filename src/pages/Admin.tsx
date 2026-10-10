import { useEffect, useState } from 'react'
import {
  Activity,
  CheckCircle2,
  CircleAlert,
  CreditCard,
  Download,
  ExternalLink,
  FileClock,
  LockKeyhole,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  Users,
  Wallet,
} from 'lucide-react'
import type { AdminData, AppContext, Payment } from '../types'
import { api, downloadText, errorMessage, fa, persianDate } from '../api'
import { Badge, EmptyState, InfoBanner, PageTitle, Spinner } from '../components/ui'
import { PaymentBadge } from './Subscription'

export default function Admin({ ctx }: { ctx: AppContext }) {
  const [data, setData] = useState<AdminData | null>(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('payments')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [busy, setBusy] = useState('')
  const isAdmin = ctx.data.user?.role === 'admin'
  async function load() {
    try {
      setData(await api<AdminData>(isAdmin ? '/admin/overview' : '/admin/demo'))
      setError('')
    } catch (e) {
      setError(errorMessage(e))
    }
  }
  useEffect(() => {
    let active = true
    void api<AdminData>(isAdmin ? '/admin/overview' : '/admin/demo')
      .then((d) => {
        if (active) setData(d)
      })
      .catch((e) => {
        if (active) setError(errorMessage(e))
      })
    return () => {
      active = false
    }
  }, [isAdmin])
  const transactions =
    data?.transactions.filter(
      (p) =>
        (status === 'all' || p.status === status) &&
        [p.user_name, p.email, p.id, p.ref_id]
          .join(' ')
          .toLowerCase()
          .includes(search.toLowerCase())
    ) ?? []
  const users =
    data?.users.filter((u) =>
      [u.name, u.email].join(' ').toLowerCase().includes(search.toLowerCase())
    ) ?? []
  async function reconcile(p: Payment) {
    if (data?.is_demo) {
      ctx.notify('تراکنش نمونه فقط خواندنی است و پرداخت واقعی نیست.')
      return
    }
    setBusy(p.id)
    try {
      const result = await api<{ status: string }>(`/admin/payments/${p.id}/reconcile`, {
        method: 'POST',
      })
      await load()
      ctx.notify(
        result.status === 'success'
          ? 'درگاه پرداخت را تأیید کرد.'
          : 'وضعیت پرداخت از درگاه بررسی شد.',
        result.status === 'success' ? 'success' : 'info'
      )
    } catch (e) {
      ctx.notify(errorMessage(e), 'error')
    } finally {
      setBusy('')
    }
  }
  async function exportCsv() {
    if (data?.is_demo) {
      const headers = 'sample_id,user,plan,amount_IRR,status\n'
      try {
        await downloadText(
          'pestino-DEMO-payments.csv',
          headers +
            transactions
              .map((p) =>
                [p.id, p.user_name, p.plan, p.amount_rial, p.status]
                  .map((v) => `"${String(v).replace(/"/g, '""')}"`)
                  .join(',')
              )
              .join('\n'),
          'text/csv;charset=utf-8'
        )
        ctx.notify('فقط داده‌های نمونه خروجی گرفته شد.')
      } catch (e) {
        ctx.notify(errorMessage(e), 'error')
      }
      return
    }
    void fetch('/api/admin/payments/export', { credentials: 'same-origin' })
      .then(async (res) => {
        if (!res.ok) throw new Error('دریافت خروجی مجاز نیست.')
        await downloadText('pestino-payments.csv', await res.text(), 'text/csv;charset=utf-8')
      })
      .catch((e) => ctx.notify(errorMessage(e), 'error'))
  }
  return (
    <>
      <PageTitle
        eyebrow="کنترل شفاف و امن"
        title="پنل مدیریت"
        subtitle="کاربران، وضعیت سرویس‌ها و تراکنش‌های تأییدشده را مدیریت کن."
        action={
          <button
            className="button secondary"
            onClick={() => {
              void load()
            }}
          >
            <RefreshCw size={16} />
            به‌روزرسانی
          </button>
        }
      />
      {data?.is_demo && (
        <InfoBanner tone="warning">
          <strong>این پنل نمایش آزمایشی و فقط خواندنی است.</strong> اعداد و کاربران زیر نمونه‌اند؛
          هیچ درآمد واقعی یا اطلاعات کاربران دیگر نمایش داده نمی‌شود. پنل واقعی به ورود مدیر نیاز
          دارد.
        </InfoBanner>
      )}
      {error && <InfoBanner tone="warning">{error}</InfoBanner>}
      {!data && !error ? (
        <div className="card loading-inline">
          <Spinner label="دریافت اطلاعات مدیریت…" />
        </div>
      ) : (
        data && (
          <>
            <div className="admin-stats stats-grid">
              {[
                {
                  label: 'درآمد تأییدشده',
                  value: fa(data.metrics.revenue_rial / 10),
                  detail: 'تومان · پرداخت موفق واقعی، بدون Sandbox',
                  icon: Wallet,
                  style: 'sage',
                },
                {
                  label: 'کل تراکنش‌ها',
                  value: fa(data.metrics.payments),
                  detail: 'تمام وضعیت‌های پرداخت',
                  icon: CreditCard,
                  style: 'blue',
                },
                {
                  label: 'در انتظار تأیید',
                  value: fa(data.metrics.pending),
                  detail: 'نیازمند بررسی وضعیت درگاه',
                  icon: FileClock,
                  style: 'sand',
                },
                {
                  label: 'کاربران ثبت‌شده',
                  value: fa(data.metrics.users),
                  detail: data.is_demo ? 'کاربران نمونه' : 'حساب واقعی، بدون مهمان آزمایشی',
                  icon: Users,
                  style: 'olive',
                },
              ].map((s) => (
                <div className="stat-card" key={s.label}>
                  <div className="stat-top">
                    <span>{s.label}</span>
                    <span className={`stat-icon ${s.style}`}>
                      <s.icon size={20} />
                    </span>
                  </div>
                  <strong>{s.value}</strong>
                  <p>
                    {s.detail}
                    {data.is_demo && ' · نمونه'}
                  </p>
                </div>
              ))}
            </div>
            <div className="card admin-content">
              <div className="tabs admin-tabs">
                {[
                  ['payments', 'پرداخت‌ها', CreditCard],
                  ['users', 'کاربران', Users],
                  ['services', 'وضعیت سرویس‌ها', Settings2],
                ].map(([id, label, Icon]) => {
                  const TabIcon = Icon as typeof CreditCard
                  return (
                    <button
                      key={id as string}
                      className={tab === id ? 'active' : ''}
                      onClick={() => {
                        setTab(id as string)
                        setSearch('')
                      }}
                    >
                      <TabIcon size={17} />
                      {label as string}
                    </button>
                  )
                })}
              </div>
              {tab !== 'services' && (
                <div className="list-toolbar">
                  <label className="search-input">
                    <Search size={16} />
                    <input
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      placeholder={
                        tab === 'payments' ? 'جستجوی نام، ایمیل یا شناسه…' : 'جستجوی کاربر…'
                      }
                      aria-label="جستجوی مدیریت"
                    />
                  </label>
                  {tab === 'payments' && (
                    <>
                      <select
                        value={status}
                        onChange={(e) => setStatus(e.target.value)}
                        aria-label="وضعیت پرداخت"
                      >
                        <option value="all">همه وضعیت‌ها</option>
                        <option value="paid">موفق</option>
                        <option value="pending">در انتظار تأیید</option>
                        <option value="failed">ناموفق</option>
                        <option value="cancelled">لغوشده</option>
                      </select>
                      <button className="button secondary small" onClick={exportCsv}>
                        <Download size={15} />
                        خروجی CSV
                      </button>
                    </>
                  )}
                </div>
              )}
              {tab === 'payments' &&
                (transactions.length ? (
                  <div className="table-scroll">
                    <table className="admin-table">
                      <thead>
                        <tr>
                          <th>باغدار</th>
                          <th>شناسه تراکنش</th>
                          <th>طرح</th>
                          <th>مبلغ (تومان)</th>
                          <th>وضعیت</th>
                          <th>تاریخ</th>
                          <th>عملیات</th>
                        </tr>
                      </thead>
                      <tbody>
                        {transactions.map((p) => (
                          <tr key={p.id}>
                            <td>
                              <strong>{p.user_name}</strong>
                              <small className="latin-cell">{p.email}</small>
                            </td>
                            <td className="latin-cell">{p.id.slice(0, 12)}</td>
                            <td>
                              {p.plan === 'monthly' ? 'ماهانه' : 'سالانه'}
                              {!!p.is_sandbox && <small>Sandbox · آزمایشی</small>}
                            </td>
                            <td>{fa(p.amount_rial / 10)}</td>
                            <td>
                              <PaymentBadge status={p.status} />
                            </td>
                            <td>{persianDate(p.created_at)}</td>
                            <td>
                              {['pending', 'failed', 'verifying'].includes(p.status) ? (
                                <button
                                  className="text-button"
                                  onClick={() => {
                                    void reconcile(p)
                                  }}
                                  disabled={!!busy}
                                >
                                  {busy === p.id ? (
                                    <Spinner label="بررسی…" />
                                  ) : (
                                    <>
                                      <RefreshCw size={13} />
                                      استعلام درگاه
                                    </>
                                  )}
                                </button>
                              ) : (
                                <span className="payment-verified">
                                  <CheckCircle2 size={14} />
                                  {p.status === 'paid' ? 'تأییدشده' : '—'}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyState
                    icon={<CreditCard size={28} />}
                    title="تراکنشی پیدا نشد"
                    text="جستجو و فیلتر را تغییر بده یا بعد از اولین پرداخت دوباره بررسی کن."
                  />
                ))}
              {tab === 'users' &&
                (users.length ? (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>باغدار</th>
                          <th>ایمیل</th>
                          <th>نقش</th>
                          <th>اشتراک</th>
                          <th>تاریخ عضویت</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((u) => (
                          <tr key={u.id}>
                            <td>
                              <strong>{u.name}</strong>
                            </td>
                            <td className="latin-cell">{u.email}</td>
                            <td>{u.role === 'admin' ? 'مدیر' : 'باغدار'}</td>
                            <td>
                              <Badge
                                tone={
                                  (u.subscription_active ??
                                  !!(
                                    u.subscription_until &&
                                    u.subscription_until > new Date().toISOString()
                                  ))
                                    ? 'green'
                                    : 'gray'
                                }
                              >
                                {(u.subscription_active ??
                                !!(
                                  u.subscription_until &&
                                  u.subscription_until > new Date().toISOString()
                                ))
                                  ? u.subscription_is_sandbox
                                    ? 'حرفه‌ای آزمایشی'
                                    : 'حرفه‌ای'
                                  : 'همراه'}
                              </Badge>
                            </td>
                            <td>{persianDate(u.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyState
                    icon={<Users size={28} />}
                    title="کاربری پیدا نشد"
                    text="نام یا ایمیل دیگری را جستجو کن."
                  />
                ))}
              {tab === 'services' && (
                <div className="services-panel">
                  {[
                    {
                      icon: Activity,
                      title: 'سرویس بینایی هوشمند',
                      ready: data.services.vision_configured,
                      text: 'VISION_PROVIDER · VISION_MODEL · GROQ_API_KEY یا OPENAI_API_KEY',
                    },
                    {
                      icon: CreditCard,
                      title: 'درگاه زرین‌پال',
                      ready: data.services.payment_configured,
                      text: 'ZARINPAL_MERCHANT_ID · PUBLIC_BASE_URL (HTTPS)',
                    },
                    {
                      icon: ShieldCheck,
                      title: 'بازبینی علمی و محلی دانشنامه',
                      ready: data.services.knowledge_reviewed,
                      text: `نسخه ${data.services.knowledge_version} · نیازمند تأیید متخصص پسته در ایران`,
                    },
                    {
                      icon: LockKeyhole,
                      title: 'پیش‌بینی زنده آب‌وهوا',
                      ready: false,
                      text: 'در این نسخه متصل نیست؛ عدد یا پیش‌بینی ساختگی ارائه نمی‌شود.',
                    },
                  ].map((s) => (
                    <div className="service-row" key={s.title}>
                      <span className="service-icon">
                        <s.icon size={22} />
                      </span>
                      <div>
                        <h3>{s.title}</h3>
                        <p>{s.text}</p>
                      </div>
                      <Badge tone={s.ready ? 'green' : 'amber'}>
                        {s.ready ? 'تنظیم شده' : 'متصل نیست / در انتظار'}
                      </Badge>
                    </div>
                  ))}
                  <InfoBanner>
                    تنظیم کلیدها فقط از محیط امن سرور انجام می‌شود. «تنظیم شده» به معنی وجود
                    پیکربندی است، نه تأیید اتصال یا دقت سرویس.{' '}
                    {data.services.payment_sandbox
                      ? 'درگاه در حالت آزمایشی Sandbox است.'
                      : 'درگاه در حالت عملیاتی تنظیم شده است.'}
                  </InfoBanner>
                  <a className="text-button" href="/api/docs" target="_blank" rel="noreferrer">
                    مستندات API
                    <ExternalLink size={14} />
                  </a>
                </div>
              )}
              <footer className="admin-footer">
                <CircleAlert size={14} />
                وضعیت موفق فقط با تأیید سرور درگاه ثبت می‌شود؛ تغییر دستی به موفق یا بازپرداخت داخل
                اپ مجاز نیست.
              </footer>
            </div>
          </>
        )
      )}
    </>
  )
}
