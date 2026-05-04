import { NavLink, useLocation } from 'react-router-dom'
import { useAppStore } from '../../stores/appStore'
import { cn } from '../../lib/utils/cn'

type NavItem = {
  label: string
  href: string
  icon: React.ReactNode
  requiresProject?: boolean
}

function IconHome() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12L12 3l9 9" /><path d="M9 21V12h6v9" /><path d="M3 12v9h18v-9" />
    </svg>
  )
}

function IconAnalysis() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

function IconRepair() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  )
}

function IconCompare() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="9" height="18" rx="1" /><rect x="13" y="3" width="9" height="18" rx="1" />
    </svg>
  )
}

function IconExport() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}

export function Sidebar() {
  const { selectedProjectId } = useAppStore()
  const location = useLocation()

  const items: NavItem[] = [
    { label: 'Home', href: '/', icon: <IconHome /> },
    {
      label: 'Analysis',
      href: selectedProjectId ? `/analysis/${selectedProjectId}` : '/analysis',
      icon: <IconAnalysis />,
      requiresProject: true,
    },
    {
      label: 'Repair',
      href: selectedProjectId ? `/repair/${selectedProjectId}` : '/repair',
      icon: <IconRepair />,
      requiresProject: true,
    },
    {
      label: 'Compare',
      href: selectedProjectId ? `/compare/${selectedProjectId}/run/latest` : '/compare',
      icon: <IconCompare />,
      requiresProject: true,
    },
    {
      label: 'Export',
      href: selectedProjectId ? `/export/${selectedProjectId}/run/latest` : '/export',
      icon: <IconExport />,
      requiresProject: true,
    },
  ]

  return (
    <aside className="flex flex-col items-center w-14 border-r border-[var(--color-border)] bg-[var(--color-surface)] flex-shrink-0 py-3 gap-1">
      {items.map((item) => {
        const disabled = item.requiresProject && !selectedProjectId
        const isActive = item.href === '/'
          ? location.pathname === '/'
          : location.pathname.startsWith(item.href.split('/').slice(0, 2).join('/'))

        if (disabled) {
          return (
            <div
              key={item.label}
              title={item.label}
              className="flex items-center justify-center w-10 h-10 rounded-[var(--radius-md)] text-[var(--color-border)] cursor-not-allowed"
            >
              {item.icon}
            </div>
          )
        }

        return (
          <NavLink
            key={item.label}
            to={item.href}
            title={item.label}
            className={cn(
              'flex items-center justify-center w-10 h-10 rounded-[var(--radius-md)] transition-colors',
              isActive
                ? 'text-[var(--color-accent)] bg-[var(--color-accent)]/10'
                : 'text-[var(--color-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-raised)]',
            )}
          >
            {item.icon}
          </NavLink>
        )
      })}
    </aside>
  )
}
