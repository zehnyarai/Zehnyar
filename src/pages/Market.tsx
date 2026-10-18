import { useState } from 'react'
import { CloudSun, Plus, Thermometer, Trash2, TrendingUp, Wind } from 'lucide-react'
import type { AppContext } from '../types'
import type { FieldRecord, MarketInput } from '../fieldwork'
import { CULTIVARS, validateField, parseMarketNumber } from '../fieldwork'
import OnlineMarket from '../components/OnlineMarket'
import { errorMessage, fa, persianDate, today } from '../api'
import { useFieldRecords } from '../useFieldRecords'
import { Badge, InfoBanner, Modal, Spinner } from '../components/ui'

export default function Market({ ctx }: { ctx: AppContext }) {
  const prices = useFieldRecords('prices'),
    climate = useFieldRecords('climate')
  const [tab, setTab] = useState('prices'),
    [modal, setModal] = useState<'price' | 'climate' | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  const [price, setPrice] = useState({
    cultivar: 'احمدآقایی',
    price: '',
    currency: 'toman',
    province: '',
    source: '',
    observed_date: today(),
    grade: '',
  })
  const [weather, setWeather] = useState({
    province: '',
    observed_date: today(),
    minimum: '',
    maximum: '',
    humidity: '',
    wind: '',
    stage: '',
    source: '',
  })
  const ordered = [...prices.records].sort(
    (a, b) =>
      b.data.observed_date.localeCompare(a.data.observed_date) ||
      b.created_at.localeCompare(a.created_at)
  )
  const domestic = ordered.find((r) => r.data.currency === 'toman'),
    exported = ordered.find((r) => r.data.currency === 'usd')
  const latestByVariety = ordered.filter(
    (r, i, all) =>
      all.findIndex(
        (x) =>
          x.data.cultivar === r.data.cultivar &&
          x.data.currency === r.data.currency &&
          x.data.province === r.data.province &&
          x.data.grade === r.data.grade
      ) === i
  )
  function open(kind: 'price' | 'climate') {
    setModal(kind)
    setError('')
  }
  async function save() {
    setError('')
    try {
      if (modal === 'price') {
        if (!price.price.trim()) throw new Error('قیمت مشاهده‌شده را وارد کنید.')
        const data = validateField('prices', { ...price, price: parseMarketNumber(price.price) })
        setBusy(true)
        await prices.save(data)
      } else {
        if (!weather.minimum.trim() || !weather.maximum.trim())
          throw new Error('کمینه و بیشینه دما را وارد کنید.')
        const data = validateField('climate', {
          ...weather,
          minimum: parseMarketNumber(weather.minimum),
          maximum: parseMarketNumber(weather.maximum),
          humidity: weather.humidity === '' ? null : parseMarketNumber(weather.humidity),
          wind: weather.wind === '' ? null : parseMarketNumber(weather.wind),
        })
        setBusy(true)
        await climate.save(data)
      }
      setModal(null)
      ctx.notify('مشاهده شما با منبع و تاریخ ثبت شد؛ داده زنده تأییدشده نیست.', 'success')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }
  function priceCard(record: FieldRecord<'prices'> | undefined, title: string) {
    const previous =
      record &&
      ordered.find(
        (r) =>
          r.id !== record.id &&
          r.data.observed_date < record.data.observed_date &&
          ['cultivar', 'currency', 'province', 'grade', 'source'].every(
            (k) => r.data[k as keyof MarketInput] === record.data[k as keyof MarketInput]
          )
      )
    return (
      <section className="reference-card market-summary">
        <span>
          {title}
          {record && ` (${record.data.cultivar})`}
        </span>
        <div>
          <strong>{record ? fa(record.data.price, 2) : '—'}</strong>
          <small>{record?.data.currency === 'usd' ? 'دلار/کیلوگرم' : 'تومان/کیلوگرم'}</small>
        </div>
        {record ? (
          <>
            <p>
              منبع: {record.data.source} · {record.data.province}
            </p>
            {previous && (
              <p className="price-change">
                تغییر دو مشاهده هم‌مشخصات:{' '}
                {fa(((record.data.price - previous.data.price) / previous.data.price) * 100)}٪
              </p>
            )}
            <small>
              تاریخ مشاهده: {persianDate(record.data.observed_date, { year: 'numeric' })}
            </small>
          </>
        ) : (
          <p>قیمت واقعی هنوز وارد نشده؛ عدد نمایشی تولید نمی‌شود.</p>
        )}
      </section>
    )
  }
  return (
    <>
      <div className="reference-page market-page" inert={!!modal}>
        <div className="reference-heading">
          <span className="feature-icon mint">
            <TrendingUp size={29} />
          </span>
          <div>
            <h1>بازار و اقلیم</h1>
            <p>نرخ‌های منتشرشده با منبع و تاریخ، کنار مشاهده‌های شخصی باغ</p>
          </div>
        </div>
        <div className="reference-tabs" role="tablist" aria-label="بازار و اقلیم">
          <button
            role="tab"
            aria-selected={tab === 'prices'}
            className={tab === 'prices' ? 'active' : ''}
            onClick={() => setTab('prices')}
          >
            <TrendingUp size={18} />
            بازار پسته
          </button>
          <button
            role="tab"
            aria-selected={tab === 'weather'}
            className={tab === 'weather' ? 'active' : ''}
            onClick={() => setTab('weather')}
          >
            <Thermometer size={18} />
            اقلیم و هشدار
          </button>
        </div>
        {tab === 'prices' ? (
          <>
            <OnlineMarket />
            <div className="market-summaries">
              {priceCard(domestic, 'قیمت داخلی ثبت‌شده')}
              {priceCard(exported, 'قیمت صادراتی ثبت‌شده')}
            </div>
            <section className="reference-card market-prices">
              <header>
                <h2>قیمت ارقام مختلف</h2>
                <button className="button primary small" onClick={() => open('price')}>
                  <Plus size={17} />
                  ثبت قیمت
                </button>
              </header>
              <p className="section-description">
                با رقم، درجه، منطقه و تاریخ مقایسه کنید؛ همه قیمت‌ها بر حسب یک کیلوگرم‌اند.
              </p>
              {prices.error && <InfoBanner tone="warning">{prices.error}</InfoBanner>}
              {prices.loading ? (
                <Spinner />
              ) : latestByVariety.length ? (
                latestByVariety.map((r) => (
                  <div className="price-row" key={r.id}>
                    <span>
                      <strong>{r.data.cultivar}</strong>
                      <small>
                        {r.data.grade || 'درجه نامشخص'} · {r.data.province} ·{' '}
                        {persianDate(r.data.observed_date)}
                      </small>
                    </span>
                    <strong>
                      {fa(r.data.price, 2)} {r.data.currency === 'usd' ? 'دلار' : 'تومان'}
                    </strong>
                    <button
                      className="icon-button"
                      aria-label="حذف قیمت"
                      onClick={() => {
                        if (confirm('این مشاهده قیمت حذف شود؟'))
                          void prices
                            .remove(r.id)
                            .catch((e) => ctx.notify(errorMessage(e), 'error'))
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              ) : (
                <div className="empty-inline">
                  <TrendingUp size={35} />
                  <p>هنوز قیمت مستندی ثبت نکرده‌اید.</p>
                </div>
              )}
            </section>
          </>
        ) : (
          <section className="reference-card climate-card">
            <header>
              <h2>
                <CloudSun size={25} />
                مشاهدات اقلیمی و هشدارهای زمینه‌ای
              </h2>
              <button className="button primary small" onClick={() => open('climate')}>
                <Plus size={17} />
                ثبت وضعیت هوا
              </button>
            </header>
            {climate.error && <InfoBanner tone="warning">{climate.error}</InfoBanner>}
            {climate.loading ? (
              <Spinner />
            ) : !climate.records.length ? (
              <div className="empty-inline">
                <CloudSun size={43} />
                <p>هنوز داده‌ای از هوای باغ ثبت نشده است.</p>
                <p>برای تصمیم حساس، هشدار رسمی هواشناسی و دمای واقعی داخل باغ را بررسی کنید.</p>
              </div>
            ) : (
              climate.records.map((r) => (
                <article className="climate-observation" key={r.id}>
                  <header>
                    <div>
                      <h3>{r.data.province}</h3>
                      <small>
                        {persianDate(r.data.observed_date, { year: 'numeric' })} · منبع:{' '}
                        {r.data.source}
                      </small>
                    </div>
                    <Badge tone="gray">مشاهده دستی، نه پیش‌بینی</Badge>
                    <button
                      className="icon-button"
                      aria-label="حذف مشاهده هوا"
                      onClick={() => {
                        if (confirm('مشاهده هوا حذف شود؟'))
                          void climate
                            .remove(r.id)
                            .catch((e) => ctx.notify(errorMessage(e), 'error'))
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </header>
                  <div className="weather-readings">
                    <span>
                      <Thermometer size={19} />
                      {fa(r.data.minimum)} تا {fa(r.data.maximum)} °C
                    </span>
                    {r.data.humidity !== null && <span>رطوبت {fa(r.data.humidity)}٪</span>}
                    {r.data.wind !== null && (
                      <span>
                        <Wind size={18} />
                        باد {fa(r.data.wind)} km/h
                      </span>
                    )}
                  </div>
                  <details className="climate-details">
                    <summary>توضیح و هشدارهای این مشاهده</summary>
                    <ul className="climate-notes">
                      {r.data.minimum <= 0 && (
                        <li>
                          دمای زیر یا نزدیک نقطه انجماد ثبت شده است؛ آسیب به مرحله رشد، مدت سرما و
                          دمای واقعی بافت وابسته است. هشدار رسمی و بازدید باغ را پیگیری کنید؛ حفاظت
                          پرخطر یا آتش‌افروزی پیشنهاد نمی‌شود.
                        </li>
                      )}
                      {r.data.maximum >= 40 && (
                        <li>
                          گرمای بالا ثبت شده؛ وضعیت رطوبت ریشه و یکنواختی آبیاری را بررسی کنید.
                          آبیاری بیشتر بدون شناخت زهکشی راهکار قطعی نیست.
                        </li>
                      )}
                      {r.data.humidity !== null && r.data.humidity >= 80 && (
                        <li>
                          رطوبت زیاد می‌تواند همراه خیس‌ماندن برگ باشد؛ پایش لکه‌ها و زمان خشک‌شدن
                          تاج مهم است، اما این عدد وجود بیماری را ثابت نمی‌کند.
                        </li>
                      )}
                      <li>
                        این قواعد غربالگری آموزشی و عمومی‌اند؛ خطر واقعی باید با مرحله رشد (
                        {r.data.stage || 'نامشخص'})، مدت رخداد و نظر کارشناس بررسی شود.
                      </li>
                    </ul>
                  </details>
                  <button
                    className="text-button"
                    onClick={() => {
                      const article = ctx.knowledge.articles.find((a) => a.id === 'frost')
                      if (article) ctx.openArticle(article)
                    }}
                  >
                    راهنمای تنش سرما و گرما
                  </button>
                </article>
              ))
            )}
          </section>
        )}
      </div>
      {modal && (
        <Modal
          title={modal === 'price' ? 'ثبت قیمت مشاهده‌شده پسته' : 'ثبت مشاهده آب‌وهوا'}
          subtitle="منبع و تاریخ واقعی را وارد کنید؛ این داده‌ها خودکار تأیید نمی‌شوند."
          onClose={() => {
            if (!busy) setModal(null)
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
              {modal === 'price' ? (
                <>
                  <label>
                    رقم پسته
                    <select
                      value={price.cultivar}
                      onChange={(e) => setPrice((p) => ({ ...p, cultivar: e.target.value }))}
                    >
                      {CULTIVARS.map((c) => (
                        <option key={c}>{c}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    قیمت هر کیلوگرم *
                    <input
                      type="text"
                      inputMode="decimal"
                      maxLength={30}
                      min="0.01"
                      max="1000000000"
                      step="any"
                      required
                      value={price.price}
                      onChange={(e) => setPrice((p) => ({ ...p, price: e.target.value }))}
                    />
                  </label>
                  <label>
                    واحد قیمت
                    <select
                      value={price.currency}
                      onChange={(e) => setPrice((p) => ({ ...p, currency: e.target.value }))}
                    >
                      <option value="toman">تومان</option>
                      <option value="usd">دلار آمریکا</option>
                    </select>
                  </label>
                  <label>
                    استان / بازار *
                    <input
                      required
                      value={price.province}
                      minLength={2}
                      maxLength={60}
                      onChange={(e) => setPrice((p) => ({ ...p, province: e.target.value }))}
                    />
                  </label>
                  <label>
                    نوع، اُنس و درجه محصول
                    <input
                      value={price.grade}
                      maxLength={120}
                      placeholder="مثلاً خشک با پوست؛ اُنس، خندان یا بسته"
                      onChange={(e) => setPrice((p) => ({ ...p, grade: e.target.value }))}
                    />
                  </label>
                  <label>
                    تاریخ مشاهده *
                    <input
                      required
                      type="date"
                      value={price.observed_date}
                      onChange={(e) => setPrice((p) => ({ ...p, observed_date: e.target.value }))}
                    />
                  </label>
                  <label className="span-all">
                    منبع قیمت *
                    <input
                      required
                      value={price.source}
                      minLength={3}
                      maxLength={300}
                      placeholder="نام بازار، گزارش یا معامله واقعی؛ بدون شماره تماس شخصی"
                      onChange={(e) => setPrice((p) => ({ ...p, source: e.target.value }))}
                    />
                  </label>
                </>
              ) : (
                <>
                  <label>
                    استان / محل باغ *
                    <input
                      required
                      minLength={2}
                      maxLength={60}
                      value={weather.province}
                      onChange={(e) => setWeather((w) => ({ ...w, province: e.target.value }))}
                    />
                  </label>
                  <label>
                    تاریخ مشاهده *
                    <input
                      required
                      type="date"
                      value={weather.observed_date}
                      onChange={(e) => setWeather((w) => ({ ...w, observed_date: e.target.value }))}
                    />
                  </label>
                  {(['minimum', 'maximum', 'humidity', 'wind'] as const).map((k) => (
                    <label key={k}>
                      {
                        {
                          minimum: 'کمینه دما (°C) *',
                          maximum: 'بیشینه دما (°C) *',
                          humidity: 'رطوبت نسبی (%)',
                          wind: 'سرعت باد (km/h)',
                        }[k]
                      }
                      <input
                        type="text"
                        inputMode="decimal"
                        maxLength={30}
                        step="any"
                        required={k === 'minimum' || k === 'maximum'}
                        min={k === 'minimum' || k === 'maximum' ? -60 : 0}
                        max={k === 'humidity' ? 100 : k === 'wind' ? 300 : 65}
                        value={weather[k]}
                        onChange={(e) => setWeather((w) => ({ ...w, [k]: e.target.value }))}
                      />
                    </label>
                  ))}
                  <label>
                    مرحله رشد
                    <input
                      value={weather.stage}
                      maxLength={60}
                      placeholder="مثلاً گل‌دهی"
                      onChange={(e) => setWeather((w) => ({ ...w, stage: e.target.value }))}
                    />
                  </label>
                  <label>
                    منبع داده *
                    <input
                      required
                      minLength={3}
                      maxLength={300}
                      value={weather.source}
                      placeholder="مثلاً دماسنج باغ؛ گزارش رسمی با زمان"
                      onChange={(e) => setWeather((w) => ({ ...w, source: e.target.value }))}
                    />
                  </label>
                </>
              )}
            </div>
            {error && (
              <div className="form-error" role="alert">
                {error}
              </div>
            )}
            <div className="modal-actions">
              <button className="button primary" type="submit" disabled={busy}>
                {busy ? <Spinner /> : 'ثبت مشاهده'}
              </button>
              <button
                type="button"
                className="button secondary"
                disabled={busy}
                onClick={() => setModal(null)}
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
