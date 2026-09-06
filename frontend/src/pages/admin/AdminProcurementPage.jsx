import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import { Package, AlertTriangle, CheckCircle2, Save } from 'lucide-react';

export default function AdminProcurementPage() {
  const [procurements, setProcurements] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({});
  const [processing, setProcessing] = useState(false);

  const load = async () => {
    try {
      const data = filter === 'pending'
        ? await adminApi.getPendingProcurements()
        : await adminApi.getAllProcurements();
      setProcurements(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleSelect = (p) => {
    setSelected(p.procurement_id === selected?.procurement_id ? null : p);
    setForm({
      quantity_submitted_quintals: p.submitted_quantity,
      quantity_accepted_quintals: p.accepted_quantity,
      price_per_quintal: p.price_per_quintal,
      remarks: p.remarks || '',
    });
  };

  const handleUpdate = async () => {
    setProcessing(true); setError(null);
    try {
      await adminApi.updateProcurement(selected.booking_id, {
        quantity_submitted_quintals: parseFloat(form.quantity_submitted_quintals),
        quantity_accepted_quintals: parseFloat(form.quantity_accepted_quintals),
        price_per_quintal: parseFloat(form.price_per_quintal),
        remarks: form.remarks,
      });
      setSelected(null); load();
    } catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  const handleComplete = async (bookingId) => {
    setProcessing(true); setError(null);
    try { await adminApi.completeProcurement(bookingId); setSelected(null); load(); }
    catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading...</p></div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>Procurement</h1>
        <p>Verify crop quantities and manage procurement records</p>
      </div>

      {error && <div className="error-banner"><AlertTriangle size={16} />{error}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button className={`btn btn-sm ${filter === 'pending' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setFilter('pending')}>Pending</button>
        <button className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-outline'}`} onClick={() => setFilter('all')}>All</button>
      </div>

      {procurements.length === 0 ? (
        <div className="card empty-state">
          <Package size={32} style={{ opacity: 0.3 }} />
          <h3>No {filter === 'pending' ? 'pending ' : ''}procurements</h3>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Booking</th>
                <th>Farmer</th>
                <th>Crop</th>
                <th>Declared</th>
                <th>Accepted</th>
                <th>Diff</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {procurements.map((p) => (
                <tr key={p.procurement_id} style={{ background: selected?.procurement_id === p.procurement_id ? 'var(--gray-100)' : undefined }}>
                  <td className="font-mono" style={{ fontSize: '0.8rem' }}>{p.booking_number}</td>
                  <td style={{ fontWeight: 600 }}>{p.farmer_name}</td>
                  <td>{p.crop}</td>
                  <td>{p.declared_quantity}Q</td>
                  <td>{p.accepted_quantity}Q</td>
                  <td>
                    {p.quantity_mismatch ? (
                      <span style={{ color: 'var(--error)', fontWeight: 700, fontSize: '0.85rem' }}>
                        {p.quantity_difference > 0 ? '+' : ''}{p.quantity_difference}
                      </span>
                    ) : (
                      <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
                    )}
                  </td>
                  <td>
                    <span className={`badge ${p.procurement_status === 'COMPLETED' ? 'badge-completed' : 'badge-pending'}`}>
                      {p.procurement_status}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-outline btn-xs" onClick={() => handleSelect(p)}>
                      {selected?.procurement_id === p.procurement_id ? 'Close' : 'Edit'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit form */}
      {selected && (
        <div className="card" style={{ marginTop: 16, borderLeft: '3px solid var(--black)' }}>
          <div className="card-header">
            <h3>Edit — {selected.booking_number}</h3>
          </div>

          {/* Quantity comparison */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
            {[
              { label: 'Declared', value: `${selected.declared_quantity} Q` },
              { label: 'Actual Weight', value: `${selected.submitted_quantity} Q` },
              { label: 'Difference', value: selected.quantity_mismatch ? `${selected.quantity_difference > 0 ? '+' : ''}${selected.quantity_difference} Q` : 'Match', highlight: selected.quantity_mismatch },
            ].map((item) => (
              <div key={item.label} style={{
                padding: 14, background: item.highlight ? 'var(--error-light)' : 'var(--gray-100)',
                borderRadius: 4, textAlign: 'center',
              }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: item.highlight ? 'var(--error)' : 'var(--gray-800)' }}>{item.value}</div>
              </div>
            ))}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 12 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Submitted (Q)</label>
              <input className="form-input" type="number" step="0.01" value={form.quantity_submitted_quintals} onChange={e => setForm({...form, quantity_submitted_quintals: e.target.value})} />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Accepted (Q)</label>
              <input className="form-input" type="number" step="0.01" value={form.quantity_accepted_quintals} onChange={e => setForm({...form, quantity_accepted_quintals: e.target.value})} />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Price / Quintal</label>
              <input className="form-input" type="number" step="0.01" value={form.price_per_quintal} onChange={e => setForm({...form, price_per_quintal: e.target.value})} />
            </div>
          </div>

          <div className="form-group">
            <label>Remarks</label>
            <textarea className="form-input" rows={2} value={form.remarks} onChange={e => setForm({...form, remarks: e.target.value})} placeholder="Quality, weight notes..." />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={handleUpdate} disabled={processing}>
              <Save size={14} /> Save Changes
            </button>
            {selected.procurement_status !== 'COMPLETED' && (
              <button className="btn btn-success" onClick={() => handleComplete(selected.booking_id)} disabled={processing}>
                <CheckCircle2 size={14} /> Complete Procurement
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
