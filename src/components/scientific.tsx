import { BookOpen, ExternalLink, Leaf, ListChecks, ShieldCheck } from 'lucide-react'
import type { AppContext } from '../types'
import { careChecklist, LAB_SOURCES } from '../scientific'
import type { DiagnosticContext } from '../scientific'
import { CheckList, InfoBanner } from './ui'

export function SourceLinks() {
  return (
    <div className="scientific-sources">
      <h3>
        <BookOpen size={18} /> منابع و دامنه کاربرد
      </h3>
      {LAB_SOURCES.map((s) => (
        <div key={s.url}>
          <a href={s.url} target="_blank" rel="noreferrer">
            {s.title}
            <ExternalLink size={14} />
          </a>
          <p>{s.scope}</p>
        </div>
      ))}
      <small>مراجع برای مطالعه‌اند؛ ادعای تأیید علمی محلی یا بررسی زنده منبع نداریم.</small>
    </div>
  )
}
export function ScientificPlan({ context, ctx }: { context: DiagnosticContext; ctx: AppContext }) {
  const plan = careChecklist(context)
  return (
    <section className="reference-card scientific-plan">
      <h2>
        <ListChecks size={23} /> مسیر بررسی، مراقبت و کیفیت محصول
      </h2>
      <InfoBanner>
        <strong>این برنامه تحلیل تصویر نیست.</strong> از نشانه‌هایی که خودتان انتخاب کرده‌اید و
        راهنماهای آموزشی ساخته شده است؛ وجود آفت، بیماری یا کمبود را تأیید نمی‌کند.
      </InfoBanner>
      <div className="care-columns">
        <section>
          <h3>۱. ثبت شواهد و اقدام کم‌خطر</h3>
          <CheckList items={plan.immediate} />
        </section>
        <section>
          <h3>۲. مدیریت تلفیقی آفات (IPM)</h3>
          <CheckList items={plan.ipm} />
        </section>
        <section>
          <h3>۳. محصول بیشتر و باکیفیت‌تر</h3>
          <CheckList items={plan.yield} />
        </section>
        <section>
          <h3>۴. بررسی‌های تکمیلی</h3>
          <CheckList items={plan.tests} />
        </section>
      </div>
      <h3>
        <Leaf size={18} /> راهنماهای مرتبط با اطلاعات شما
      </h3>
      <div className="guide-chips">
        {ctx.knowledge.articles
          .filter((a) => plan.guides.includes(a.id))
          .map((a) => (
            <button key={a.id} onClick={() => ctx.openArticle(a)}>
              {a.title}
            </button>
          ))}
      </div>
      <div className="safety-note">
        <ShieldCheck size={18} />
        <p>
          شدت یا علت دقیق، دوز سم و کود، وضعیت ریشه و آفلاتوکسین از عکس تنها تعیین نمی‌شوند. خشکیدگی
          سریع، صمغ طوقه یا گسترش شدید علائم نیازمند بازدید کارشناس است. هیچ تضمین افزایش محصول یا
          نابودی کامل آفت ارائه نمی‌شود.
        </p>
      </div>
    </section>
  )
}
