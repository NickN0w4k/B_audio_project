import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { StatusStrip } from './StatusStrip'
import { useRunEvents } from '../../features/runtime/useRunEvents'

export function Shell() {
  useRunEvents()

  return (
    <div className="flex flex-col h-screen bg-[var(--color-bg)] overflow-hidden">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
      <StatusStrip />
    </div>
  )
}
