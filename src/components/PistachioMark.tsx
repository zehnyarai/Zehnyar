import { LEAVES, MIDRIBS, STEM, VIEW } from '../brand/pistachio'

/**
 * The Pestino mark: a green compound pistachio leaf (two opposite leaflet pairs on a
 * rachis plus a terminal leaflet). Geometry comes from the same generator that draws the
 * launcher icons, so the app and the home-screen icon never drift apart.
 *
 * `tile` draws the green→teal→sky rounded tile (for the brand block). Without it only the
 * leaf is drawn, which is what the header, footer and headings use.
 */
export default function PistachioMark({
  size = 28,
  tile = false,
  className,
  title,
}: {
  size?: number
  tile?: boolean
  className?: string
  title?: string
}) {
  const id = `pistachio-${tile ? 'tile' : 'leaf'}`
  return (
    <svg
      viewBox={`0 0 ${VIEW} ${VIEW}`}
      width={size}
      height={size}
      className={className}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      focusable="false"
    >
      {tile && (
        <>
          <defs>
            <linearGradient id={`${id}-bg`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#0f6b4f" />
              <stop offset=".55" stopColor="#157a7c" />
              <stop offset="1" stopColor="#2b9fd8" />
            </linearGradient>
            <linearGradient id={`${id}-leaf`} x1="0" y1="1" x2=".7" y2="0">
              <stop offset="0" stopColor="#2f9e63" />
              <stop offset="1" stopColor="#8ee39a" />
            </linearGradient>
          </defs>
          <rect width={VIEW} height={VIEW} rx={VIEW * 0.235} fill={`url(#${id}-bg)`} />
        </>
      )}
      <g
        fill={tile ? `url(#${id}-leaf)` : 'currentColor'}
        stroke={tile ? '#1d6b45' : 'none'}
        strokeOpacity=".35"
        strokeWidth="2"
      >
        {LEAVES.map((d) => (
          <path key={d} d={d} />
        ))}
      </g>
      {tile &&
        MIDRIBS.map((d) => (
          <path
            key={d}
            d={d}
            fill="none"
            stroke="#2f7a4d"
            strokeOpacity=".45"
            strokeWidth="3.4"
            strokeLinecap="round"
          />
        ))}
      <path
        d={STEM}
        fill="none"
        stroke={tile ? '#1f7c50' : 'currentColor'}
        strokeWidth={tile ? 13 : 26}
        strokeLinecap="round"
      />
    </svg>
  )
}
