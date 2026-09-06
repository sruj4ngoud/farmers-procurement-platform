import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import { useAdmin } from '../../context/AdminContext.jsx';

export default function AdminBookingsPage() {
  const { admin } = useAdmin();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await adminApi.getBookings();
        if (!cancelled) setBookings(data);
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <div className="page-container"><p>Loading bookings...</p></div>;
  if (error) return <div className="page-container"><div className="error-banner">{error}</div></div>;

  const statusColor = (s) => {
    if (s === 'CONFIRMED') return '#22c55e';
    if (s === 'COMPLETED') return '#3b82f6';
    if (s === 'CANCELLED') return '#ef4444';
    if (s === 'NO_SHOW') return '#f59e0b';
    return '#94a3b8';
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Bookings</h1>
        <p style={{ color: '#64748b' }}>{bookings.length} booking(s)</p>
      </div>

      <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <thead>
            <tr style={{ background: '#f1f5f9' }}>
              <th style={thStyle}>Booking #</th>
              <th style={thStyle}>Quantity (Q)</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Created</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.booking_id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={tdStyle}>{b.booking_number}</td>
                <td style={tdStyle}>{b.quantity_to_sell_quintals}</td>
                <td style={tdStyle}>
                  <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600, background: `${statusColor(b.booking_status)}20`, color: statusColor(b.booking_status) }}>
                    {b.booking_status}
                  </span>
                </td>
                <td style={tdStyle}>{b.created_at ? new Date(b.created_at).toLocaleDateString() : '-'}</td>
              </tr>
            ))}
            {bookings.length === 0 && (
              <tr><td colSpan="4" style={{ ...tdStyle, textAlign: 'center', color: '#94a3b8' }}>No bookings found in this district</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const thStyle = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, color: '#475569', fontSize: '0.85rem' };
const tdStyle = { padding: '0.75rem 1rem', color: '#334155', fontSize: '0.9rem' };
