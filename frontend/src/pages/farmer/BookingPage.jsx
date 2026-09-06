import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { bookingApi } from '../../services/bookingApi.js';
import { localizeCrop, cropEmoji } from '../../data/crops.js';
import { localizeCentre } from '../../utils/locale.js';
import BookingProgress from '../../components/farmer/BookingProgress.jsx';

const STEP_KEYS = ['sell.stepCrop', 'sell.stepQuantity', 'sell.stepCentre', 'sell.stepSlot', 'sell.stepConfirm', 'sell.stepQueue'];

function formatTime(t) {
  if (!t) return '';
  const [h, m] = t.split(':');
  const hr = parseInt(h, 10);
  return `${((hr - 1) % 12) + 1}:${m} ${hr >= 12 ? 'PM' : 'AM'}`;
}

export default function BookingPage() {
  const { setError: setAuthError } = useAuth();
  const { t, lang } = useLanguage();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const SELL_STEPS = STEP_KEYS.map((k) => ({ label: t(k) }));

  const cultivation = JSON.parse(localStorage.getItem('fp_selected_cultivation') || 'null');
  const centre = JSON.parse(localStorage.getItem('fp_selected_centre') || 'null');
  const slot = JSON.parse(localStorage.getItem('fp_selected_slot') || 'null');

  useEffect(() => {
    if (!cultivation || !centre || !slot) navigate('/sell', { replace: true });
  }, [cultivation, centre, slot, navigate]);

  if (!cultivation || !centre || !slot) return null;

  const handleConfirm = async () => {
    setSubmitting(true); setError(null);
    try {
      const booking = await bookingApi.create({
        cultivation_id: cultivation.cultivation_id,
        centre_id: centre.centre_id,
        slot_id: slot.slot_id,
        quantity_to_sell_quintals: Number(cultivation.quantity_to_sell_quintals),
      });
      localStorage.setItem('fp_last_booking', JSON.stringify(booking));
      localStorage.removeItem('fp_selected_cultivation');
      localStorage.removeItem('fp_selected_centre');
      localStorage.removeItem('fp_selected_slot');
      navigate('/booking-success');
    } catch (e) {
      if (e.status === 401) {
        setAuthError('Session expired');
        navigate('/login', { replace: true });
      } else if (e.status === 409) {
        setError(t('bk.err.slotFull'));
      } else if (e.status === 403) {
        setError(t('bk.err.permission'));
      } else {
        setError(e.message || t('bk.err.generic'));
      }
    }
    finally { setSubmitting(false); }
  };

  return (
    <div className="animate-fadeIn">
      <BookingProgress steps={SELL_STEPS} current={4} />

      <div className="page-header">
        <h1>{t('bk.title')}</h1>
        <p>{t('bk.sub')}</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Crop & Quantity */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>{t('bk.cropTitle')}</h3>
        <div className="summary-row-detail">
          <span className="label">{t('dash.crop')}</span>
          <span className="value">{cropEmoji(cultivation.crop)} {localizeCrop(cultivation.crop, lang)}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">{t('bk.season')}</span>
          <span className="value">{cultivation.season}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">{t('bk.qtyToSell')}</span>
          <span className="value highlight">{Number(cultivation.quantity_to_sell_quintals)} {t('unit.quintals')}</span>
        </div>
      </div>

      {/* Centre */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>{t('bk.centreTitle')}</h3>
        <div className="summary-row-detail">
          <span className="label">{t('dash.centre')}</span>
          <span className="value">{localizeCentre(centre.centre_name, lang)}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">{t('bk.location')}</span>
          <span className="value">{centre.village}, {centre.mandal}</span>
        </div>
        {centre.distance_km != null && (
          <div className="summary-row-detail">
            <span className="label">{t('bk.distance')}</span>
            <span className="value">{Number(centre.distance_km).toFixed(1)} {t('unit.km')}</span>
          </div>
        )}
      </div>

      {/* Slot */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>{t('bk.slotTitle')}</h3>
        <div className="summary-row-detail">
          <span className="label">{t('bk.date')}</span>
          <span className="value">{slot.slot_date}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">{t('bk.time')}</span>
          <span className="value">{formatTime(slot.start_time)} — {formatTime(slot.end_time)}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">{t('bk.availSpots')}</span>
          <span className="value">{slot.maximum_farmers - slot.booked_farmers}</span>
        </div>
      </div>

      {/* Government note */}
      <div className="info-banner" style={{ marginBottom: 24 }}>
        {t('bk.note')}
      </div>

      <div style={{ display: 'flex', gap: 12 }}>
        <button className="btn btn-secondary" onClick={() => navigate(-1)}>
          {t('sell.back')}
        </button>
        <button
          className="btn btn-primary btn-lg"
          style={{ flex: 1 }}
          onClick={handleConfirm}
          disabled={submitting}
        >
          {submitting ? t('bk.creating') : t('bk.confirm')}
        </button>
      </div>
    </div>
  );
}
