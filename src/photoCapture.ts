/**
 * Photos are copied into memory the moment the farmer picks them, not later.
 *
 * On Android the file behind `<input type="file">` (or a camera/gallery result) is a
 * temporary reference. When the page has re-rendered, or the picker activity has ended,
 * reading it again throws NotReadableError — the browser's wording is
 * "The requested file could not be read, typically due to permission problems…".
 * That used to surface as a raw English error right after tapping «تحلیل تصویر».
 * Copying the bytes immediately makes the photo independent of the picker's lifetime.
 */

export interface CapturedPhoto {
  name: string
  type: string
  /** The file's bytes in memory; no link to the picker's temporary handle remains. */
  bytes: Uint8Array
}

const ALLOWED = ['image/jpeg', 'image/png', 'image/webp']
const MAX_BYTES = 8 * 1024 * 1024

export class PhotoReadError extends Error {
  constructor() {
    super(
      'عکس انتخاب‌شده دیگر در دسترس برنامه نیست (اندروید دسترسی به فایل را بست). ' +
        'عکس را دوباره از همین صفحه انتخاب یا با دکمهٔ «گرفتن عکس» ثبت کنید؛ دفتر و یادداشت‌های شما دست‌نخورده می‌مانند.'
    )
  }
}

function errorName(error: unknown): string {
  return error && typeof error === 'object' && 'name' in error ? String(error.name) : ''
}

/** True for the family of errors that mean "the picker's file handle is gone". */
export function isUnreadableFile(error: unknown): boolean {
  if (error instanceof PhotoReadError) return true
  const name = errorName(error)
  if (name === 'NotReadableError' || name === 'NotFoundError' || name === 'SecurityError')
    return true
  const message = error instanceof Error ? error.message : ''
  return /could not be read|not readable|permission problems/i.test(message)
}

/** Sniffs the real image type, because Android sometimes reports an empty MIME type. */
function sniffType(bytes: Uint8Array): string | null {
  if (bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) return 'image/jpeg'
  if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47)
    return 'image/png'
  if (
    String.fromCharCode(...bytes.slice(0, 4)) === 'RIFF' &&
    String.fromCharCode(...bytes.slice(8, 12)) === 'WEBP'
  )
    return 'image/webp'
  return null
}

function fromFileReader(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(reader.error ?? new Error('read failed'))
    reader.readAsDataURL(file)
  })
}

/** Reads the file now. If the picker handle is already stale, tries the byte API once. */
async function readBytes(file: File): Promise<Uint8Array> {
  try {
    const buffer = await file.arrayBuffer()
    return new Uint8Array(buffer)
  } catch (error) {
    // A stale handle can still sometimes be read through FileReader before it is released.
    try {
      const data = await fromFileReader(file)
      const comma = data.indexOf(',')
      if (comma < 0) throw new PhotoReadError()
      const binary = atob(data.slice(comma + 1))
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
      return bytes
    } catch {
      throw isUnreadableFile(error) ? new PhotoReadError() : error
    }
  }
}

/**
 * Copies one picked photo into memory. A caller that gets a CapturedPhoto can drop the
 * original File immediately; the copy never depends on Android's temporary handle.
 */
export async function capturePhoto(file: File): Promise<CapturedPhoto> {
  if (!ALLOWED.includes(file.type) && file.type)
    throw new Error('لطفاً تصویر JPG، PNG یا WebP انتخاب کنید.')
  if (file.size > MAX_BYTES) throw new Error('حجم تصویر باید کمتر از ۸ مگابایت باشد.')
  let bytes: Uint8Array
  try {
    bytes = await readBytes(file)
  } catch (error) {
    if (isUnreadableFile(error)) throw new PhotoReadError()
    throw error
  }
  // The bytes decide the type: a renamed HTML/PDF file with an image MIME type must not
  // reach the device's resize step, and an empty Android MIME type is still readable.
  const type = sniffType(bytes)
  if (!type) throw new Error('محتوای فایل تصویر معتبر نیست؛ یک عکس JPG، PNG یا WebP انتخاب کنید.')
  return {
    name:
      file.name || `photo.${type === 'image/png' ? 'png' : type === 'image/webp' ? 'webp' : 'jpg'}`,
    type,
    bytes,
  }
}

/** A preview URL built from the in-memory copy, never from the picker's File. */
export function previewUrl(photo: CapturedPhoto): string {
  return URL.createObjectURL(new Blob([photo.bytes.buffer as ArrayBuffer], { type: photo.type }))
}

/**
 * Builds a fresh in-memory File for the upload. It has no link to the picker, so the
 * existing resize/EXIF-stripping step can read it without permission errors.
 */
export function fileFromCaptured(photo: CapturedPhoto): File {
  return new File([photo.bytes.buffer.slice(0) as ArrayBuffer], photo.name, {
    type: photo.type,
    lastModified: Date.now(),
  })
}
