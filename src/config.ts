export const IS_STANDALONE = import.meta.env.VITE_APP_MODE === 'standalone'
export const assetUrl = (path: string) =>
  path.startsWith('/') ? `${import.meta.env.BASE_URL}${path.slice(1)}` : path
