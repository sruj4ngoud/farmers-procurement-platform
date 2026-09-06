import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useLanguage } from '../context/LanguageContext.jsx';
import { NotificationProvider } from '../context/NotificationContext.jsx';
import LanguageSwitcher from '../components/common/LanguageSwitcher.jsx';
import HelpWidget from '../components/farmer/HelpWidget.jsx';
import {
  LayoutDashboard, Sprout, ClipboardCheck, Landmark,
  History, LogOut, Menu, X
} from 'lucide-react';

export default function FarmerLayout() {
  const { farmer, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const NAV = [
    { to: '/dashboard', icon: LayoutDashboard, label: t('nav.dashboard') },
    { to: '/sell', icon: Sprout, label: t('nav.sell') },
    { to: '/my-booking', icon: ClipboardCheck, label: t('nav.myBooking') },
    { to: '/bank-details', icon: Landmark, label: t('nav.bank') },
    { to: '/history', icon: History, label: t('nav.history') },
  ];

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <NotificationProvider>
      <div className="app-container">
        {/* Mobile menu button */}
        <button
          className="mobile-menu-btn"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label="Toggle menu"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div
          className={`sidebar-overlay ${sidebarOpen ? 'open' : ''}`}
          onClick={() => setSidebarOpen(false)}
        />

        {/* Sidebar */}
        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <div className="sidebar-brand">Smart Farmer</div>
            <p style={{ color: 'var(--gray-500)', fontSize: '0.72rem', marginTop: 2 }}>
              {farmer?.farmer_name || 'Farmer'}
            </p>
          </div>

          <nav>
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/dashboard'}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon size={18} />
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="sidebar-footer">
            <button onClick={handleLogout}>
              <LogOut size={16} />
              {t('nav.signOut')}
            </button>
          </div>
        </aside>

        <main className="main-content">
          <div className="fp-topbar">
            <span className="fp-topbar-hint">
              {farmer?.passbook_number ? farmer.passbook_number : ''}
            </span>
            <LanguageSwitcher />
          </div>
          <Outlet />
        </main>

        <HelpWidget />
      </div>
    </NotificationProvider>
  );
}
