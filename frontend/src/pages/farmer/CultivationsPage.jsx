import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext.jsx';
import { useNavigate, Link } from 'react-router-dom';
import { farmerApi } from '../../services/farmerApi.js';
import { cultivationApi } from '../../services/cultivationApi.js';
import { CATEGORY_EMOJI, getCropCategory } from '../../data/crops.js';

export default function CultivationsPage() {
  const { farmer } = useAuth();
  const navigate = useNavigate();
  const [cultivations, setCultivations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    farmerApi.getDashboard()
      .then((d) => setCultivations(d.cultivations || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (cult) => {
    const qty = parseFloat(editValue);
    if (isNaN(qty) || qty <= 0) { setError('Quantity must be greater than 0'); return; }
    if (qty > Number(cult.quantity_produced_quintals)) { setError('Quantity cannot exceed total produced'); return; }
    setSaving(true); setError(null); setSuccessMsg('');
    try {
      const res = await cultivationApi.updateQuantityToSell(cult.cultivation_id, qty);
      setCultivations((prev) => prev.map((c) =>
        c.cultivation_id === cult.cultivation_id ? { ...c, quantity_to_sell_quintals: res.quantity_to_sell_quintals } : c
      ));
      setEditingId(null);
      setSuccessMsg(`${cult.crop}: quantity to sell updated to ${res.quantity_to_sell_quintals} quintals`);
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (e) {
      if (e.message.includes('already confirmed') || e.message.includes('below')) {
        setError('Cannot reduce below the quantity already confirmed in active bookings.');
      } else {
        setError(e.message);
      }
    }
    finally { setSaving(false); }
  };

  const handleProceedToSell = (cult) => {
    localStorage.setItem('fp_selected_cultivation', JSON.stringify(cult));
    navigate('/sell/quantity');
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading crops...</p></div>;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>🌾 My Crops</h1>
          <p>Manage your cultivation records and set how much you want to sell</p>
        </div>
        <Link to="/cultivations/add" className="btn btn-primary">➕ Add Crop</Link>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {successMsg && <div className="success-banner">{successMsg}</div>}

      {cultivations.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon">🌾</div>
          <h3>No cultivation records found</h3>
          <p>Contact your agricultural office to register crops.</p>
        </div>
      ) : (
        <div className="card-grid">
          {cultivations.map((c) => {
            const produced = Number(c.quantity_produced_quintals);
            const toSell = Number(c.quantity_to_sell_quintals);
            const area = Number(c.cultivated_area_acres);
            const remaining = produced - toSell;
            const isEditing = editingId === c.cultivation_id;
            const cat = getCropCategory(c.crop);
            const emoji = CATEGORY_EMOJI[cat] || '🌱';
            return (
              <div className="card" key={c.cultivation_id}>
                <div className="card-header">
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: '1.3rem' }}>{emoji}</span> {c.crop}
                  </h3>
                  <span className="badge badge-confirmed">{c.season}</span>
                </div>
                <div style={{ fontSize: '.82rem', color: 'var(--gray-500)', marginBottom: 14 }}>{cat}</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                  <div>
                    <div style={{ fontSize: '.72rem', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '.5px', fontWeight: 500 }}>Cultivated Area</div>
                    <div style={{ fontWeight: 700, fontSize: '1.05rem', marginTop: 2 }}>{area} acres</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '.72rem', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '.5px', fontWeight: 500 }}>Quantity Produced</div>
                    <div style={{ fontWeight: 700, fontSize: '1.05rem', marginTop: 2 }}>{produced} quintals</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '.72rem', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '.5px', fontWeight: 500 }}>Quantity to Sell</div>
                    <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--green-700)', marginTop: 2 }}>{toSell} quintals</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '.72rem', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '.5px', fontWeight: 500 }}>Quantity Kept</div>
                    <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--blue-600)', marginTop: 2 }}>{remaining > 0 ? remaining : 0} quintals</div>
                  </div>
                </div>

                {isEditing ? (
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      className="form-input"
                      type="number"
                      step="0.01"
                      min="0.01"
                      max={produced}
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      placeholder={`Max ${produced}`}
                      autoFocus
                    />
                    <button className="btn btn-primary btn-sm" onClick={() => handleSave(c)} disabled={saving}>
                      {saving ? '...' : 'Save'}
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => setEditingId(null)}>Cancel</button>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button className="btn btn-outline btn-sm" onClick={() => { setEditingId(c.cultivation_id); setEditValue(String(toSell)); }}>
                      ✏️ Update Quantity
                    </button>
                    <button className="btn btn-primary btn-sm" onClick={() => handleProceedToSell(c)}>
                      🌾 Sell This Crop →
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
