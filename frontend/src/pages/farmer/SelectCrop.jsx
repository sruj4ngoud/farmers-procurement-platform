import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { farmerApi } from '../../services/farmerApi.js';
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

export default function SelectCrop() {
  const { farmer } = useAuth();
  const navigate = useNavigate();
  const [cultivations, setCultivations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    farmerApi.getDashboard()
      .then((d) => setCultivations(d.cultivations || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = (cult) => {
    localStorage.setItem('fp_selected_cultivation', JSON.stringify(cult));
    navigate('/sell/quantity');
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading your crops...</p></div>;

  return (
    <div>
      <BookingProgress steps={SELL_STEPS} current={0} />

      <div className="page-header">
        <h1>🌾 Select Your Crop</h1>
        <p>Choose a crop you have already cultivated and want to sell</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {cultivations.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon">🌾</div>
          <h3>No cultivation records found</h3>
          <p>You need to have cultivated crops before you can sell. Contact your agricultural office to register crops.</p>
        </div>
      ) : (
        <div className="card-grid card-grid-2">
          {cultivations.map((c) => {
            const area = Number(c.cultivated_area_acres);
            const produced = Number(c.quantity_produced_quintals);
            const cat = getCropCategory(c.crop);
            const emoji = CATEGORY_EMOJI[cat] || '🌱';
            return (
              <div
                className="crop-card"
                key={c.cultivation_id}
                onClick={() => handleSelect(c)}
              >
                <div className="crop-emoji">{emoji}</div>
                <div className="crop-name">{c.crop}</div>
                <div className="crop-area">{area} acres · {produced} quintals produced</div>
                <div style={{ fontSize: '.75rem', color: 'var(--gray-400)', marginTop: 4 }}>{c.season}</div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: 20 }}>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
}
