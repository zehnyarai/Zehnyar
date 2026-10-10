import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import { ArrowLeft, Check, CircleAlert, LoaderCircle, X } from 'lucide-react'

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand">
      <div className="brand-mark">
        <svg viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <path
            d="M24 37V22M24 28C10 28 11 13 11 13s14-1 13 15ZM24 22C24 10 37 10 37 10s1 13-13 15"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      {!compact && (
        <div>
          <strong>
            پستینو<span className="brand-dot">.</span>
          </strong>
          <span>همراه هوشمند باغ شما</span>
        </div>
      )}
    </div>
  )
}
export function Badge({
  children,
  tone = 'green',
}: {
  children: ReactNode
  tone?: 'green' | 'amber' | 'red' | 'gray' | 'blue'
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}
export function Spinner({ label = 'در حال بارگذاری…' }: { label?: string }) {
  return (
    <span className="spinner-label">
      <LoaderCircle size={18} className="spin" />
      {label}
    </span>
  )
}
export function EmptyState({
  icon,
  title,
  text,
  action,
}: {
  icon: ReactNode
  title: string
  text: string
  action?: ReactNode
}) {
  return (
    <div className="empty-state">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  )
}
export function PageTitle({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow?: string
  title: string
  subtitle: string
  action?: ReactNode
}) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action && <div className="heading-actions">{action}</div>}
    </div>
  )
}
export function CardHeader({
  title,
  subtitle,
  action,
  onClick,
}: {
  title: string
  subtitle?: string
  action?: string
  onClick?: () => void
}) {
  return (
    <div className="card-header">
      <div>
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action && (
        <button className="text-button" onClick={onClick}>
          {action}
          <ArrowLeft size={15} />
        </button>
      )}
    </div>
  )
}
export function InfoBanner({
  children,
  tone = 'info',
}: {
  children: ReactNode
  tone?: 'info' | 'warning' | 'success'
}) {
  return (
    <div className={`info-banner ${tone}`}>
      <CircleAlert size={18} />
      <div>{children}</div>
    </div>
  )
}
export function CheckList({ items }: { items: string[] }) {
  return (
    <ul className="check-list">
      {items.map((item, i) => (
        <li key={i}>
          <Check size={16} />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}

export function Modal({
  title,
  subtitle,
  children,
  onClose,
  wide = false,
}: {
  title: string
  subtitle?: string
  children: ReactNode
  onClose: () => void
  wide?: boolean
}) {
  const ref = useRef<HTMLDivElement>(null)
  const id = useId()
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const focusable = () =>
      [
        ...(ref.current?.querySelectorAll<HTMLElement>(
          'button, input, select, textarea, a[href], [tabindex="0"]'
        ) ?? []),
      ].filter((el) => !el.hasAttribute('disabled'))
    focusable()[0]?.focus()
    const handle = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'Tab') {
        const nodes = focusable()
        const first = nodes[0]
        const last = nodes[nodes.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last?.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first?.focus()
        }
      }
    }
    document.addEventListener('keydown', handle)
    return () => {
      document.body.style.overflow = overflow
      document.removeEventListener('keydown', handle)
      previous?.focus()
    }
  }, [onClose])
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={ref}
        className={`modal ${wide ? 'modal-wide' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
      >
        <header className="modal-header">
          <div>
            <h2 id={id}>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <button onClick={onClose} className="icon-button" aria-label="بستن">
            <X size={20} />
          </button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}
