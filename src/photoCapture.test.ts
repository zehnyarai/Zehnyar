import { describe, expect, it } from 'vitest'
import { capturePhoto, fileFromCaptured, isUnreadableFile, PhotoReadError } from './photoCapture'

// A one-pixel JPEG header plus padding: enough for magic-byte sniffing.
const JPEG_BYTES = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10, 0x4a, 0x46, 0x49, 0x46])
const PNG_BYTES = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00])

function file(bytes: Uint8Array, type = 'image/jpeg', name = 'leaf.jpg'): File {
  return new File([bytes.buffer.slice(0) as ArrayBuffer], name, { type })
}

/** A File whose storage went away after the picker closed. */
function staleFile(type = 'image/jpeg'): File {
  const value = file(JPEG_BYTES, type)
  Object.defineProperty(value, 'arrayBuffer', {
    value: () => Promise.reject(new DOMException('stale handle', 'NotReadableError')),
  })
  Object.defineProperty(value, 'slice', {
    value: () => ({
      arrayBuffer: () => Promise.reject(new DOMException('stale handle', 'NotReadableError')),
    }),
  })
  return value
}

describe('photo capture keeps the bytes, not the picker handle', () => {
  it('copies a picked JPEG into a self-contained data URL', async () => {
    const captured = await capturePhoto(file(JPEG_BYTES))
    expect(captured.type).toBe('image/jpeg')
    expect(Array.from(captured.bytes)).toEqual(Array.from(JPEG_BYTES))
    // The fresh File holds the same bytes and has no link to the original handle.
    const fresh = fileFromCaptured(captured)
    expect(fresh.type).toBe('image/jpeg')
    expect(fresh.name).toBe('leaf.jpg')
    const bytes = new Uint8Array(await fresh.arrayBuffer())
    expect(Array.from(bytes)).toEqual(Array.from(JPEG_BYTES))
    expect(await fileFromCaptured(captured).slice(0, 3).arrayBuffer()).toBeTruthy()
  })
  it('sniffs the real type when Android reports an empty MIME type', async () => {
    const captured = await capturePhoto(file(PNG_BYTES, '', 'photo'))
    expect(captured.type).toBe('image/png')
    expect(captured.name).toBe('photo')
    expect(Array.from(captured.bytes)).toEqual(Array.from(PNG_BYTES))
  })
  it('refuses a file that is not really an image', async () => {
    await expect(
      capturePhoto(file(new Uint8Array([0x3c, 0x68, 0x74, 0x6d, 0x6c]), 'image/jpeg'))
    ).rejects.toThrow(/معتبر نیست/)
    await expect(capturePhoto(file(JPEG_BYTES, 'application/pdf'))).rejects.toThrow(/JPG/)
  })
  it('explains a stale handle in Persian instead of leaking the browser error', async () => {
    const realReader = globalThis.FileReader
    class FailingReader {
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      error = new DOMException('could not read', 'NotReadableError')
      result: string | null = null
      readAsDataURL() {
        setTimeout(() => this.onerror?.(), 0)
      }
    }
    // @ts-expect-error deliberately replacing the browser reader for this case
    globalThis.FileReader = FailingReader
    try {
      const error = await capturePhoto(staleFile()).catch((e: unknown) => e)
      expect(error).toBeInstanceOf(PhotoReadError)
      expect((error as Error).message).toContain('دوباره')
      expect((error as Error).message).not.toMatch(/permission|could not be read/i)
    } finally {
      globalThis.FileReader = realReader
    }
  })
  it('recovers through FileReader when only the byte API is broken', async () => {
    const value = file(JPEG_BYTES)
    Object.defineProperty(value, 'arrayBuffer', {
      value: () => Promise.reject(new DOMException('busy', 'NotReadableError')),
    })
    const base64 = btoa(String.fromCharCode(...JPEG_BYTES))
    const realReader = globalThis.FileReader
    class WorkingReader {
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      error = null
      result: string | null = null
      readAsDataURL() {
        this.result = `data:image/jpeg;base64,${base64}`
        setTimeout(() => this.onload?.(), 0)
      }
    }
    // @ts-expect-error minimal reader for this environment
    globalThis.FileReader = WorkingReader
    try {
      const captured = await capturePhoto(value)
      expect(Array.from(captured.bytes)).toEqual(Array.from(JPEG_BYTES))
      const bytes = new Uint8Array(await fileFromCaptured(captured).arrayBuffer())
      expect(Array.from(bytes)).toEqual(Array.from(JPEG_BYTES))
    } finally {
      globalThis.FileReader = realReader
    }
  })
  it('recognises the family of unreadable-file errors by name or message', () => {
    expect(isUnreadableFile(new DOMException('x', 'NotReadableError'))).toBe(true)
    expect(isUnreadableFile(new DOMException('x', 'SecurityError'))).toBe(true)
    expect(
      isUnreadableFile(
        new Error(
          'The requested file could not be read, typically due to permission problems that have occurred after a reference to a file was acquired.'
        )
      )
    ).toBe(true)
    expect(isUnreadableFile(new Error('network down'))).toBe(false)
    expect(isUnreadableFile(new PhotoReadError())).toBe(true)
  })
})
