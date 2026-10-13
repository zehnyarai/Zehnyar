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
            نسخه آزمایشی پژوهش/رابط برای اندروید ۷ به بالا؛ نه نسخه نهایی تحلیل عکس. همه نسخه‌های
            ساخته‌شده و اطلاعات بررسی فایل در پوشه نصب قرار دارند.
          </p>
          <a
            className="button primary"
            href="https://raw.githubusercontent.com/zehnyarai/Zehnyar/arena/e819b607-zehnyar/installers/Pestino-0.6.2.apk"
            target="_blank"
            rel="noreferrer"
          >
            <Download size={18} />
            APK پستینو ۰.۳.۰ — آزمایش پژوهش و رابط
          </a>
          <p className="section-description">
            از APK قدیمی انتظار رابط جدید نداشته باشید؛ نام نسخه و اطلاعات ساخت همراه فایل را کنترل
            کنید. امضای آزمایشی، کلید ثابت فروشگاهی نیست.
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
