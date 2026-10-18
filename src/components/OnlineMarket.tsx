import { useEffect, useRef, useState } from 'react'
import { ExternalLink, RefreshCw } from 'lucide-react'
import { cachedMarketQuotes, marketDate, refreshMarketQuotes, MARKET_SEARCH } from '../marketQuotes'
import type { MarketQuotes } from '../marketQuotes'
import { fa, persianDate } from '../api'
import { Badge, InfoBanner } from './ui'

export default function OnlineMarket() {
  const [quotes, setQuotes] = useState<MarketQuotes | null>(() => cachedMarketQuotes())
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [clock, setClock] = useState(() => new Date())
  const alive = useRef(false)
  const loading = useRef(false)
  const attempted = useRef(0)
  async function refresh(force = false) {
    if (loading.current || (!force && Date.now() - attempted.current < 1800000)) return
    attempted.current = Date.now()
    loading.current = true
    setBusy(true)
    setError('')
    try {
      const data = await refreshMarketQuotes()
      if (alive.current) {
        setQuotes(data)
        setClock(new Date())
      }
    } catch {
      if (alive.current)
        setError(
          'دریافت خودکار قیمت انجام نشد؛ اتصال یا دسترسی به منبع را بررسی کنید. دادهٔ ذخیره‌شده تازه نشده و قیمت امروز تأیید نشده است. در نسخهٔ وب ممکن است منبع اجازهٔ دسترسی مستقیم ندهد.'
        )
    } finally {
      loading.current = false
      if (alive.current) setBusy(false)
    }
  }
  useEffect(() => {
    alive.current = true
    const update = () => {
      if (document.visibilityState === 'hidden') return
      setClock(new Date())
      const cache = cachedMarketQuotes()
      if (
        !cache ||
        cache.report_date !== marketDate() ||
        Date.now() - Date.parse(cache.fetched_at) > 1800000
      )
        void refresh()
    }
    update()
    const interval = setInterval(update, 60000)
    const online = () => {
      if (document.visibilityState !== 'hidden') void refresh(true)
    }
    window.addEventListener('online', online)
    document.addEventListener('visibilitychange', update)
    return () => {
      alive.current = false
      clearInterval(interval)
      window.removeEventListener('online', online)
      document.removeEventListener('visibilitychange', update)
    }
  }, [])
  const isToday = quotes?.report_date === marketDate(clock)
  return (
    <section className="reference-card online-market" aria-label="دریافت خودکار نرخ پسته">
      <div className="section-title">
        <h2>نرخ‌های منتشرشدهٔ بازار</h2>
        <button
          className="button secondary small"
          disabled={busy}
          onClick={() => void refresh(true)}
        >
          <RefreshCw size={16} className={busy ? 'spin' : ''} />
          {busy ? 'در حال دریافت…' : 'به‌روزرسانی قیمت‌ها'}
        </button>
      </div>
      <p className="muted">
        هنگام باز بودن این صفحه، دریافت دوره‌ای از منبع خبری انجام می‌شود؛ بدون کلید تحلیل و بدون
        مصرف اعتبار. نرخ معاملهٔ قطعی باغ یا قیمت صادراتی نیست.
      </p>
      {error && <InfoBanner tone="warning">{error}</InfoBanner>}
      {quotes ? (
        <>
          <Badge tone={isToday && !error ? 'green' : 'amber'}>
            {isToday ? 'گزارش منتشرشدهٔ امروز؛ نه تأیید معامله' : 'گزارش قدیمی؛ نه قیمت امروز'}
          </Badge>
          <p>
            تاریخ گزارش: {persianDate(quotes.report_date, { year: 'numeric' })} · آخرین دریافت موفق:{' '}
            {persianDate(quotes.fetched_at, {
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
          {quotes.rows.map((row) => (
            <div className="online-price-row" key={row.cultivar}>
              <strong>{row.cultivar}</strong>
              <span>
                {fa(row.toman, 2)} تومان{row.weight_basis === 'kg' ? ' / کیلوگرم' : ''}
              </span>
              <small>
                درجه یک طبق عنوان جدول؛{' '}
                {row.weight_basis === 'kg'
                  ? 'وزن طبق منبع'
                  : 'مبنای وزن و اُنس در جدول منبع مشخص نیست'}
              </small>
            </div>
          ))}
          <p className="muted">
            اگر مبلغ منبع ریال باشد، فقط با تقسیم بر ۱۰ به تومان تبدیل می‌شود. منبع، قیمت مستقل برای
            باغ/اُنس شما یا نرخ ارز صادراتی ارائه نمی‌کند؛ تفاوت کیفیت و شرایط معامله را جدا بسنجید.
          </p>
          <a href={quotes.url} target="_blank" rel="noreferrer">
            منبع: {quotes.source} · مشاهدهٔ گزارش اصلی <ExternalLink size={14} />
          </a>
        </>
      ) : (
        <p>
          {busy
            ? 'در حال خواندن آخرین جدول دارای تاریخ و واحد مشخص…'
            : 'هنوز نرخ مستند خودکار دریافت نشده؛ عدد تخمینی نمایش داده نمی‌شود.'}
        </p>
      )}
      {!quotes && (
        <a href={MARKET_SEARCH} target="_blank" rel="noreferrer">
          باز کردن منبع اصلی قیمت‌ها <ExternalLink size={14} />
        </a>
      )}
    </section>
  )
}
