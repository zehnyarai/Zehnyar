import { Capacitor, registerPlugin } from '@capacitor/core'
const saver = registerPlugin<{
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
