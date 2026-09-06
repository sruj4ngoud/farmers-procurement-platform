import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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

export default function EntrySummary() {
  const navigate = useNavigate();
  const [cultivation, setCultivation] = useState(null);

  useEffect(() => {
    const raw = localStorage.getItem('fp_selected_cultivation');
    if (!raw) { navigate('/sell', { replace: true }); return; }
    setCultivation(JSON.parse(raw));
  }, [navigate]);

  if (!cultivation) return null;

  const produced = Number(cultivation.quantity_produced_quintals);
  const toSell = Number(cultivation.quantity_to_sell_quintals);
  const area = Number(cultivation.cultivated_area_acres);
  const kept = produced - toSell;
  const cat = getCropCategory(cultivation.crop);
  const emoji = CATEGORY_EMOJI[cat] || '🌱';

  return (
    <div>
      <BookingProgress steps={SELL_STEPS} current={1} />

      <div className="page-header">
        <h1>📋 Your Entry Summary</h1>
        <p>Review your crop and quantity details before selecting a procurement centre</p>
      </div>

      <div className="summary-card">
        <h2 style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.5rem' }}>{emoji}</span> Entry Summary
        </h2>

        <div className="summary-row-detail">
          <span className="label">Crop</span>
          <span className="value">{cultivation.crop}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">Season</span>
          <span className="value">{cultivation.season}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">Cultivated Area</span>
          <span className="value">{area} Acres</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">Total Quantity Produced</span>
          <span className="value">{produced} Quintals</span>
        </div>
        <div className="summary-row-detail" style={{ borderBottom: '2px solid var(--green-200)', paddingBottom: 14 }}>
          <span className="label" style={{ fontWeight: 600 }}>Quantity You Want to Sell</span>
          <span className="value highlight">{toSell} Quintals</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">Quantity You Keep</span>
          <span className="value keep">{kept} Quintals</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12 }}>
        <button className="btn btn-secondary" onClick={() => navigate('/sell/quantity')}>
          ← Edit Quantity
        </button>
        <button
          className="btn btn-primary btn-lg"
          style={{ flex: 1 }}
          onClick={() => navigate('/centres')}
        >
          Confirm Details →
        </button>
      </div>
    </div>
  );
}
