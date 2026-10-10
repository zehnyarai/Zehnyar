import { IS_STANDALONE } from './config'
import LocalSettings from './pages/LocalSettings'
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ArrowLeft,
  Bell,
  BookOpen,
  CalendarDays,
  Check,
  ChevronLeft,
  CircleHelp,
  CreditCard,
  FileChartColumn,
  Home,
  LayoutDashboard,
  Leaf,
  Menu,
  PanelRightClose,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Trees,
  UserRound,
  X,
} from 'lucide-react'
import type { AppContext, Article, Bootstrap, Knowledge, Orchard, Page, Report } from './types'
import { api, errorMessage, fa, persianDate, today } from './api'
import { Badge, Logo, Spinner } from './components/ui'
import { AuthForm, OrchardForm, ProfileModal, TaskForm } from './components/forms'
import { ArticleDetail, HelpModal, ReportDetail } from './components/details'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Orchards from './pages/Orchards'
import Reports from './pages/Reports'
import CalendarPage from './pages/Calendar'
import KnowledgePage from './pages/Knowledge'
import Subscription from './pages/Subscription'
import Admin from './pages/Admin'

const paths: Record<Page, string> = {
  dashboard: '/',
  analysis: '/analysis',
  orchards: '/orchards',
  reports: '/reports',
  calendar: '/calendar',
  knowledge: '/knowledge',
  subscription: '/subscription',
  admin: '/admin',
}
const titles: Record<Page, string> = {
  dashboard: 'نمای کلی',
  analysis: IS_STANDALONE ? 'ثبت عکس' : 'تحلیل هوشمند',
  orchards: 'باغ‌های من',
  reports: IS_STANDALONE ? 'عکس‌ها و یادداشت‌ها' : 'گزارش‌ها',
  calendar: 'تقویم مراقبت',
  knowledge: 'دانشنامه پسته',
  subscription: IS_STANDALONE ? 'داده‌ها و پشتیبان' : 'اشتراک و پرداخت',
  admin: 'پنل مدیریت',
}
const pageFromPath = () =>
  (Object.entries(paths).find(
    ([, path]) => path === (IS_STANDALONE ? location.hash.slice(1) || '/' : location.pathname)
  )?.[0] as Page | undefined) ?? 'dashboard'
type ModalState =
  | { kind: 'auth' | 'task' | 'help' | 'privacy' | 'profile' }
  | { kind: 'orchard'; orchard?: Orchard }
  | { kind: 'article'; article: Article }
  | { kind: 'report'; report: Report }
let initialRequest: Promise<[Bootstrap, Knowledge]> | null = null
function initialize() {
  if (!initialRequest)
    initialRequest = Promise.all([
      api<Bootstrap>('/bootstrap'),
      api<Knowledge>('/knowledge'),
    ]).finally(() => {
      initialRequest = null
    })
  return initialRequest
}

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null)
  const [knowledge, setKnowledge] = useState<Knowledge | null>(null)
  const [page, setPage] = useState<Page>(pageFromPath)
  const [bootError, setBootError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [modal, setModal] = useState<ModalState | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [mobile, setMobile] = useState(() => window.matchMedia('(max-width: 820px)').matches)
  const [notifications, setNotifications] = useState(false)
  const [search, setSearch] = useState('')
  const [knowledgeSearch, setKnowledgeSearch] = useState('')
  const [searchKey, setSearchKey] = useState(0)
  const [analysisInput, setAnalysisInput] = useState<{
    file?: File
    orchard?: string
    key: number
  }>({ key: 0 })
  const [toast, setToast] = useState<{
    message: string
    type: 'success' | 'error' | 'info'
  } | null>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  const notificationsRef = useRef<HTMLDivElement>(null)
  const closeModal = useCallback(() => setModal(null), [])
  useEffect(() => {
    const query = window.matchMedia('(max-width: 820px)')
    const changed = () => setMobile(query.matches)
    query.addEventListener('change', changed)
    return () => query.removeEventListener('change', changed)
  }, [])
  useEffect(() => {
    let active = true
    setBootError('')
    void initialize()
      .then(([boot, kb]) => {
        if (active) {
          setData(boot)
          setKnowledge(kb)
        }
      })
      .catch((e) => {
        if (active) setBootError(errorMessage(e))
      })
    return () => {
      active = false
    }
  }, [attempt])
  useEffect(() => {
    const pop = () => {
      setPage(pageFromPath())
      setSidebarOpen(false)
    }
    window.addEventListener('popstate', pop)
    window.addEventListener('hashchange', pop)
    return () => {
      window.removeEventListener('popstate', pop)
      window.removeEventListener('hashchange', pop)
    }
  }, [])
  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 6000)
    return () => clearTimeout(timer)
  }, [toast])
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        searchRef.current?.focus()
      }
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [])
  useEffect(() => {
    if (!notifications) return
    const close = (e: MouseEvent) => {
      if (!notificationsRef.current?.contains(e.target as Node)) setNotifications(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [notifications])
  const refresh = useCallback(async () => {
    setData(await api<Bootstrap>('/bootstrap'))
  }, [])
  const navigate = useCallback((next: Page) => {
    setPage(next)
    setSidebarOpen(false)
    setNotifications(false)
    const target = IS_STANDALONE ? `#${paths[next]}` : paths[next]
    if ((IS_STANDALONE ? location.hash : location.pathname) !== target)
      history.pushState(null, '', target)
    window.scrollTo({ top: 0, behavior: 'auto' })
  }, [])
  const notify = useCallback(
    (message: string, type: 'success' | 'error' | 'info' = 'info') => setToast({ message, type }),
    []
  )
  const startAnalysis = useCallback(
    (file?: File, orchardId?: string) => {
      setAnalysisInput((old) => ({ file, orchard: orchardId, key: old.key + 1 }))
      navigate('analysis')
    },
    [navigate]
  )
  function submitSearch(e: React.FormEvent) {
    e.preventDefault()
    setKnowledgeSearch(search.trim())
    setSearchKey((key) => key + 1)
    navigate('knowledge')
  }
  if (!data || !knowledge)
    return (
      <div className="boot-screen">
        <Logo />
        {bootError ? (
          <>
            <h1>ارتباط با باغت برقرار نشد</h1>
            <p>{bootError}</p>
            <button className="button primary" onClick={() => setAttempt((a) => a + 1)}>
              تلاش دوباره
            </button>
          </>
        ) : (
          <>
            <div className="boot-leaf">
              <Leaf size={36} />
            </div>
            <Spinner label="در حال آماده‌کردن پیشخوان باغ…" />
          </>
        )}
      </div>
    )
  const ctx: AppContext = {
    data,
    knowledge,
    refresh,
    navigate,
    notify,
    openArticle: (article) => setModal({ kind: 'article', article }),
    openReport: (report) => setModal({ kind: 'report', report }),
    openAuth: () => (IS_STANDALONE ? navigate('subscription') : setModal({ kind: 'auth' })),
    openOrchard: (orchard) => setModal({ kind: 'orchard', orchard }),
    openTask: () => setModal({ kind: 'task' }),
    startAnalysis,
  }
  const nav = [
    { id: 'dashboard' as const, icon: LayoutDashboard },
    { id: 'analysis' as const, icon: Sparkles },
    { id: 'orchards' as const, icon: Trees },
    { id: 'reports' as const, icon: FileChartColumn },
    { id: 'calendar' as const, icon: CalendarDays },
    { id: 'knowledge' as const, icon: BookOpen },
  ]
  const pending = data.tasks.filter((t) => !t.done)
  return (
    <div className="app-shell">
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="بستن منو"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        id="sidebar-menu"
        className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}
        inert={!!modal || (mobile && !sidebarOpen)}
        aria-hidden={!!modal || (mobile && !sidebarOpen)}
      >
        <div className="sidebar-brand">
          <a
            href="/"
            aria-label="صفحه اصلی پستینو"
            onClick={(e) => {
              e.preventDefault()
              navigate('dashboard')
            }}
          >
            <Logo />
          </a>
          <button
            className="icon-button sidebar-close"
            aria-label="بستن منو"
            onClick={() => setSidebarOpen(false)}
          >
            <PanelRightClose size={21} />
          </button>
        </div>
        <div className="sidebar-navigation">
          <span className="nav-section-label">همراه باغ شما</span>
          <nav aria-label="منوی اصلی">
            {nav.map((item) => (
              <a
                key={item.id}
                href={IS_STANDALONE ? `#${paths[item.id]}` : paths[item.id]}
                onClick={(e) => {
                  e.preventDefault()
                  navigate(item.id)
                }}
                className={`nav-item ${page === item.id ? 'nav-active' : ''}`}
                aria-current={page === item.id ? 'page' : undefined}
              >
                <item.icon size={20} strokeWidth={1.7} />
                <span>{titles[item.id]}</span>
                {item.id === 'analysis' && !IS_STANDALONE && <span className="ai-badge">AI</span>}
                {item.id === 'orchards' && (
                  <span className="nav-count">{fa(data.orchards.length)}</span>
                )}
                {page === item.id && <ChevronLeft className="nav-active-arrow" size={15} />}
              </a>
            ))}
          </nav>
          <div className="nav-divider" />
          <a
            href="/subscription"
            onClick={(e) => {
              e.preventDefault()
              navigate('subscription')
            }}
            className={`nav-item ${page === 'subscription' ? 'nav-active' : ''}`}
          >
            <CreditCard size={20} strokeWidth={1.7} />
            <span>{titles.subscription}</span>
          </a>
        </div>
        <div className="sidebar-bottom">
          <div className="sidebar-tip">
            <div className="sidebar-tip-leaf">
              <Leaf size={29} strokeWidth={1.3} />
            </div>
            <strong>هر روز، یک قدم سبزتر</strong>
            <p>
              مراقبت‌های کوچک امروز،
              <br />
              تفاوت‌های بزرگ فردا.
            </p>
            <button onClick={() => setModal({ kind: 'help' })}>
              از کجا شروع کنم؟
              <ArrowLeft size={13} />
            </button>
            <span className="tip-decor decor-1" />
            <span className="tip-decor decor-2" />
          </div>
          {(data.user?.is_demo || data.user?.role === 'admin') && (
            <a
              className={`nav-item admin-nav ${page === 'admin' ? 'nav-active' : ''}`}
              href="/admin"
              onClick={(e) => {
                e.preventDefault()
                navigate('admin')
              }}
            >
              <Settings2 size={19} />
              <span>پنل مدیریت</span>
              {data.user?.is_demo ? (
                <span className="nav-mini">نمایش</span>
              ) : (
                <ShieldCheck size={14} />
              )}
            </a>
          )}
          <button
            className="sidebar-user"
            onClick={() =>
              IS_STANDALONE
                ? navigate('subscription')
                : setModal({ kind: !data.user || data.user.is_demo ? 'auth' : 'profile' })
            }
          >
            <span className="user-avatar">
              {data.user?.name.slice(0, 1) ?? <UserRound size={18} />}
            </span>
            <span>
              <strong>{data.user?.name ?? 'مهمان پستینو'}</strong>
              <small>
                {IS_STANDALONE
                  ? 'روی دستگاه · رایگان'
                  : !data.user || data.user.is_demo
                    ? 'حساب آزمایشی · ورود'
                    : data.usage.premium
                      ? 'باغدار حرفه‌ای'
                      : 'طرح همراه'}
              </small>
            </span>
            <ChevronLeft size={16} />
          </button>
        </div>
      </aside>
      <div className="main-shell" inert={!!modal || (mobile && sidebarOpen)}>
        <header className="topbar">
          <div className="topbar-breadcrumb">
            <button
              className="icon-button mobile-menu"
              aria-label="باز کردن منو"
              aria-expanded={sidebarOpen}
              aria-controls="sidebar-menu"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={23} />
            </button>
            <Home size={17} strokeWidth={1.6} />
            <span>پیشخوان</span>
            <ChevronLeft size={13} />
            <strong>{titles[page]}</strong>
          </div>
          <form className="topbar-search" onSubmit={submitSearch}>
            <Search size={17} />
            <input
              ref={searchRef}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="جستجو در دانشنامه…"
              aria-label="جستجوی سراسری"
            />
            <kbd>⌘ K</kbd>
          </form>
          <div className="topbar-actions">
            <span className="topbar-date">
              <CalendarDays size={15} />
              {persianDate(new Date(), { weekday: 'long' })}
            </span>
            <div ref={notificationsRef} className="notification-anchor">
              <button
                className={`icon-button notification-button ${notifications ? 'selected-button' : ''}`}
                aria-label="نمایش یادآورها"
                aria-expanded={notifications}
                onClick={() => setNotifications(!notifications)}
              >
                <Bell size={19} strokeWidth={1.7} />
                {pending.length > 0 && <span />}
              </button>
              {notifications && (
                <div className="notification-panel">
                  <header>
                    <strong>یادآورهای باغ</strong>
                    <Badge tone="gray">{fa(pending.length)}</Badge>
                  </header>
                  {pending.length ? (
                    pending.slice(0, 4).map((t) => (
                      <button key={t.id} onClick={() => navigate('calendar')}>
                        <span className="notification-leaf">
                          <Leaf size={15} />
                        </span>
                        <div>
                          <strong>{t.title}</strong>
                          <small>
                            {t.orchard_name ?? 'برنامه مراقبت'} ·{' '}
                            {t.due_date === today() ? 'امروز' : persianDate(t.due_date)}
                          </small>
                        </div>
                      </button>
                    ))
                  ) : (
                    <p className="muted">همه کارها انجام شده است.</p>
                  )}
                  <button className="text-button" onClick={() => navigate('calendar')}>
                    رفتن به تقویم
                    <ArrowLeft size={14} />
                  </button>
                </div>
              )}
            </div>
            <button
              className="icon-button topbar-help"
              aria-label="راهنمای پستینو"
              onClick={() => setModal({ kind: 'help' })}
            >
              <CircleHelp size={19} strokeWidth={1.7} />
            </button>
          </div>
        </header>
        <main className="main-content" id="main-content">
          {IS_STANDALONE && (
            <div className="demo-ribbon">
              <span>
                <span className="demo-dot" />
                نسخه مستقل و رایگان · اطلاعات فقط روی همین دستگاه
              </span>
              <button onClick={() => navigate('subscription')}>
                پشتیبان و تنظیمات
                <ArrowLeft size={13} />
              </button>
            </div>
          )}
          {!IS_STANDALONE && (!data.user || !!data.user.is_demo) && (
            <div className="demo-ribbon">
              <span>
                <span className="demo-dot" />
                فضای آزمایشی<span className="ribbon-separator">/</span>اطلاعات باغ و گزارش‌های
                اولیه، نمونه‌اند.
              </span>
              <button onClick={() => setModal({ kind: 'auth' })}>
                ورود به حساب واقعی
                <ArrowLeft size={13} />
              </button>
            </div>
          )}
          {page === 'dashboard' && <Dashboard ctx={ctx} />}
          {page === 'analysis' && (
            <Analysis
              ctx={ctx}
              initialFile={analysisInput.file}
              initialOrchard={analysisInput.orchard}
              key={analysisInput.key}
            />
          )}
          {page === 'orchards' && <Orchards ctx={ctx} />}
          {page === 'reports' && <Reports ctx={ctx} />}
          {page === 'calendar' && <CalendarPage ctx={ctx} />}
          {page === 'knowledge' && (
            <KnowledgePage ctx={ctx} initialSearch={knowledgeSearch} key={searchKey} />
          )}
          {page === 'subscription' &&
            (IS_STANDALONE ? <LocalSettings ctx={ctx} /> : <Subscription ctx={ctx} />)}
          {page === 'admin' && (IS_STANDALONE ? <LocalSettings ctx={ctx} /> : <Admin ctx={ctx} />)}
          <footer className="app-footer">
            <span>
              <Leaf size={13} />
              پستینو · با آگاهی، برای باغی ماندگار
            </span>
            <div>
              <span className="version-label">
                {IS_STANDALONE ? 'نسخه مستقل ۰.۱' : 'نسخه آزمایشی ۰.۱'}
              </span>
              <button onClick={() => setModal({ kind: 'privacy' })}>حریم خصوصی</button>
              <span>·</span>
              <button onClick={() => setModal({ kind: 'help' })}>راهنما</button>
            </div>
          </footer>
        </main>
      </div>
      <nav className="mobile-bottom-nav" aria-label="دسترسی سریع" inert={!!modal || sidebarOpen}>
        {[
          { id: 'dashboard' as const, title: 'پیشخوان', icon: Home },
          { id: 'analysis' as const, title: 'بررسی', icon: Sparkles },
          { id: 'orchards' as const, title: 'باغ‌ها', icon: Trees },
          { id: 'knowledge' as const, title: 'دانشنامه', icon: BookOpen },
        ].map((n) => (
          <button
            key={n.id}
            className={page === n.id ? 'active' : ''}
            onClick={() => navigate(n.id)}
          >
            <n.icon size={19} />
            <span>{n.title}</span>
          </button>
        ))}
        <button onClick={() => setSidebarOpen(true)}>
          <Menu size={19} />
          <span>بیشتر</span>
        </button>
      </nav>
      {modal?.kind === 'auth' && <AuthForm ctx={ctx} onClose={closeModal} />}{' '}
      {modal?.kind === 'orchard' && (
        <OrchardForm ctx={ctx} orchard={modal.orchard} onClose={closeModal} />
      )}{' '}
      {modal?.kind === 'task' && <TaskForm ctx={ctx} onClose={closeModal} />}{' '}
      {modal?.kind === 'article' && <ArticleDetail article={modal.article} onClose={closeModal} />}{' '}
      {modal?.kind === 'report' && (
        <ReportDetail ctx={ctx} report={modal.report} onClose={closeModal} />
      )}{' '}
      {(modal?.kind === 'help' || modal?.kind === 'privacy') && (
        <HelpModal onClose={closeModal} privacy={modal.kind === 'privacy'} />
      )}{' '}
      {modal?.kind === 'profile' && <ProfileModal ctx={ctx} onClose={closeModal} />}
      {toast && (
        <div className={`toast toast-${toast.type}`} role="status">
          {toast.type === 'success' ? (
            <Check size={19} />
          ) : toast.type === 'error' ? (
            <X size={19} />
          ) : (
            <Leaf size={18} />
          )}
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} aria-label="بستن پیام">
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  )
}
