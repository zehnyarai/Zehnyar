import { Download, Info, Smartphone } from 'lucide-react'
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
            نسخه ۰.۷.۵ برای اندروید ۷ به بالا: تحلیل عکس و تفسیر آزمایش، دو تحلیل رایگان و سپس بستهٔ
            تومانی، و همهٔ دفتر باغ به‌صورت آفلاین. راه‌اندازی تحلیل فقط از «پنل مدیر» انجام می‌شود.
          </p>
          <a
            className="button primary"
            href="https://raw.githubusercontent.com/zehnyarai/Zehnyar/arena/e819b607-zehnyar/installers/Pestino-0.7.5.apk"
            target="_blank"
            rel="noreferrer"
          >
            <Download size={18} />
            دانلود APK پستینو ۰.۷.۵
          </a>
          <p className="section-description">
            اندازه و SHA-256 هر نسخه در پوشهٔ نصب (`installers/`) و در `installers/BUILD.txt` است.
            امضا آزمایشی است و کلید فروشگاهی ثابت نیست؛ پیش از نصب نسخهٔ تازه پشتیبان بگیرید.
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
        داشته باشند و روی هم نصب نشوند. بدون پشتیبان برنامه یا داده‌ها را حذف نکنید.
        <button className="text-button" onClick={() => ctx.navigate('settings')}>
          داده‌ها و پشتیبان
        </button>
      </InfoBanner>
    </div>
  )
}
