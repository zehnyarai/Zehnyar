import { Capacitor, registerPlugin } from '@capacitor/core'
const saver = registerPlugin<{
  share: (options: { name: string; content: string }) => Promise<void>
  save: (options: {
    name: string
    content: string
    mime: string
  }) => Promise<{ cancelled?: boolean }>
}>('PestinoFiles')

export async function saveTextFile(
  name: string,
  content: string,
  mime = 'application/json'
): Promise<boolean> {
  if (Capacitor.isNativePlatform()) {
    const result = await saver.save({ name, content: '\uFEFF' + content, mime: mime.split(';')[0] })
    return !result.cancelled
  }
  const url = URL.createObjectURL(new Blob(['\uFEFF', content], { type: mime }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 10000)
  return true
}

/** Returns the action taken, never claims that a manager received a file. */
export async function shareReceiptFile(
  name: string,
  content: string
): Promise<'shared' | 'saved' | 'cancelled'> {
  if (Capacitor.isNativePlatform()) {
    await saver.share({ name, content })
    return 'shared'
  }
  const file = new File([content], name, { type: 'application/json' })
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: 'فیش پستینو' })
      return 'shared'
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') return 'cancelled'
      // A browser can advertise sharing but reject this file type; download instead.
    }
  }
  return (await saveTextFile(name, content)) ? 'saved' : 'cancelled'
}
