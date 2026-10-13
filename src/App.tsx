import { useCallback, useEffect, useState } from 'react'
import {
  ArrowLeft,
  BookOpen,
  Bug,
  CalendarDays,
  Check,
  ChevronDown,
  Download,
  FileText,
  FlaskConical,
  Home,
  Leaf,
  LogOut,
  Menu,
  ShieldCheck,
  TrendingUp,
  Trees,
  UserRound,
  Users,
  Wallet,
  X,
} from 'lucide-react'
import { IS_STANDALONE } from './config'
import { api, errorMessage, fa } from './api'
import type { AppContext, Article, Bootstrap, Knowledge, Orchard, Page, Report } from './types'
import { Logo, Spinner } from './components/ui'
import { AuthForm, OrchardForm, ProfileModal, TaskForm } from './components/forms'
import { ArticleDetail, HelpModal, ReportDetail } from './components/details'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Laboratory from './pages/Laboratory'
import Community from './pages/Community'
import Market from './pages/Market'
import Credits from './pages/Credits'
import CreditAdmin from './pages/CreditAdmin'
import Install from './pages/Install'
import Orchards from './pages/Orchards'
import Reports from './pages/Reports'
import CalendarPage from './pages/Calendar'
import KnowledgePage from './pages/Knowledge'
import LocalSettings from './pages/LocalSettings'
import Admin from './pages/Admin'

const paths: Record<Page, string> = {
  dashboard: '/',
  analysis: '/analysis',
  laboratory: '/laboratory',
  community: '/community',
  market: '/market',
  subscription: '/subscription',
  admin: '/admin',
  orchards: '/orchards',
  reports: '/reports',
  calendar: '/calendar',
  knowledge: '/knowledge',
  settings: '/settings',
  install: '/install',
}
const NAV = [
  { id: 'dashboard', label: 'خانه', icon: Home },
  { id: 'analysis', label: 'اسکن آفت', icon: Bug },
  { id: 'laboratory', label: 'تحلیل خاک و آب', icon: FlaskConical },
  { id: 'community', label: 'دیوار تجربه', icon: Users },
  { id: 'market', label: 'بازار و اقلیم', icon: TrendingUp },
  { id: 'subscription', label: 'اعتبار من', icon: Wallet },
  { id: 'admin', label: 'پنل مدیر', icon: ShieldCheck },
] as const
const TOOLS = [
  { id: 'orchards', label: 'باغ‌های من', icon: Trees },
  { id: 'reports', label: 'پرونده‌ها و عکس‌ها', icon: FileText },
  { id: 'calendar', label: 'تقویم مراقبت', icon: CalendarDays },
  { id: 'knowledge', label: 'دانشنامه پسته', icon: BookOpen },
  { id: 'settings', label: 'داده‌ها و پشتیبان', icon: Download },
] as const
function pageFromPath() {
  return (
    (Object.entries(paths).find(
      ([, path]) => path === (IS_STANDALONE ? location.hash.slice(1) || '/' : location.pathname)
    )?.[0] as Page | undefined) ?? 'dashboard'
  )
}
type ModalState =
  | { kind: 'auth' | 'task' | 'help' | 'privacy' | 'profile' }
  | { kind: 'orchard'; orchard?: Orchard }
  | { kind: 'article'; article: Article }
  | { kind: 'report'; report: Report }
let initialRequest: Promise<[Bootstrap, Knowledge]> | null = null
function initialize() {
  return (initialRequest ??= Promise.all([
    api<Bootstrap>('/bootstrap'),
    api<Knowledge>('/knowledge'),
  ]).finally(() => {
    initialRequest = null
  }))
}

export default function App() {
  const [data, setData] = useState<Bootstrap | null>(null),
    [knowledge, setKnowledge] = useState<Knowledge | null>(null)
  const [page, setPage] = useState<Page>(pageFromPath),
    [bootError, setBootError] = useState(''),
    [attempt, setAttempt] = useState(0)
  const [modal, setModal] = useState<ModalState | null>(null),
    [menu, setMenu] = useState(false),
    [tools, setTools] = useState(false)
  const [signingOut, setSigningOut] = useState(false)
  const [adminTab, setAdminTab] = useState('receipts')
  const [analysisInput, setAnalysisInput] = useState<{
    file?: File
    orchard?: string
    key: number
  }>({ key: 0 })
  const [toast, setToast] = useState<{
    message: string
    type: 'success' | 'error' | 'info'
  } | null>(null)
  const closeModal = useCallback(() => setModal(null), [])
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
      setMenu(false)
      setTools(false)
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
    const timer = setTimeout(() => setToast(null), 6500)
    return () => clearTimeout(timer)
  }, [toast])
  const refresh = useCallback(async () => {
    setData(await api<Bootstrap>('/bootstrap'))
  }, [])
  const navigate = useCallback((next: Page) => {
    setPage(next)
    setMenu(false)
    setTools(false)
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
  async function logout() {
    setSigningOut(true)
    try {
      await api('/auth/logout', { method: 'POST' })
      await refresh()
      navigate('dashboard')
      notify('از حساب خارج شدید.')
    } catch (e) {
      notify(errorMessage(e), 'error')
    } finally {
      setSigningOut(false)
    }
  }
  if (!data || !knowledge)
    return (
      <div className="boot-screen">
        <Logo />
        {bootError ? (
          <>
            <h1>پستینو آماده نشد</h1>
            <p>{bootError}</p>
            <button className="button primary" onClick={() => setAttempt((a) => a + 1)}>
              تلاش دوباره
            </button>
          </>
        ) : (
          <Spinner label="در حال آماده‌کردن پستینو…" />
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
    openAuth: () =>
      IS_STANDALONE
        ? notify('نسخه مستقل حساب سروری ندارد؛ اطلاعات روی دستگاه ذخیره می‌شوند.')
        : setModal({ kind: 'auth' }),
    openOrchard: (orchard) => setModal({ kind: 'orchard', orchard }),
    openTask: () => setModal({ kind: 'task' }),
    startAnalysis,
  }
  return (
    <div className="reference-app">
      <a className="skip-link" href="#main-content">
        رفتن به محتوای صفحه
      </a>
      <header className="reference-header" inert={!!modal}>
        <div className="reference-header-inner">
          <a
            className="reference-brand"
            href={IS_STANDALONE ? '#/' : '/'}
            onClick={(e) => {
              e.preventDefault()
              navigate('dashboard')
            }}
            aria-label="صفحه اصلی پستینو"
          >
            <span className="reference-brand-mark">
              <Leaf size={28} />
            </span>
            <span>
              <strong>دستیار هوشمند باغداران پسته</strong>
              <small>
                پستینو <span lang="en">/ Pestino</span>
              </small>
            </span>
          </a>
          <button
            className="icon-button reference-menu-button"
            aria-label="باز کردن منو"
            aria-expanded={menu}
            aria-controls="reference-navigation"
            onClick={() => setMenu(!menu)}
          >
            {menu ? <X size={23} /> : <Menu size={23} />}
          </button>
          <nav
            className={`reference-navigation ${menu ? 'is-open' : ''}`}
            aria-label="منوی اصلی"
            id="reference-navigation"
          >
            {NAV.map((n) => (
              <a
                key={n.id}
                className={page === n.id ? 'is-active' : ''}
                href={IS_STANDALONE ? `#${paths[n.id]}` : paths[n.id]}
                aria-current={page === n.id ? 'page' : undefined}
                onClick={(e) => {
                  e.preventDefault()
                  navigate(n.id)
                }}
              >
                <n.icon size={17} />
                <span>{n.label}</span>
              </a>
            ))}
          </nav>
          <div className="reference-header-actions">
            <button className="button install-outline" onClick={() => navigate('install')}>
              <Download size={17} />
              نصب اپ
            </button>
            <button
              className="credit-pill"
              onClick={() => navigate('subscription')}
              aria-label="اعتبار من"
            >
              <Wallet size={17} />
              {IS_STANDALONE ? 'رایگان' : fa(data.credit_balance ?? 0)}
            </button>
            <button
              className="icon-button account-button"
              onClick={() =>
                IS_STANDALONE
                  ? navigate('settings')
                  : setModal({ kind: !data.user || data.user.is_demo ? 'auth' : 'profile' })
              }
              aria-label="حساب و تنظیمات"
            >
              <UserRound size={19} />
              <span className="reference-account-name">
                {IS_STANDALONE
                  ? 'داده‌ها'
                  : !data.user || data.user.is_demo
                    ? 'ورود'
                    : data.user.name}
              </span>
            </button>
            {!IS_STANDALONE && data.user && !data.user.is_demo && (
              <button
                className="icon-button"
                aria-label="خروج از حساب"
                title="خروج از حساب"
                disabled={signingOut}
                onClick={() => void logout()}
              >
                <LogOut size={18} />
              </button>
            )}
          </div>
        </div>
      </header>
      <div className="reference-toolsbar" inert={!!modal}>
        <div>
          <span>همراه باغ شما</span>
          <button className="tools-toggle" aria-expanded={tools} onClick={() => setTools(!tools)}>
            دفتر باغ و دانشنامه
            <ChevronDown size={15} />
          </button>
          <div className={`reference-tools ${tools ? 'tools-open' : ''}`}>
            {TOOLS.map((n) => (
              <button
                key={n.id}
                className={page === n.id ? 'active' : ''}
                onClick={() => navigate(n.id)}
              >
                <n.icon size={15} />
                {n.label}
              </button>
            ))}
          </div>
          <span
            className={`connection-status ${data.services.vision_configured ? 'connected' : ''}`}
          >
            <span />
            {data.services.vision_configured ? 'مدل بینایی تنظیم شده' : 'تحلیل تصویر: متصل نیست'}
          </span>
        </div>
      </div>
      <main
        className={`reference-main ${page === 'dashboard' ? 'home-main' : ''}`}
        id="main-content"
        inert={!!modal}
      >
        {!IS_STANDALONE && (!data.user || !!data.user.is_demo) && (
          <div className="demo-ribbon">
            <span>فضای آزمایشی؛ داده‌های باغ اولیه نمونه‌اند.</span>
            <button onClick={() => setModal({ kind: 'auth' })}>
              ورود به حساب واقعی
              <ArrowLeft size={14} />
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
        {page === 'laboratory' && <Laboratory ctx={ctx} />}
        {page === 'community' && <Community ctx={ctx} />}
        {page === 'market' && <Market ctx={ctx} />}
        {page === 'subscription' && <Credits ctx={ctx} />}
        {page === 'admin' && (
          <>
            <div className="admin-view-tabs">
              <button
                className={adminTab === 'receipts' ? 'active' : ''}
                onClick={() => setAdminTab('receipts')}
              >
                رسیدها و اعتبار
              </button>
              {!IS_STANDALONE && (
                <button
                  className={adminTab === 'services' ? 'active' : ''}
                  onClick={() => setAdminTab('services')}
                >
                  سرویس‌ها و درگاه
                </button>
              )}
            </div>
            {adminTab === 'receipts' ? <CreditAdmin ctx={ctx} /> : <Admin ctx={ctx} />}
          </>
        )}
        {page === 'orchards' && <Orchards ctx={ctx} />}
        {page === 'reports' && <Reports ctx={ctx} />}
        {page === 'calendar' && <CalendarPage ctx={ctx} />}
        {page === 'knowledge' && <KnowledgePage ctx={ctx} />}
        {page === 'settings' &&
          (IS_STANDALONE ? (
            <LocalSettings ctx={ctx} />
          ) : (
            <div className="reference-card online-settings">
              <h1>حساب و داده‌های شما</h1>
              <p>
                در نسخه سروری، داده‌ها در حساب ذخیره می‌شوند. پرونده‌های تصویر و خروجی گزارش از بخش
                پرونده‌ها در دسترس‌اند.
              </p>
              <button className="button primary" onClick={() => navigate('reports')}>
                پرونده‌های من
              </button>
              <button
                className="button secondary"
                onClick={() =>
                  setModal({ kind: !data.user || data.user.is_demo ? 'auth' : 'profile' })
                }
              >
                حساب کاربری
              </button>
            </div>
          ))}
        {page === 'install' && <Install ctx={ctx} />}
      </main>
      <footer className="reference-footer" inert={!!modal}>
        <div>
          <span>
            <Leaf size={19} />
            <strong>پستینو</strong> · با آگاهی، برای باغی ماندگار
          </span>
          <p>
            {IS_STANDALONE
              ? 'ذخیره محلی · بدون همگام‌سازی · پرداخت غیرفعال'
              : 'نسخه سروری آزمایشی · وضعیت سرویس‌ها را بررسی کنید'}
          </p>
        </div>
        <div>
          <span>نسخه آزمایشی ۰.۶</span>
          <button onClick={() => setModal({ kind: 'privacy' })}>حریم خصوصی</button>
          <button onClick={() => setModal({ kind: 'help' })}>راهنما</button>
        </div>
      </footer>
      {modal?.kind === 'auth' && <AuthForm ctx={ctx} onClose={closeModal} />}
      {modal?.kind === 'orchard' && (
        <OrchardForm ctx={ctx} orchard={modal.orchard} onClose={closeModal} />
      )}
      {modal?.kind === 'task' && <TaskForm ctx={ctx} onClose={closeModal} />}
      {modal?.kind === 'article' && <ArticleDetail article={modal.article} onClose={closeModal} />}
      {modal?.kind === 'report' && (
        <ReportDetail ctx={ctx} report={modal.report} onClose={closeModal} />
      )}
      {(modal?.kind === 'help' || modal?.kind === 'privacy') && (
        <HelpModal onClose={closeModal} privacy={modal.kind === 'privacy'} />
      )}
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
