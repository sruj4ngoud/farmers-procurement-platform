import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAdmin } from '../context/AdminContext.jsx';
import {
  LayoutDashboard, Users, MapPin, Wheat, Building2, Clock,
  ClipboardCheck, Eye, ListOrdered, Package, Landmark, CreditCard,
  BarChart3, AlertTriangle, ScrollText, BrainCircuit, LogOut, Menu, X, Shield
} from 'lucide-react';

const ADMIN_NAV = [
  { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/admin/reviews', icon: Eye, label: 'Reviews' },
  { to: '/admin/queue', icon: ListOrdered, label: 'Queue' },
  { to: '/admin/procurement', icon: Package, label: 'Procurement' },
  { to: '/admin/payments', icon: CreditCard, label: 'Payments' },
  { to: '/admin/bank', icon: Landmark, label: 'Bank Verification' },
  { to: '/admin/farmers', icon: Users, label: 'Farmers' },
  { to: '/admin/crops', icon: Wheat, label: 'Crops & MSP' },
  { to: '/admin/centres', icon: Building2, label: 'Centres' },
  { to: '/admin/slots', icon: Clock, label: 'Slots' },
  { to: '/admin/bookings', icon: ClipboardCheck, label: 'Bookings' },
  { to: '/admin/reports', icon: BarChart3, label: 'Reports' },
  { to: '/admin/issues', icon: AlertTriangle, label: 'Issues' },
  { to: '/admin/audit', icon: ScrollText, label: 'Audit Logs' },
  { to: '/admin/ml', icon: BrainCircuit, label: 'AI Insights' },
];

export default function AdminLayout() {
  const { admin, logout } = useAdmin();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  return (
    <div className="app-container">
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

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Shield size={16} style={{ color: 'var(--gray-400)' }} />
            <span style={{
              fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.08em',
              textTransform: 'uppercase', color: 'var(--gray-500)'
            }}>
              District Administration
            </span>
          </div>
          <div className="sidebar-brand">{admin?.district || 'District'}</div>
          <p>{admin?.username || 'Admin'}</p>
        </div>

        <nav>
          {ADMIN_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/admin/dashboard'}
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
            Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
