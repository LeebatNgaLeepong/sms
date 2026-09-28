import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { IconMenu } from './Icons'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="app-layout">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-content">
        <header className="main-header">
          <div className="main-header-left">
            <button
              className="btn-icon btn-ghost mobile-menu-toggle"
              onClick={() => setSidebarOpen(true)}
              id="mobile-menu-btn"
              aria-label="Open menu"
            >
              <IconMenu />
            </button>
            <div className="mobile-brand-title">College SMS</div>
          </div>
          <div className="main-header-actions" />
        </header>
        <div className="page-content page-enter">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
