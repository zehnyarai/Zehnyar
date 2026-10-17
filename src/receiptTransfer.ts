/** Explicit file exchange, NOT a simulated server inbox or proof of bank payment. */
import { capturePhoto, previewUrl } from './photoCapture'
import { validateReceipt, validateReceiptImage } from './localAdmin'
import type { LocalReceipt } from './localAdmin'

export const RECEIPT_LIMIT = 2_200_000

/** Decode a copied image and re-encode JPEG; camera EXIF/location never leaves the device. */
export async function prepareReceiptImage(file: File): Promise<string> {
  const photo = await capturePhoto(file)
  const url = previewUrl(photo)
  try {
    const image = new Image()
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve()
      image.onerror = () => reject(new Error('عکس فیش باز نشد؛ عکس دیگری انتخاب کنید.'))
      image.src = url
    })
    if (
      !image.naturalWidth ||
      !image.naturalHeight ||
      image.naturalWidth * image.naturalHeight > 40_000_000
    )
      throw new Error('ابعاد عکس فیش بیش از حد بزرگ است؛ عکس کوچک‌تری انتخاب کنید.')
    const scale = Math.min(1, 1600 / Math.max(image.naturalWidth, image.naturalHeight))
    const canvas = document.createElement('canvas')
    canvas.width = Math.max(1, Math.round(image.naturalWidth * scale))
    canvas.height = Math.max(1, Math.round(image.naturalHeight * scale))
    const context = canvas.getContext('2d')
    if (!context) throw new Error('آماده‌کردن عکس روی این دستگاه ممکن نشد.')
    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0, canvas.width, canvas.height)
    return validateReceiptImage(canvas.toDataURL('image/jpeg', 0.84))
  } finally {
    URL.revokeObjectURL(url)
  }
}

/** Export only the receipt, not keys, orchard data, credits or an approval supplied by a user. */
export function receiptPacket(row: LocalReceipt): string {
  if (!row.image_data) throw new Error('برای ارسال، عکس فیش را انتخاب کنید.')
  return JSON.stringify({
    format: 'pestino-receipt',
    version: 1,
    receipt: {
      ...validateReceipt(row),
      id: row.id,
      created_at: row.created_at,
    },
  })
}

export function parseReceiptPacket(content: string): LocalReceipt {
  if (content.length > RECEIPT_LIMIT) throw new Error('فایل فیش بیش از حد بزرگ است.')
  let packet: Record<string, unknown>
  try {
    packet = JSON.parse(content.replace(/^\uFEFF/, '')) as Record<string, unknown>
  } catch {
    throw new Error('فایل فیش خوانده نشد؛ فایل پستینو را انتخاب کنید.')
  }
  if (
    !packet ||
    packet.format !== 'pestino-receipt' ||
    packet.version !== 1 ||
    !packet.receipt ||
    typeof packet.receipt !== 'object'
  )
    throw new Error('این فایل رسید پستینو نیست؛ فایل پشتیبان را اینجا وارد نکنید.')
  const raw = packet.receipt as Record<string, unknown>
  if (typeof raw.id !== 'string' || !/^[a-zA-Z0-9-]{16,64}$/.test(raw.id))
    throw new Error('شناسهٔ فیش معتبر نیست.')
  const checked = validateReceipt(raw)
  if (!checked.image_data || checked.reference.length < 4)
    throw new Error('عکس فیش و کد پیگیری حداقل چهار نویسه‌ای لازم است.')
  return {
    ...checked,
    id: raw.id,
    created_at: new Date().toISOString(),
    imported: true,
    confirmed_at: null,
  }
}

export async function readReceiptPacket(file: File): Promise<string> {
  if (file.size > RECEIPT_LIMIT) throw new Error('فایل فیش بیش از حد بزرگ است.')
  // FileReader also works on older Android WebViews without File.text().
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(new Error('فایل فیش خوانده نشد؛ دوباره انتخاب کنید.'))
    reader.readAsText(file)
  })
}
