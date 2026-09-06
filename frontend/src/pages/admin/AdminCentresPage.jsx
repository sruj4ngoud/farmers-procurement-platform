import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import { useAdmin } from '../../context/AdminContext.jsx';

export default function AdminCentresPage() {
  const { admin } = useAdmin();
  const [centres, setCentres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await adminApi.getCentres();
        if (!cancelled) setCentres(data);
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) return <div className="page-container"><p>Loading centres...</p></div>;
  if (error) return <div className="page-container"><div className="error-banner">{error}</div></div>;

  const statusColor = (s) => {
    if (s === 'ACTIVE') return '#22c55e';
    if (s === 'LIMITED') return '#f59e0b';
    if (s === 'FULL') return '#ef4444';
    return '#94a3b8';
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Procurement Centres</h1>
        <p style={{ color: '#64748b' }}>{centres.length} centre(s)</p>
      </div>

      <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <thead>
            <tr style={{ background: '#f1f5f9' }}>
              <th style={thStyle}>Centre Name</th>
              <th style={thStyle}>Code</th>
              <th style={thStyle}>Agency</th>
              <th style={thStyle}>Mandal</th>
              <th style={thStyle}>Capacity</th>
              <th style={thStyle}>Status</th>
            </tr>
          </thead>
          <tbody>
            {centres.map((c) => (
              <tr key={c.centre_id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={tdStyle}>{c.centre_name}</td>
                <td style={tdStyle}>{c.centre_code}</td>
                <td style={tdStyle}>{c.agency}</td>
                <td style={tdStyle}>{c.mandal}</td>
                <td style={tdStyle}>{c.capacity}</td>
                <td style={tdStyle}>
                  <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600, background: `${statusColor(c.current_status)}20`, color: statusColor(c.current_status) }}>
                    {c.current_status}
                  </span>
                </td>
              </tr>
            ))}
            {centres.length === 0 && (
              <tr><td colSpan="6" style={{ ...tdStyle, textAlign: 'center', color: '#94a3b8' }}>No centres found in this district</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const thStyle = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, color: '#475569', fontSize: '0.85rem' };
const tdStyle = { padding: '0.75rem 1rem', color: '#334155', fontSize: '0.9rem' };
