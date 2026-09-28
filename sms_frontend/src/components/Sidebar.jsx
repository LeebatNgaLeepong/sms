import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  IconDashboard,
  IconStudents,
  IconSubjects,
  IconGrades,
  IconLogout,
} from './Icons'

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout, isAdmin, isTeacher, isStudent } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const initials = user
    ? `${(user.first_name || user.username)[0]}${(user.last_name || '')[0] || ''}`.toUpperCase()
    : ''

  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: <IconDashboard />,
      show: true,
    },
    {
      to: '/students',
      label: 'Students',
      icon: <IconStudents />,
      show: true,
    },
    {
      to: '/subjects',
      label: 'Subjects',
      icon: <IconSubjects />,
      show: true,
    },
    {
      to: '/grades',
      label: 'Grades',
      icon: <IconGrades />,
      show: true,
    },
  ]

  return (
    <>
      {isOpen && <div className="modal-overlay" style={{ zIndex: 99 }} onClick={onClose} />}
      <aside className={`sidebar${isOpen ? ' open' : ''}`}>
        <div className="sidebar-brand">
          <h1>College SMS</h1>
          <span>Student Management System</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Menu</div>
          {navItems
            .filter((item) => item.show)
            .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
                onClick={onClose}
              >
                {item.icon}
                {item.label}
              </NavLink>
            ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">
                {user?.first_name || user?.username}
              </div>
              <div className="sidebar-user-role">{user?.role}</div>
            </div>
            <button className="sidebar-logout" onClick={handleLogout} title="Sign out">
              <IconLogout />
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
