/**
 * Provider calls on the phone (APK) go through Capacitor's native HTTP plugin, not the
 * WebView. Two reasons:
 *  - a WebView is a browser: CORS, Origin headers and preflights apply, and a provider
 *    that does not answer a preflight looks exactly like a broken key;
 *  - Android's HTTP stack keeps the behaviour identical across WebView versions.
 * On the web/PWA edition the normal fetch is used, unchanged.
 */
export async function providerFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const { Capacitor, CapacitorHttp } = await import('@capacitor/core')
  if (!Capacitor.isNativePlatform()) return fetch(url, init)

  const headers: Record<string, string> = {}
  new Headers(init.headers ?? {}).forEach((value, key) => {
    headers[key] = value
  })
  // The native plugin serialises an object; a JSON string can be double-quoted, so parse.
  let data: unknown
  if (typeof init.body === 'string') {
    try {
      data = JSON.parse(init.body) as unknown
    } catch {
      data = init.body
    }
  }
  const response = await CapacitorHttp.request({
    url,
    method: (init.method ?? 'GET').toUpperCase(),
    headers,
    ...(data === undefined ? {} : { data }),
    responseType: 'text',
    connectTimeout: 30_000,
    // A photo screening can legitimately take a couple of minutes on a slow orchard link.
    readTimeout: 180_000,
  })
  const text =
    typeof response.data === 'string' ? response.data : JSON.stringify(response.data ?? '')
  return new Response(text, {
    status: response.status,
    headers: response.headers as Record<string, string>,
  })
}
