import {
  ArrowLeft,
  BookOpen,
  Brain,
  Bug,
  CalendarDays,
  FileText,
  FlaskConical,
  Leaf,
  Shield,
  Sprout,
  TrendingUp,
  Trees,
  Users,
} from 'lucide-react'
import type { AppContext, Page } from '../types'
import { fa } from '../api'

const FEATURES = [
  {
    title: 'اسکن هوشمند آفت',
    text: 'ثبت عکس از همه بخش‌های درخت؛ بررسی شواهد، احتمال‌ها و اقدام بعدی با مدل بیناییِ متصل',
    icon: Bug,
    color: 'red',
    page: 'analysis',
  },
  {
    title: 'تحلیل خاک و آب',
    text: 'ورود نتایج آزمایشگاه، بررسی واحد و روش سنجش، محاسبات آب و راهنمای تصمیم‌گیری تغذیه',
    icon: FlaskConical,
    color: 'amber',
    page: 'laboratory',
  },
  {
    title: 'دیوار تجربه',
    text: 'تجارب عملی باغداران پسته — یاد بگیرید و تجربه خود را با زمینه و محدودیت‌هایش ثبت کنید',
    icon: Users,
    color: 'blue',
    page: 'community',
  },
  {
    title: 'بازار و اقلیم',
    text: 'ثبت قیمت پسته با منبع و تاریخ، مشاهدات آب‌وهوا و پیگیری خطرهای اقلیمی باغ',
    icon: TrendingUp,
    color: 'mint',
    page: 'market',
  },
] as const
export default function Dashboard({ ctx }: { ctx: AppContext }) {
  const shortcuts: { page: Page; title: string; description: string; icon: typeof Trees }[] = [
    {
      page: 'orchards',
      title: 'باغ‌های من',
      description: `${fa(ctx.data.orchards.length)} باغ ثبت‌شده`,
      icon: Trees,
    },
    {
      page: 'calendar',
      title: 'تقویم مراقبت',
      description: 'پایش، آبیاری و یادآورها',
      icon: CalendarDays,
    },
    {
      page: 'reports',
      title: 'پرونده‌های درخت',
      description: `${fa(ctx.data.reports.length)} عکس و گزارش`,
      icon: FileText,
    },
    {
      page: 'knowledge',
      title: 'دانشنامه پسته',
      description: `${fa(ctx.knowledge.articles.length)} راهنمای آموزشی با منبع`,
      icon: BookOpen,
    },
  ]
  return (
    <div className="reference-home">
      <section className="reference-hero">
        <div className="hero-label">
          <Leaf size={19} />
          پلتفرم هوشمند باغداری پسته
        </div>
        <h1>دستیار هوشمند باغداران پسته</h1>
        <p>بررسی آفت، تحلیل خاک، تبادل تجربه و رصد بازار</p>
        <strong>با شواهد، برای تصمیمی آگاهانه‌تر</strong>
        <div className="hero-actions">
          <button className="button primary" onClick={() => ctx.startAnalysis()}>
            شروع اسکن آفت
            <ArrowLeft size={19} />
          </button>
          <button className="button secondary" onClick={() => ctx.navigate('community')}>
            مشاهده تجارب
          </button>
        </div>
        <div className="hero-caption">
          <span className="tiny-dot" />
          پستینو · برای باغداران سراسر ایران
        </div>
      </section>
      <section className="reference-features" aria-label="امکانات پستینو">
        {FEATURES.map((f) => (
          <button className="reference-feature" key={f.page} onClick={() => ctx.navigate(f.page)}>
            <span className={`feature-icon ${f.color}`}>
              <f.icon size={29} />
            </span>
            <div>
              <h2>{f.title}</h2>
              <p>{f.text}</p>
            </div>
            <ArrowLeft className="feature-arrow" size={18} />
          </button>
        ))}
      </section>
      <section className="why-assistant">
        <header>
          <Shield size={29} />
          <h2>چرا این دستیار؟</h2>
        </header>
        <div>
          <Brain size={24} />
          <p>
            راهنماهای مراقبت با <strong>ارجاع به منابع آموزشی</strong> ارائه می‌شوند. مشاهدات،
            احتمال‌ها و داده‌های نیازمند آزمایش از هم جدا هستند؛ محتوا هنوز تأیید متخصص محلی ندارد.
          </p>
        </div>
        <div>
          <Shield size={24} />
          <p>
            به <strong>شفافیت</strong> پایبندیم — وضعیت اتصال مدل، منبع قیمت و محدودیت هر بررسی مشخص
            است؛ بدون داده واقعی، تشخیص یا درصد دقت ساختگی نشان نمی‌دهیم.
          </p>
        </div>
        <div>
          <Sprout size={24} />
          <p>
            از ثبت باغ تا پیگیری مراقبت، گرده‌افشانی، مدیریت آب و کیفیت برداشت؛{' '}
            <strong>نگاه به کل چرخه باغ</strong>، نه فقط یک عکس.
          </p>
        </div>
      </section>
      <section className="garden-shortcuts">
        <div className="home-section-heading">
          <span>
            <Leaf size={21} />
            <h2>دفتر و دانش باغ شما</h2>
          </span>
          <button className="text-button" onClick={() => ctx.navigate('knowledge')}>
            همه راهنماها
            <ArrowLeft size={16} />
          </button>
        </div>
        <div className="shortcut-grid">
          {shortcuts.map((s) => (
            <button key={s.page} onClick={() => ctx.navigate(s.page)}>
              <s.icon size={25} />
              <strong>{s.title}</strong>
              <span>{s.description}</span>
            </button>
          ))}
        </div>
      </section>
      <section className="home-reading">
        <div className="home-section-heading">
          <span>
            <BookOpen size={21} />
            <h2>از شناخت نشانه تا مراقبت درست</h2>
          </span>
        </div>
        <div className="home-guide-grid">
          {['sampling', 'psylla', 'nutrition', 'pollination', 'irrigation', 'harvest']
            .map((id) => ctx.knowledge.articles.find((a) => a.id === id))
            .filter((a) => !!a)
            .map((a) => (
              <button className="home-guide" key={a.id} onClick={() => ctx.openArticle(a)}>
                <span>{a.category_label}</span>
                <h3>{a.title}</h3>
                <p>{a.summary}</p>
                <small>
                  مطالعه راهنما
                  <ArrowLeft size={15} />
                </small>
              </button>
            ))}
        </div>
      </section>
    </div>
  )
}
