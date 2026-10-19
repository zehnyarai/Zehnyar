import { Info, Smartphone } from 'lucide-react'
import type { AppContext } from '../types'
import { InfoBanner } from '../components/ui'

export default function Install({ ctx }: { ctx: AppContext }) {
  return (
    <div className="reference-page install-page">
      <div className="reference-heading">
        <span className="feature-icon green">
          <Smartphone size={28} />
        </span>
        <div>
          <h1>نصب پستینو</h1>
          <p>فایل اندروید و راهنمای دسترسی آیفون؛ بدون معرفی وب‌اپ به‌عنوان IPA</p>
        </div>
      </div>
      <div className="install-cards">
        <section className="reference-card">
          <Smartphone size={34} />
          <h2>اندروید</h2>
          <p>
            نسخه ۰.۸.۱ برای اندروید ۷ به بالا: تحلیل عکس و تفسیر آزمایش، دو تحلیل رایگان و سپس بستهٔ
            تومانی، و همهٔ دفتر باغ به‌صورت آفلاین. راه‌اندازی تحلیل فقط از «پنل مدیر» انجام می‌شود.
          </p>
          <InfoBanner tone="warning">
            انتشار فایل نصب تازه تا آماده شدن امضای ثابت متوقف است. نسخهٔ آزمایشی ۰.۸.۱،
            به‌روزرسانیِ سازگار با همهٔ نصب‌های قبلی نیست؛ برای رفع اختلاف امضا برنامهٔ فعلی را حذف
            نکنید.
          </InfoBanner>
          <p className="section-description">
            کلیدهای قبلاً ذخیره‌شده روی همان نصب باقی می‌مانند. نیازی به ارسال دوبارهٔ کلیدهای سرویس
            تحلیل نیست. آماده شدن سازوکار امضای ثابت، به معنی بازیابی امضای تصادفی نسخه‌های قدیمی
            نیست.
          </p>
        </section>
        <section className="reference-card">
          <Smartphone size={34} />
          <h2>آیفون</h2>
          <p>
            فایل IPA امضاشده در دسترس نیست. این وب‌اپ در Safari قابل استفاده است؛ افزودن به صفحه
            اصلی، نصب اپ بومی iOS نیست.
          </p>
          <ol>
            <li>نشانی HTTPS فعال را در Safari باز کنید.</li>
            <li>گزینه Share را لمس کنید.</li>
            <li>Add to Home Screen و سپس Add را بزنید.</li>
          </ol>
          <InfoBanner>
            پیش‌نمایش موقت است؛ میزبانی دائمی و کار کاملاً آفلاین آیفون هنوز تأیید نشده‌اند.
          </InfoBanner>
        </section>
      </div>
      <InfoBanner tone="warning">
        <Info size={18} />
        <strong>پیش از تغییر نسخه، پشتیبان بگیرید.</strong> نسخه‌های آزمایشی ممکن است امضای متفاوت
        داشته باشند و روی هم نصب نشوند. برای رفع این خطا برنامه یا داده‌ها را حذف نکنید، حتی اگر
        پشتیبان گرفته‌اید.
        <button className="text-button" onClick={() => ctx.navigate('settings')}>
          داده‌ها و پشتیبان
        </button>
      </InfoBanner>
    </div>
  )
}
