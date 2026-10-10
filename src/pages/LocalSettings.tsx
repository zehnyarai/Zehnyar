import { useRef, useState } from 'react'
import { Download, HardDrive, ShieldCheck, Trash2, Upload } from 'lucide-react'
import type { AppContext } from '../types'
import { errorMessage, fa, today } from '../api'
import { eraseLocalData, exportBackup, restoreBackup, validateBackup } from '../standalone'
import { saveTextFile } from '../files'
import { Badge, InfoBanner, PageTitle, Spinner } from '../components/ui'

export default function LocalSettings({ ctx }: { ctx: AppContext }) {
  const input = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [pending, setPending] = useState<string | null>(null)
  const [confirmErase, setConfirmErase] = useState(false)
  async function run(action: () => Promise<void>) {
    if (busy) return
    setBusy(true)
    try {
      await action()
    } catch (e) {
      ctx.notify(errorMessage(e), 'error')
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="ساده، مستقل و بدون هزینه"
        title="داده‌ها و پشتیبان"
        subtitle="حساب میزبانی، کارت بانکی یا اشتراک لازم نیست."
        action={<Badge tone="green">رایگان</Badge>}
      />
      <InfoBanner>
        <strong>اطلاعات فقط روی همین دستگاه ذخیره می‌شوند.</strong> حساب اینترنتی و همگام‌سازی
        ندارید. تشخیص هوشمند عکس و پرداخت واقعی در این نسخه غیرفعال‌اند.
      </InfoBanner>
      <section className="card local-settings-card">
        <h2>
          <HardDrive size={22} /> دفتر باغ شما
        </h2>
        <p>
          {fa(ctx.data.orchards.length)} باغ · {fa(ctx.data.reports.length)} عکس ·{' '}
          {fa(ctx.data.tasks.length)} یادآور
        </p>
        <p className="muted">
          با حذف برنامه یا پاک‌کردن داده‌های مرورگر، اطلاعات محلی از بین می‌روند. قبل از این کار،
          فایل پشتیبان بگیرید. بین گوشی‌ها انتقال خودکار انجام نمی‌شود.
        </p>
        <div className="local-settings-actions">
          <button
            className="button primary"
            disabled={busy}
            onClick={() =>
              void run(async () => {
                const saved = await saveTextFile(
                  `pestino-backup-${today()}.json`,
                  await exportBackup()
                )
                ctx.notify(
                  saved ? 'فایل پشتیبان آماده شد.' : 'ذخیره فایل لغو شد.',
                  saved ? 'success' : 'info'
                )
              })
            }
          >
            <Download size={17} /> دریافت پشتیبان
          </button>
          <button
            className="button secondary"
            disabled={busy}
            onClick={() => input.current?.click()}
          >
            <Upload size={17} /> بازگردانی پشتیبان
          </button>
          {busy && <Spinner />}
        </div>
        <input
          ref={input}
          hidden
          type="file"
          accept="application/json,.json"
          onChange={(e) => {
            const file = e.target.files?.[0]
            e.target.value = ''
            if (!file) return
            void run(async () => {
              if (file.size > 32 * 1024 * 1024)
                throw new Error('فایل باید کمتر از ۳۲ مگابایت باشد.')
              const content = await file.text()
              validateBackup(content)
              setPending(content)
            })
          }}
        />
        {pending !== null && (
          <div className="delete-confirm">
            <strong>اطلاعات فعلی با فایل پشتیبان جایگزین شود؟</strong>
            <p>ابتدا از داده‌های فعلی پشتیبان بگیرید. این کار ادغام نیست.</p>
            <button
              className="button primary small"
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await restoreBackup(pending)
                  await ctx.refresh()
                  setPending(null)
                  ctx.notify('اطلاعات از فایل پشتیبان بازگردانی شد.', 'success')
                })
              }
            >
              تأیید بازگردانی
            </button>
            <button
              className="button secondary small"
              disabled={busy}
              onClick={() => setPending(null)}
            >
              انصراف
            </button>
          </div>
        )}
      </section>
      <InfoBanner tone="warning">
        <ShieldCheck size={18} /> فایل پشتیبان شامل مشخصات باغ و عکس‌هاست و رمزگذاری نشده است؛ آن را
        در جای امن نگه دارید و عمومی منتشر نکنید. مطالب دانشنامه آموزشی‌اند و هنوز بازبینی علمی محلی
        نشده‌اند.
      </InfoBanner>
      <section className="card local-settings-card">
        <h2>پاک‌کردن اطلاعات همین دستگاه</h2>
        <p>اطلاعات حذف‌شده بدون فایل پشتیبان قابل بازیابی نیستند.</p>
        <button
          className="button danger ghost"
          disabled={busy}
          onClick={() => setConfirmErase(true)}
        >
          <Trash2 size={16} /> حذف همه داده‌های محلی
        </button>
        {confirmErase && (
          <div className="delete-confirm">
            <p>همه باغ‌ها، عکس‌ها، یادآورها و نشان‌ها پاک شوند؟</p>
            <button
              className="button danger small"
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await eraseLocalData()
                  await ctx.refresh()
                  setConfirmErase(false)
                  ctx.notify('اطلاعات محلی حذف شدند.')
                })
              }
            >
              تأیید حذف همه داده‌ها
            </button>
            <button
              className="button secondary small"
              disabled={busy}
              onClick={() => setConfirmErase(false)}
            >
              انصراف
            </button>
          </div>
        )}
      </section>
    </>
  )
}
