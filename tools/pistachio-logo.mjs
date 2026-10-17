#!/usr/bin/env node
/**
 * Pistachio leaf brand mark (Pistacia vera, odd-pinnate: two opposite pairs + a terminal
 * leaflet). The owner rejected the generic leaf, which read like a "post" pin, and asked for
 * a green pistachio leaf. This script is the single source of truth for:
 *   - public/favicon.svg and the PNG icons (web + iPhone)
 *   - every Android launcher mipmap and splash screen
 *   - the adaptive-icon foreground vector
 *
 * Run: node tools/pistachio-logo.mjs
 * Requires @resvg/resvg-js (installed with --no-save; not a runtime dependency).
 */
import { Resvg } from '@resvg/resvg-js'
import { mkdirSync, writeFileSync, readdirSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'

const root = new URL('..', import.meta.url).pathname
const VIEW = 512

/* ---------------------------------------------------------------- geometry */
const round = (n) => Math.round(n * 100) / 100
const add = (a, b) => [a[0] + b[0], a[1] + b[1]]
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]]
const mul = (a, k) => [a[0] * k, a[1] * k]
const norm = (a) => {
  const len = Math.hypot(a[0], a[1]) || 1
  return [a[0] / len, a[1] / len]
}
const perp = (a) => [-a[1], a[0]]
const mix = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]

/** A pointed, slightly curved leaflet from base B to tip T with half-width W. */
function leaflet(B, T, W, bend = 0.18) {
  const dir = norm(sub(T, B))
  const side = perp(dir)
  const mid = mix(B, T, 0.45)
  const belly = add(mid, mul(side, W))
  const belly2 = add(mid, mul(side, -W))
  const tipPull = mul(dir, -0.04 * Math.hypot(...sub(T, B)))
  const c1 = add(add(mix(B, belly, 0.72), mul(side, bend * W)), tipPull)
  const c2 = add(add(mix(B, belly2, 0.72), mul(side, -bend * W)), tipPull)
  return {
    path: `M${round(B[0])} ${round(B[1])} Q${round(c1[0])} ${round(c1[1])} ${round(T[0])} ${round(T[1])} Q${round(c2[0])} ${round(c2[1])} ${round(B[0])} ${round(B[1])} Z`,
    midrib: `M${round(add(B, mul(dir, 6))[0])} ${round(add(B, mul(dir, 6))[1])} Q${round(add(mix(B, T, 0.5), mul(side, bend * 4))[0])} ${round(add(mix(B, T, 0.5), mul(side, bend * 4))[1])} ${round(add(mix(B, T, 0.9), mul(side, bend * 6))[0])} ${round(add(mix(B, T, 0.9), mul(side, bend * 6))[1])}`,
  }
}

/** Rachis (stem) of the compound leaf, bottom-left to top-right. */
const STEM = { from: [168, 412], to: [344, 140], control: [206, 262] }
function stemPoint(t) {
  const { from, to, control } = STEM
  const a = mix(from, control, t)
  const b = mix(control, to, t)
  return mix(a, b, t)
}
const stemTangent = (t) =>
  norm(sub(stemPoint(Math.min(1, t + 0.01)), stemPoint(Math.max(0, t - 0.01))))

const LEAFLETS = []
for (const [t, length, width] of [
  [0.26, 152, 82],
  [0.6, 162, 86],
]) {
  const base = stemPoint(t)
  const dir = stemTangent(t)
  const up = norm(add(dir, [0, -0.35]))
  // two opposite leaflets per node, swept forward and slightly upward
  for (const sign of [1, -1]) {
    const along = add(norm(add(up, mul(perp(up), sign * 1.2))), [0, -0.3])
    const tip = add(base, mul(norm(along), length))
    LEAFLETS.push({ ...leaflet(base, tip, width, sign * 0.14), sign })
  }
}
// terminal leaflet, slightly fanning up from the tip of the rachis
{
  const base = stemPoint(0.94)
  const tip = add(stemPoint(1), [-16, -92])
  LEAFLETS.push({ ...leaflet(base, tip, 72, 0), sign: 0 })
}
// Centre the drawing: shift every point by the bounding box of the geometry.
{
  const xs = []
  const ys = []
  for (const point of [STEM.from, STEM.control, STEM.to]) {
    xs.push(point[0])
    ys.push(point[1])
  }
  for (const l of LEAFLETS) {
    for (const part of l.path.slice(1).split(/[MQZ]/).filter(Boolean)) {
      const nums = part
        .trim()
        .split(/[\s,]+/)
        .map(Number)
      for (let i = 0; i + 1 < nums.length; i += 2) {
        xs.push(nums[i])
        ys.push(nums[i + 1])
      }
    }
  }
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const dx = Math.round(VIEW / 2 - (minX + maxX) / 2)
  const dy = Math.round(VIEW / 2 - (minY + maxY) / 2)
  if (dx || dy) {
    STEM.from[0] += dx
    STEM.from[1] += dy
    STEM.control[0] += dx
    STEM.control[1] += dy
    STEM.to[0] += dx
    STEM.to[1] += dy
    for (const l of LEAFLETS) {
      l.path = shiftPath(l.path, dx, dy)
      l.midrib = shiftPath(l.midrib, dx, dy)
    }
  }
}
function shiftPath(d, dx, dy) {
  const tokens = d.match(/[MQZ]|-?\d+(?:\.\d+)?/g) ?? []
  let axis = 0
  return tokens
    .map((token) => {
      if (/^[MQZ]$/.test(token)) {
        axis = 0
        return token
      }
      const value = Number(token) + (axis === 0 ? dx : dy)
      axis = (axis + 1) % 2
      return String(Math.round(value * 100) / 100)
    })
    .join(' ')
}
const STEM_PATH = () =>
  `M${round(STEM.from[0])} ${round(STEM.from[1])} Q${round(STEM.control[0])} ${round(STEM.control[1])} ${round(STEM.to[0])} ${round(STEM.to[1])}`

/* ------------------------------------------------------------------ pieces */
const leafBody = () => LEAFLETS.map((l) => `<path d="${l.path}"/>`).join('')
const leafMidribs = () =>
  LEAFLETS.map(
    (l) =>
      `<path d="${l.midrib}" fill="none" stroke="#2f7a4d" stroke-opacity=".45" stroke-width="3.4" stroke-linecap="round"/>`
  ).join('')

/**
 * The app mark: a green pistachio leaf on a deep pistachio → teal → sky gradient tile.
 * `plain` paints a flat background (used for the adaptive foreground, where Android
 * supplies the background layer itself).
 */
function mark({ size = 512, plain = false, white = false, padding = 0 } = {}) {
  const g = padding ? ` translate(${padding} ${padding}) scale(${(VIEW - padding * 2) / VIEW})` : ''
  const bg = plain
    ? ''
    : `<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0f6b4f"/><stop offset=".55" stop-color="#157a7c"/><stop offset="1" stop-color="#2b9fd8"/>
    </linearGradient>
    <radialGradient id="glow" cx=".5" cy=".38" r=".55">
      <stop offset="0" stop-color="#ffffff" stop-opacity=".26"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="leaf" x1="0" y1="1" x2=".7" y2="0">
      <stop offset="0" stop-color="#2f9e63"/><stop offset="1" stop-color="#8ee39a"/>
    </linearGradient>
  </defs>
  <rect width="${VIEW}" height="${VIEW}" rx="${VIEW * 0.235}" fill="url(#bg)"/>
  <rect width="${VIEW}" height="${VIEW}" rx="${VIEW * 0.235}" fill="url(#glow)"/>`
  if (white) {
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${VIEW} ${VIEW}" width="${size}" height="${size}"><g${g} fill="#ffffff" fill-opacity=".96">${leafBody()}</g><path d="${STEM_PATH()}" fill="none" stroke="#ffffff" stroke-opacity=".96" stroke-width="13" stroke-linecap="round"/>${LEAFLETS.map((l) => `<path d="${l.midrib}" fill="none" stroke="#0f6b4f" stroke-opacity=".28" stroke-width="3.4" stroke-linecap="round"/>`).join('')}</svg>`
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${VIEW} ${VIEW}" width="${size}" height="${size}">${bg}
  <g${g}><g fill="url(#leaf)" stroke="#1d6b45" stroke-opacity=".35" stroke-width="2">${leafBody()}</g>${leafMidribs()}<path d="${STEM_PATH()}" fill="none" stroke="#1f7c50" stroke-width="13" stroke-linecap="round"/></g>
</svg>`
}

/** Foreground-only layer for Android adaptive icons: the leaf, transparent background. */
function foreground() {
  return mark({ plain: true, size: 512 })
}

/* ------------------------------------------------------------------ writing */
function png(svg, size) {
  return new Resvg(svg, { fitTo: { mode: 'width', value: size } }).render().asPng()
}
function write(path, data) {
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, data)
  console.log('wrote', path.replace(root, ''), data.length ? `${data.length} B` : '')
}

write(join(root, 'public/favicon.svg'), mark())
for (const size of [180, 192, 512]) write(join(root, `public/icon-${size}.png`), png(mark(), size))

const res = join(root, 'android/app/src/main/res')
for (const [folder, size] of [
  ['mdpi', 48],
  ['hdpi', 72],
  ['xhdpi', 96],
  ['xxhdpi', 144],
  ['xxxhdpi', 192],
]) {
  write(join(res, `mipmap-${folder}/ic_launcher.png`), png(mark(), size))
  write(join(res, `mipmap-${folder}/ic_launcher_round.png`), png(mark(), size))
  // Adaptive foreground: the leaf sits inside the 66% safe zone.
  const fg = png(foreground(), Math.round(size * 2.25))
  write(join(res, `mipmap-${folder}/ic_launcher_foreground.png`), fg)
}

// Splash screens keep their existing pixel sizes; only the mark changes.
for (const folder of readdirSync(res).filter((f) => f.startsWith('drawable'))) {
  const file = join(res, folder, 'splash.png')
  try {
    const existing = readFileSync(file)
    // PNG IHDR: width/height are the first two big-endian uint32 after the signature.
    const width = existing.readUInt32BE(16)
    const height = existing.readUInt32BE(20)
    const markSize = Math.max(60, Math.min(240, Math.round(Math.min(width, height) * 0.23)))
    const svg = mark({ size: markSize })
    const tile = new Resvg(svg, { fitTo: { mode: 'width', value: markSize } }).render().asPng()
    // Compose on the paper background with a tiny raw composition (no image library needed).
    write(file, composeOnPaper(tile, width, height))
  } catch (error) {
    console.warn('splash skipped', file, String(error).slice(0, 80))
  }
}

/** Draw the mark centred on the paper colour, without an image dependency. */
function composeOnPaper(_tile, width, height) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="${width}" height="${height}" fill="#f7faf8"/><g transform="translate(${(width - Math.min(240, Math.round(Math.min(width, height) * 0.23))) / 2} ${(height - Math.min(240, Math.round(Math.min(width, height) * 0.23))) / 2})">${mark(
    { size: 240 }
  )
    .replace(/^<svg[^>]*>/, '')
    .replace(/<\/svg>$/, '')
    .replace(/width="\d+" height="\d+"/g, '')}</g></svg>`
  return new Resvg(svg, { fitTo: { mode: 'width', value: width } }).render().asPng()
}

// Vector drawable for the adaptive foreground (same geometry, Android path syntax).
const vector = `<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="${VIEW}" android:viewportHeight="${VIEW}">
  <group android:translateX="8" android:translateY="8" android:scaleX="0.66" android:scaleY="0.66">
${LEAFLETS.map((l) => `    <path android:pathData="${l.path}" android:fillColor="#FFFFFF" android:strokeColor="#1D6B45" android:strokeAlpha="0.35" android:strokeWidth="3"/>`).join('\n')}
    <path android:pathData="${STEM_PATH()}" android:strokeColor="#FFFFFF" android:strokeWidth="16" android:strokeLineCap="round"/>
  </group>
</vector>
`
write(join(res, 'drawable-v24/ic_launcher_foreground.xml'), vector)
write(
  join(res, 'values/ic_launcher_background.xml'),
  '<?xml version="1.0" encoding="utf-8"?><resources><color name="ic_launcher_background">#0F6B4F</color></resources>\n'
)

// One source of truth for the in-app React mark (header, footer, logo component).
write(
  join(root, 'src/brand/pistachio.ts'),
  `// Generated by tools/pistachio-logo.mjs — do not edit by hand.
// A Pistacia (pistachio) compound leaf: two opposite leaflet pairs on a rachis plus a
// terminal leaflet. Geometry is shared with the launcher icons so the app and the icon match.
export const VIEW = ${VIEW}
export const LEAVES = [
${LEAFLETS.map((l) => `  '${l.path}',`).join('\n')}
] as const
export const MIDRIBS = [
${LEAFLETS.map((l) => `  '${l.midrib}',`).join('\n')}
] as const
export const STEM = '${STEM_PATH()}'
`
)
console.log('wrote src/brand/pistachio.ts')
