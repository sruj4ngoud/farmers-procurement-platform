import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';

export default function AdminIssuesPage() {
  const [issues, setIssues] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ issue_type: 'OTHER', severity: 'MEDIUM', entity_type: 'booking', entity_id: '', description: '' });
  const [resolveComment, setResolveComment] = useState('');

  const load = async () => {
    try { setIssues(await adminApi.getIssues(filter || undefined)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleCreate = async () => {
    if (!form.description.trim()) { setError('Description required'); return; }
    try { await adminApi.createIssue(form); setShowForm(false); setForm({ issue_type: 'OTHER', severity: 'MEDIUM', entity_type: 'booking', entity_id: '', description: '' }); load(); }
    catch (e) { setError(e.message); }
  };

  const handleResolve = async (issueId) => {
    try { await adminApi.updateIssue(issueId, { status: 'RESOLVED', resolution_comment: resolveComment }); setResolveComment(''); load(); }
    catch (e) { setError(e.message); }
  };

  const sevColor = { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444' };

  if (loading) return <div className="page-container"><p>Loading issues...</p></div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Issues & Exceptions</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>{showForm ? 'Cancel' : '+ Report Issue'}</button>
      </div>
      {error && <div className="error-banner" style={{ margin: '1rem 0' }}>{error}</div>}

      <div style={{ display: 'flex', gap: '6px', margin: '1rem 0' }}>
        {[{ l: 'All', v: '' }, { l: 'Open', v: 'OPEN' }, { l: 'In Progress', v: 'IN_PROGRESS' }, { l: 'Resolved', v: 'RESOLVED' }].map(f => (
          <button key={f.v} className={`btn btn-sm ${filter === f.v ? 'btn-primary' : 'btn-outline'}`} onClick={() => setFilter(f.v)}>{f.l}</button>
        ))}
      </div>

      {showForm && (
        <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div><label style={lbl}>Type</label><select className="form-input" value={form.issue_type} onChange={e => setForm({...form, issue_type: e.target.value})}>
              {['DUPLICATE_BOOKING','QUANTITY_MISMATCH','SLOT_CAPACITY_CONFLICT','CENTRE_INACTIVE','PAYMENT_FAILED','BANK_VERIFICATION_FAILED','BOOKING_PENDING_TOO_LONG','UNUSUAL_QUANTITY','PROCUREMENT_DELAYED','OTHER'].map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
            </select></div>
            <div><label style={lbl}>Severity</label><select className="form-input" value={form.severity} onChange={e => setForm({...form, severity: e.target.value})}>
              {['LOW','MEDIUM','HIGH','CRITICAL'].map(s => <option key={s} value={s}>{s}</option>)}
            </select></div>
            <div><label style={lbl}>Entity ID</label><input className="form-input" value={form.entity_id} onChange={e => setForm({...form, entity_id: e.target.value})} placeholder="Optional" /></div>
          </div>
          <div><label style={lbl}>Description</label><textarea className="form-input" rows={2} value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
          <button className="btn btn-primary" style={{ marginTop: '0.75rem' }} onClick={handleCreate}>Create Issue</button>
        </div>
      )}

      {issues.length === 0 ? <p style={{ color: '#94a3b8' }}>No issues found.</p> : issues.map(i => (
        <div key={i.issue_id} style={{ background: 'white', borderRadius: '12px', padding: '1rem 1.25rem', marginBottom: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.05)', borderLeft: `4px solid ${sevColor[i.severity] || '#94a3b8'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontWeight: 700, color: '#1e293b' }}>{i.issue_type.replace(/_/g, ' ')}</span>
              <span style={{ marginLeft: '8px', padding: '2px 6px', borderRadius: '8px', fontSize: '0.7rem', fontWeight: 600, background: `${sevColor[i.severity]}20`, color: sevColor[i.severity] }}>{i.severity}</span>
            </div>
            <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem', fontWeight: 600, background: i.status === 'RESOLVED' ? '#dcfce7' : i.status === 'OPEN' ? '#fef3c7' : '#dbeafe', color: i.status === 'RESOLVED' ? '#16a34a' : i.status === 'OPEN' ? '#92400e' : '#3b82f6' }}>{i.status}</span>
          </div>
          <p style={{ margin: '0.5rem 0', color: '#475569', fontSize: '0.9rem' }}>{i.description}</p>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{i.entity_type}: {i.entity_id} | {new Date(i.created_at).toLocaleString()}</div>
          {i.status !== 'RESOLVED' && (
            <div style={{ display: 'flex', gap: '8px', marginTop: '0.5rem' }}>
              <input className="form-input" placeholder="Resolution comment..." value={resolveComment} onChange={e => setResolveComment(e.target.value)} style={{ flex: 1 }} />
              <button className="btn btn-sm btn-primary" onClick={() => handleResolve(i.issue_id)}>Resolve</button>
            </div>
          )}
          {i.resolution_comment && <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: '#f0fdf4', borderRadius: '6px', fontSize: '0.85rem', color: '#166534' }}>Resolved: {i.resolution_comment}</div>}
        </div>
      ))}
    </div>
  );
}

const lbl = { display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' };
