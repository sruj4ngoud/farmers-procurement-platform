import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';

export default function AdminAuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    adminApi.getAuditLogs().then(d => { setLogs(d); setLoading(false); }).catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <div className="page-container"><p>Loading audit logs...</p></div>;

  return (
    <div className="page-container">
      <h1>Audit Logs</h1>
      <p style={{ color: '#64748b', marginBottom: '1rem' }}>Every important admin action is recorded here.</p>
      {error && <div className="error-banner">{error}</div>}
      {logs.length === 0 ? <p style={{ color: '#94a3b8' }}>No audit logs found.</p> : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <thead><tr style={{ background: '#f1f5f9' }}>
              <th style={th}>Time</th><th style={th}>User</th><th style={th}>Action</th><th style={th}>Entity</th><th style={th}>Old</th><th style={th}>New</th>
            </tr></thead>
            <tbody>{logs.map(l => (
              <tr key={l.log_id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={td}>{new Date(l.created_at).toLocaleString()}</td>
                <td style={td}>{l.username || 'system'}</td>
                <td style={td}><span style={{ fontWeight: 600 }}>{l.action.replace(/_/g, ' ')}</span></td>
                <td style={td}>{l.entity_type}: {l.entity_id?.slice(0, 8)}...</td>
                <td style={td}>{l.old_value || '-'}</td>
                <td style={td}>{l.new_value || '-'}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const th = { padding: '0.6rem 0.75rem', textAlign: 'left', fontWeight: 600, color: '#475569', fontSize: '0.8rem' };
const td = { padding: '0.6rem 0.75rem', color: '#334155', fontSize: '0.85rem' };
