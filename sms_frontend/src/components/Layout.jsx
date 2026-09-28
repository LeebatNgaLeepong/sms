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
          <button
            className="btn-icon btn-ghost"
            onClick={() => setSidebarOpen(true)}
            style={{ display: 'none' }}
            id="mobile-menu-btn"
          >
            <IconMenu />
          </button>
          <div />
          <div className="main-header-actions" />
        </header>
        <div className="page-content page-enter">
          <Outlet />
        </div>
      </div>
      <style>{`
        @media (max-width: 768px) {
          #mobile-menu-btn { display: flex !important; }
        }
      `}</style>
    </div>
  )
}
