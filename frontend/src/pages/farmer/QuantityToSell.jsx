import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { cultivationApi } from '../../services/cultivationApi.js';
import { CATEGORY_EMOJI, getCropCategory } from '../../data/crops.js';
import BookingProgress from '../../components/farmer/BookingProgress.jsx';

const SELL_STEPS = [
  { label: 'Crop' },
  { label: 'Quantity' },
  { label: 'Centre' },
  { label: 'Slot' },
  { label: 'Confirm' },
  { label: 'Queue' },
];

export default function QuantityToSell() {
  const navigate = useNavigate();
  const [cultivation, setCultivation] = useState(null);
  const [quantity, setQuantity] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const raw = localStorage.getItem('fp_selected_cultivation');
    if (!raw) { navigate('/sell', { replace: true }); return; }
    const cult = JSON.parse(raw);
    setCultivation(cult);
    setQuantity(String(cult.quantity_to_sell_quintals || ''));
  }, [navigate]);

  if (!cultivation) return null;

  const produced = Number(cultivation.quantity_produced_quintals);
  const qtyNum = parseFloat(quantity);
  const isValid = !isNaN(qtyNum) && qtyNum > 0 && qtyNum <= produced;
  const quantityKept = isValid ? (produced - qtyNum) : 0;
  const cat = getCropCategory(cultivation.crop);
  const emoji = CATEGORY_EMOJI[cat] || '🌱';

  const handleContinue = async () => {
    if (!isValid) return;
    setSaving(true); setError(null);
    try {
      await cultivationApi.updateQuantityToSell(cultivation.cultivation_id, qtyNum);
      const updated = { ...cultivation, quantity_to_sell_quintals: qtyNum };
      localStorage.setItem('fp_selected_cultivation', JSON.stringify(updated));
      navigate('/sell/summary');
    } catch (e) {
      if (e.message.includes('already confirmed') || e.message.includes('below')) {
        setError('Cannot reduce below the quantity already confirmed in active bookings.');
      } else if (e.message.includes('exceed') || e.message.includes('greater')) {
        setError('Quantity cannot exceed the total quantity produced.');
      } else {
        setError(e.message || 'Please enter a valid quantity.');
      }
    }
    finally { setSaving(false); }
  };

  return (
    <div>
      <BookingProgress steps={SELL_STEPS} current={1} />

      <div className="page-header">
        <h1>📊 Enter Quantity to Sell</h1>
        <p>How much of <strong>{cultivation.crop}</strong> do you want to sell?</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Crop info */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <span style={{ fontSize: '2rem' }}>{emoji}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>{cultivation.crop}</div>
            <div style={{ fontSize: '.85rem', color: 'var(--gray-500)' }}>{cultivation.season}</div>
          </div>
        </div>
        <div style={{ fontSize: '.72rem', color: 'var(--gray-500)', textTransform: 'uppercase', letterSpacing: '.5px', fontWeight: 500 }}>Total Quantity Produced</div>
        <div style={{ fontWeight: 700, fontSize: '1.1rem', marginTop: 2 }}>{produced} quintals</div>
      </div>

      {/* Quantity input */}
      <div className="quantity-display">
        <div className="qty-label">How much do you want to sell?</div>
        <div className="quantity-input-group">
          <input
            className="form-input"
            type="number"
            step="0.01"
            min="0.01"
            max={produced}
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="0"
          />
          <span className="unit">Quintals</span>
        </div>
        {!isNaN(qtyNum) && qtyNum > produced && (
          <div style={{ fontSize: '.82rem', color: 'var(--red-500)', marginTop: 8 }}>
            Cannot exceed total produced ({produced} quintals)
          </div>
        )}
      </div>

      {/* Breakdown */}
      {isValid && (
        <div className="card" style={{ marginBottom: 20, background: 'var(--green-50)', border: '1px solid var(--green-200)' }}>
          <div className="summary-row-detail">
            <span className="label">Total Quantity Produced</span>
            <span className="value">{produced} Quintals</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">Quantity You Want to Sell</span>
            <span className="value highlight">{qtyNum} Quintals</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">Quantity You Keep</span>
            <span className="value keep">{quantityKept} Quintals</span>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 12 }}>
        <button className="btn btn-secondary" onClick={() => navigate('/sell')}>
          ← Back
        </button>
        <button
          className="btn btn-primary btn-lg"
          style={{ flex: 1 }}
          onClick={handleContinue}
          disabled={saving || !isValid}
        >
          {saving ? 'Saving...' : 'Continue →'}
        </button>
      </div>
    </div>
  );
}
