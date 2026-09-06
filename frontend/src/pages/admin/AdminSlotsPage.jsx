import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';

export default function AdminSlotsPage() {
  const [slots, setSlots] = useState([]);
  const [centres, setCentres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ centre_id: '', slot_date: '', start_time: '09:00', end_time: '12:00', maximum_farmers: 10 });

  const load = async () => {
    try {
      const [s, c] = await Promise.all([adminApi.getSlots(), adminApi.getCentres()]);
      setSlots(s); setCentres(c);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    try {
      if (!form.centre_id || !form.slot_date) { setError('Select centre and date'); return; }
      await adminApi.createSlot(form);
      setShowForm(false);
      setForm({ centre_id: '', slot_date: '', start_time: '09:00', end_time: '12:00', maximum_farmers: 10 });
      load();
    } catch (e) { setError(e.message); }
  };

  const handleToggleActive = async (slot) => {
    try {
      await adminApi.updateSlot(slot.slot_id, { is_active: !slot.is_active });
      load();
    } catch (e) { setError(e.message); }
  };

  if (loading) return <div className="page-container"><p>Loading slots...</p></div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Slot Management</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Create Slot'}
        </button>
      </div>
      {error && <div className="error-banner" style={{ margin: '1rem 0' }}>{error}</div>}

      {showForm && (
        <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem' }}>Create New Slot</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>Centre</label>
              <select className="form-input" value={form.centre_id} onChange={e => setForm({...form, centre_id: e.target.value})}>
                <option value="">Select...</option>
                {centres.map(c => <option key={c.centre_id} value={c.centre_id}>{c.centre_name}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>Date</label>
              <input className="form-input" type="date" value={form.slot_date} onChange={e => setForm({...form, slot_date: e.target.value})} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>Start Time</label>
              <input className="form-input" type="time" value={form.start_time} onChange={e => setForm({...form, start_time: e.target.value})} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>End Time</label>
              <input className="form-input" type="time" value={form.end_time} onChange={e => setForm({...form, end_time: e.target.value})} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>Max Farmers</label>
              <input className="form-input" type="number" min="1" value={form.maximum_farmers} onChange={e => setForm({...form, maximum_farmers: parseInt(e.target.value) || 10})} />
            </div>
          </div>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={handleCreate}>Create Slot</button>
        </div>
      )}

      <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <thead>
            <tr style={{ background: '#f1f5f9' }}>
              <th style={thStyle}>Centre</th>
              <th style={thStyle}>Date</th>
              <th style={thStyle}>Time</th>
              <th style={thStyle}>Booked / Max</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {slots.map((s) => (
              <tr key={s.slot_id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={tdStyle}>{s.centre_name || '-'}</td>
                <td style={tdStyle}>{s.slot_date}</td>
                <td style={tdStyle}>{s.start_time} – {s.end_time}</td>
                <td style={tdStyle}>{s.booked_farmers} / {s.maximum_farmers}</td>
                <td style={tdStyle}>
                  <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600, background: s.is_active ? '#dcfce7' : '#fee2e2', color: s.is_active ? '#16a34a' : '#dc2626' }}>
                    {s.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={tdStyle}>
                  <button className="btn btn-sm" style={{ color: s.is_active ? '#dc2626' : '#16a34a' }} onClick={() => handleToggleActive(s)}>
                    {s.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const thStyle = { padding: '0.75rem 1rem', textAlign: 'left', fontWeight: 600, color: '#475569', fontSize: '0.85rem' };
const tdStyle = { padding: '0.75rem 1rem', color: '#334155', fontSize: '0.9rem' };
