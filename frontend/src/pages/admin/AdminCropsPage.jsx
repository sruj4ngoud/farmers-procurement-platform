import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';

export default function AdminCropsPage() {
  const [crops, setCrops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCrop, setEditingCrop] = useState(null);
  const [form, setForm] = useState({ crop_name: '', crop_category: 'Cereal', msp_per_quintal: '', is_active: true });

  const categories = ['Cereal', 'Pulse', 'Oilseed', 'Cash Crop', 'Fiber Crop', 'Plantation', 'Spice', 'Vegetable', 'Tuber', 'Fruit'];

  const load = async () => {
    try { setCrops(await adminApi.getCrops()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    try {
      if (editingCrop) {
        await adminApi.updateCrop(editingCrop.crop_id, {
          ...form,
          msp_per_quintal: form.msp_per_quintal ? parseFloat(form.msp_per_quintal) : null,
        });
      } else {
        await adminApi.createCrop({
          ...form,
          msp_per_quintal: form.msp_per_quintal ? parseFloat(form.msp_per_quintal) : null,
        });
      }
      setShowForm(false); setEditingCrop(null);
      setForm({ crop_name: '', crop_category: 'Cereal', msp_per_quintal: '', is_active: true });
      load();
    } catch (e) { setError(e.message); }
  };

  const handleToggleActive = async (crop) => {
    try {
      await adminApi.updateCrop(crop.crop_id, { is_active: !crop.is_active });
      load();
    } catch (e) { setError(e.message); }
  };

  const handleEdit = (crop) => {
    setEditingCrop(crop);
    setForm({ crop_name: crop.crop_name, crop_category: crop.crop_category, msp_per_quintal: crop.msp_per_quintal || '', is_active: crop.is_active });
    setShowForm(true);
  };

  if (loading) return <div className="page-container"><p>Loading crops...</p></div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Crop Management</h1>
        <button className="btn btn-primary" onClick={() => { setShowForm(!showForm); setEditingCrop(null); setForm({ crop_name: '', crop_category: 'Cereal', msp_per_quintal: '', is_active: true }); }}>
          {showForm ? 'Cancel' : '+ Add Crop'}
        </button>
      </div>
      {error && <div className="error-banner" style={{ margin: '1rem 0' }}>{error}</div>}

      {showForm && (
        <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0', marginBottom: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem' }}>{editingCrop ? 'Edit Crop' : 'Add New Crop'}</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>Crop Name</label>
              <input className="form-input" value={form.crop_name} onChange={e => setForm({...form, crop_name: e.target.value})} disabled={!!editingCrop} />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>Category</label>
              <select className="form-input" value={form.crop_category} onChange={e => setForm({...form, crop_category: e.target.value})}>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#475569', marginBottom: '4px' }}>MSP (₹/Quintal)</label>
              <input className="form-input" type="number" value={form.msp_per_quintal} onChange={e => setForm({...form, msp_per_quintal: e.target.value})} />
            </div>
          </div>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={handleSave}>{editingCrop ? 'Update' : 'Create'}</button>
        </div>
      )}

      <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <thead>
            <tr style={{ background: '#f1f5f9' }}>
              <th style={thStyle}>Crop Name</th>
              <th style={thStyle}>Category</th>
              <th style={thStyle}>MSP (₹/Q)</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {crops.map((c) => (
              <tr key={c.crop_id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                <td style={tdStyle}>{c.crop_name}</td>
                <td style={tdStyle}>{c.crop_category}</td>
                <td style={tdStyle}>{c.msp_per_quintal ? `₹${c.msp_per_quintal.toLocaleString()}` : '-'}</td>
                <td style={tdStyle}>
                  <span style={{ padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600, background: c.is_active ? '#dcfce7' : '#fee2e2', color: c.is_active ? '#16a34a' : '#dc2626' }}>
                    {c.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={tdStyle}>
                  <button className="btn btn-sm btn-outline" style={{ marginRight: 8 }} onClick={() => handleEdit(c)}>Edit</button>
                  <button className="btn btn-sm" style={{ color: c.is_active ? '#dc2626' : '#16a34a' }} onClick={() => handleToggleActive(c)}>
                    {c.is_active ? 'Deactivate' : 'Activate'}
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
