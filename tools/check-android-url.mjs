const value = process.env.CAPACITOR_SERVER_URL
let valid = false
try {
  const url = new URL(value)
  valid = url.protocol === 'https:' && !url.username && !url.password && !url.search && !url.hash && url.pathname === '/' && !['localhost', '127.0.0.1', '::1', '[::1]'].includes(url.hostname) && !url.hostname.endsWith('.e2b.app')
} catch {}
if (!valid) {
  console.error('ساخت نسخه آنلاین اندروید نیاز به CAPACITOR_SERVER_URL با دامنه HTTPS واقعی در ریشه سایت دارد. بدون سرور منتشرشده، نسخه قابل انتشار نیست. هیچ کلید محرمانه‌ای در این نشانی قرار ندهید.')
  process.exit(1)
}
