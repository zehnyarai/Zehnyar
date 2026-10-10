import { IS_STANDALONE } from './config'
export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (IS_STANDALONE) {
    const { localApi } = await import('./standalone')
    return localApi<T>(path, options)
  }
  const isForm = options.body instanceof FormData
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      credentials: 'same-origin',
      ...options,
      headers: {
        ...(options.body && !isForm ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError('ارتباط با سرور برقرار نشد. اتصال اینترنت را بررسی و دوباره تلاش کنید.', 0)
  }
  let body: unknown
  try {
    body = await response.json()
  } catch {
    throw new ApiError('ارتباط با سرور برقرار نشد. دوباره تلاش کنید.', response.status)
  }
  if (!response.ok) {
    const detail =
      body && typeof body === 'object' ? (body as { detail?: unknown }).detail : undefined
    const message =
      typeof detail === 'string' ? detail : 'اطلاعات واردشده معتبر نیست. فیلدهای فرم را بررسی کنید.'
    throw new ApiError(message, response.status)
  }
  return body as T
}

export const fa = (value: number, maximumFractionDigits = 1) =>
  new Intl.NumberFormat('fa-IR', { maximumFractionDigits }).format(value)
export const today = () => {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Tehran',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date())
  return ['year', 'month', 'day'].map((t) => parts.find((p) => p.type === t)?.value).join('-')
}
export function persianDate(value: string | Date, options: Intl.DateTimeFormatOptions = {}) {
  return new Intl.DateTimeFormat('fa-IR', {
    day: 'numeric',
    month: 'long',
    timeZone: 'Asia/Tehran',
    ...options,
  }).format(
    typeof value === 'string' ? new Date(value.length === 10 ? `${value}T12:00:00Z` : value) : value
  )
}
export function relativeDate(value: string) {
  const days = Math.floor(
    (new Date(today() + 'T12:00:00Z').getTime() -
      new Date(value.slice(0, 10) + 'T12:00:00Z').getTime()) /
      86400000
  )
  if (days === 0) return 'امروز'
  if (days === 1) return 'دیروز'
  if (days > 1 && days < 7) return `${fa(days)} روز پیش`
  return persianDate(value)
}
export function dueLabel(date: string) {
  const days = Math.round(
    (new Date(date + 'T12:00:00Z').getTime() - new Date(today() + 'T12:00:00Z').getTime()) /
      86400000
  )
  if (days === 0) return 'امروز'
  if (days === 1) return 'فردا'
  if (days < 0) return 'گذشته'
  return persianDate(date)
}
export function checkImage(file: File) {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type))
    return 'لطفاً تصویر JPG، PNG یا WebP انتخاب کنید.'
  if (file.size > 8 * 1024 * 1024) return 'حجم تصویر باید کمتر از ۸ مگابایت باشد.'
  return null
}
export async function takePhoto(fallback: () => void, onFile: (file: File) => void) {
  const { Capacitor } = await import('@capacitor/core')
  if (!Capacitor.isNativePlatform()) {
    fallback()
    return
  }
  const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera')
  const photo = await Camera.getPhoto({
    quality: 90,
    resultType: CameraResultType.Uri,
    source: CameraSource.Camera,
    correctOrientation: true,
  })
  if (photo.webPath) {
    const blob = await (await fetch(photo.webPath)).blob()
    onFile(new File([blob], 'pistachio-camera.jpg', { type: 'image/jpeg' }))
  }
}
export async function downloadText(
  name: string,
  content: string,
  type = 'text/plain;charset=utf-8'
) {
  const { saveTextFile } = await import('./files')
  return saveTextFile(name, content, type)
}
export const errorMessage = (err: unknown) =>
  err instanceof Error ? err.message : 'خطایی رخ داد. دوباره تلاش کنید.'
