import { useState, useEffect } from 'react';
import { useAdmin } from '../../context/AdminContext.jsx';
import { adminApi } from '../../services/adminApi.js';
import {
  Users, ClipboardCheck, Eye, Calendar, ListOrdered,
  Building2, Package, CreditCard, ChevronRight
} from 'lucide-react';

const STAT_ICONS = {
  total_farmers: Users,
  active_bookings: ClipboardCheck,
  pending_reviews: Eye,
  today_bookings: Calendar,
  farmers_in_queue: ListOrdered,
  active_centres: Building2,
  today_procurement: Package,
  payments_processing: CreditCard,
};

const STAT_LABELS = {
  total_farmers: 'Total Farmers',
  active_bookings: 'Active Bookings',
  pending_reviews: 'Pending Reviews',
  today_bookings: "Today's Bookings",
  farmers_in_queue: 'Farmers in Queue',
  active_centres: 'Active Centres',
  today_procurement: "Today's Procurement",
  payments_processing: 'Payments Processing',
};

export default function AdminDashboardPage() {
  const { admin } = useAdmin();
  const [stats, setStats] = useState(null);
  const [mandals, setMandals] = useState([]);
  const [selectedMandal, setSelectedMandal] = useState(null);
  const [mandalDetail, setMandalDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [dashData, mandalData] = await Promise.all([
          adminApi.getDashboard(),
          adminApi.getMandals(),
        ]);
        if (!cancelled) {
          setStats(dashData);
          setMandals(mandalData);
        }
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const handleMandalClick = async (mandalId) => {
    if (selectedMandal === mandalId) {
      setSelectedMandal(null);
      setMandalDetail(null);
      return;
    }
    try {
      const data = await adminApi.getMandalDetail(mandalId);
      setSelectedMandal(mandalId);
      setMandalDetail(data);
    } catch (e) {
      setError(e.message);
    }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading dashboard...</p></div>;
  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <p style={{
          fontSize: '0.72rem', fontWeight: 600, color: 'var(--gray-400)',
          textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4,
        }}>
          District Administration
        </p>
        <h1>{admin?.district}</h1>
        <p style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>
          {admin?.username}
        </p>
      </div>

      {/* Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 1,
        background: 'var(--gray-200)',
        borderRadius: 6,
        overflow: 'hidden',
        marginBottom: 32,
      }}>
        {Object.keys(STAT_LABELS).map((key) => {
          const Icon = STAT_ICONS[key];
          return (
            <div key={key} style={{
              background: 'var(--white)',
              padding: '16px 20px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Icon size={14} style={{ color: 'var(--gray-400)' }} />
                <span style={{
                  fontSize: '0.68rem', fontWeight: 600, color: 'var(--gray-400)',
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                }}>
                  {STAT_LABELS[key]}
                </span>
              </div>
              <div style={{
                fontSize: '1.5rem', fontWeight: 800, color: 'var(--black)',
                letterSpacing: '-0.03em', lineHeight: 1,
              }}>
                {stats?.[key] ?? 0}
              </div>
            </div>
          );
        })}
      </div>

      {/* Mandal Overview */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ marginBottom: 16 }}>Mandal Overview</h2>

        {mandals.length === 0 ? (
          <p style={{ color: 'var(--gray-400)', fontSize: '0.875rem' }}>No mandals registered in this district.</p>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 12,
          }}>
            {mandals.map((m) => (
              <div
                key={m.mandal_id}
                onClick={() => handleMandalClick(m.mandal_id)}
                className="card"
                style={{
                  cursor: 'pointer',
                  borderColor: selectedMandal === m.mandal_id ? 'var(--black)' : 'var(--gray-200)',
                  transition: 'border-color .15s var(--ease)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h3 style={{ fontSize: '0.95rem' }}>{m.mandal_name}</h3>
                  <ChevronRight size={14} style={{ color: 'var(--gray-400)' }} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                  {[
                    { label: 'Farmers', value: m.farmers },
                    { label: 'Bookings', value: m.bookings },
                    { label: 'Queue', value: m.active_queue },
                  ].map((item) => (
                    <div key={item.label}>
                      <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 2 }}>
                        {item.label}
                      </div>
                      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--gray-800)' }}>
                        {item.value}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Selected Mandal Detail */}
        {mandalDetail && (
          <div className="card" style={{ marginTop: 16 }}>
            <div className="card-header">
              <h3>{mandalDetail.mandal_name} — Detail</h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 16, marginBottom: 20 }}>
              {[
                { label: 'Farmers', value: mandalDetail.farmers },
                { label: 'Centres', value: mandalDetail.centres },
                { label: 'Bookings', value: mandalDetail.bookings },
                { label: 'Active Queue', value: mandalDetail.active_queue },
                { label: 'Procurement', value: mandalDetail.procurement_completed },
                { label: 'Payments', value: mandalDetail.payments_pending },
              ].map((item) => (
                <div key={item.label}>
                  <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                    {item.label}
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--black)' }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>

            {mandalDetail.recent_bookings && mandalDetail.recent_bookings.length > 0 && (
              <div>
                <h4 style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                  Recent Bookings
                </h4>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Booking #</th>
                        <th>Quantity (Q)</th>
                        <th>Status</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mandalDetail.recent_bookings.map((b, i) => (
                        <tr key={i}>
                          <td className="font-mono" style={{ fontSize: '0.8rem' }}>{b.booking_number}</td>
                          <td>{b.quantity}</td>
                          <td>
                            <span className={`badge ${
                              b.status === 'COMPLETED' ? 'badge-completed' :
                              b.status === 'ACCEPTED' || b.status === 'CONFIRMED' ? 'badge-confirmed' :
                              'badge-pending'
                            }`}>
                              {b.status}
                            </span>
                          </td>
                          <td style={{ whiteSpace: 'nowrap' }}>
                            {b.created_at ? new Date(b.created_at).toLocaleDateString('en-IN') : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
