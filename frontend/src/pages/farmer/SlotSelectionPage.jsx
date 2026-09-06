import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { centreApi } from '../../services/centreApi.js';
import { mlApi } from '../../services/mlApi.js';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { localizeCentre } from '../../utils/locale.js';
import BookingProgress from '../../components/farmer/BookingProgress.jsx';

const STEP_KEYS = ['sell.stepCrop', 'sell.stepQuantity', 'sell.stepCentre', 'sell.stepSlot', 'sell.stepConfirm', 'sell.stepQueue'];

function formatTime(t) {
  if (!t) return '';
  const [h, m] = t.split(':');
  const hr = parseInt(h, 10);
  const ampm = hr >= 12 ? 'PM' : 'AM';
  return `${((hr - 1) % 12) + 1}:${m} ${ampm}`;
}

function formatDate(d) {
  if (!d) return '';
  try {
    const date = new Date(d + 'T00:00:00');
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch { return d; }
}

function getCongestionColor(level) {
  switch (level) {
    case 'LOW': return { bg: '#dcfce7', text: '#166534', border: '#86efac' };
    case 'MODERATE': return { bg: '#fef3c7', text: '#92400e', border: '#fcd34d' };
    case 'HIGH': return { bg: '#fee2e2', text: '#991b1b', border: '#fca5a5' };
    default: return { bg: '#f3f4f6', text: '#6b7280', border: '#d1d5db' };
  }
}

function getCongestionEmoji(level) {
  switch (level) {
    case 'LOW': return '🟢';
    case 'MODERATE': return '🟡';
    case 'HIGH': return '🔴';
    default: return '⚪';
  }
}

export default function SlotSelectionPage() {
  const { centreId } = useParams();
  const { t, lang } = useLanguage();
  const navigate = useNavigate();
  const [slots, setSlots] = useState([]);
  const [centre, setCentre] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [predictions, setPredictions] = useState({});
  const [predictionsLoading, setPredictionsLoading] = useState(false);

  const SELL_STEPS = STEP_KEYS.map((k) => ({ label: t(k) }));

  // Get crop from localStorage (set during booking flow).
  // NOTE: this value is sent to the ML prediction API, which expects the
  // English crop name, so it must NOT be localized.
  const getCrop = () => {
    try {
      const cultivation = JSON.parse(localStorage.getItem('fp_selected_cultivation') || '{}');
      return cultivation.crop || 'Unknown';
    } catch {
      return 'Unknown';
    }
  };

  useEffect(() => {
    Promise.all([
      centreApi.getById(centreId),
      centreApi.getSlots(centreId),
    ])
      .then(([c, s]) => { setCentre(c); setSlots(s); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [centreId]);

  // Fetch ML predictions for all active slots
  useEffect(() => {
    if (slots.length === 0 || !centre) return;

    const activeSlots = slots.filter(s => s.is_active);
    if (activeSlots.length === 0) return;

    setPredictionsLoading(true);
    const crop = getCrop();

    const predictionPromises = activeSlots.map(slot => {
      const slotHour = parseInt(slot.start_time.split(':')[0], 10);
      return mlApi.getSlotPrediction({
        centreId: centreId,
        slotDate: slot.slot_date,
        slotHour: slotHour,
        crop: crop,
        slotCapacity: slot.maximum_farmers,
        currentBookings: slot.booked_farmers,
      })
        .then(pred => ({ slotId: slot.slot_id, prediction: pred }))
        .catch(() => ({
          slotId: slot.slot_id,
          prediction: {
            congestion_level: 'UNKNOWN',
            predicted_wait_minutes: 0,
            message: 'AI prediction temporarily unavailable.',
          },
        }));
    });

    Promise.all(predictionPromises)
      .then(results => {
        const predMap = {};
        results.forEach(({ slotId, prediction }) => {
          predMap[slotId] = prediction;
        });
        setPredictions(predMap);
      })
      .finally(() => setPredictionsLoading(false));
  }, [slots, centre, centreId]);

  const handleSelectSlot = (slot) => {
    localStorage.setItem('fp_selected_slot', JSON.stringify(slot));
    navigate('/booking');
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>{t('slot.loading')}</p></div>;

  const activeSlots = slots.filter(s => s.is_active);

  // Group slots by date
  const slotsByDate = {};
  activeSlots.forEach(s => {
    if (!slotsByDate[s.slot_date]) slotsByDate[s.slot_date] = [];
    slotsByDate[s.slot_date].push(s);
  });

  return (
    <div className="animate-fadeIn">
      <BookingProgress steps={SELL_STEPS} current={3} />

      <div className="page-header">
        <h1>🕐 {t('slot.title')}</h1>
        {centre && (
          <p>
            <strong>{localizeCentre(centre.centre_name, lang)}</strong>
            {centre.village && <> — {centre.village}, {centre.mandal}</>}
          </p>
        )}
      </div>

      {error && <div className="error-banner">{error}</div>}

      {activeSlots.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon">🕐</div>
          <h3>{t('slot.none')}</h3>
          <p>{t('slot.noneDesc')}</p>
        </div>
      ) : (
        Object.entries(slotsByDate).map(([date, dateSlots]) => (
          <div key={date} style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: '.95rem', fontWeight: 700, color: 'var(--gray-700)', marginBottom: 12 }}>
              📅 {formatDate(date)}
            </h3>
            <div className="card-grid card-grid-2">
              {dateSlots.map((s) => {
                const available = s.maximum_farmers - s.booked_farmers;
                const isFull = available <= 0;
                const isAlmostFull = available > 0 && available <= 2;
                const pred = predictions[s.slot_id];
                const congestionLevel = pred?.congestion_level || 'UNKNOWN';
                const waitMinutes = pred?.predicted_wait_minutes || 0;
                const congestionColor = getCongestionColor(congestionLevel);
                const congestionEmoji = getCongestionEmoji(congestionLevel);

                return (
                  <div
                    className={`slot-card ${isFull ? 'full' : ''}`}
                    key={s.slot_id}
                    onClick={() => !isFull && handleSelectSlot(s)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                      <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>
                        {formatTime(s.start_time)} — {formatTime(s.end_time)}
                      </div>
                      {isFull ? (
                        <span className="badge badge-full">{t('slot.full')}</span>
                      ) : isAlmostFull ? (
                        <span className="badge badge-waiting">{t('slot.almostFull')}</span>
                      ) : (
                        <span className="badge badge-active">{t('slot.available')}</span>
                      )}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '.85rem', color: 'var(--gray-500)' }}>
                      <span>{t('slot.booked', { n: s.booked_farmers, m: s.maximum_farmers })}</span>
                      <span style={{ color: isFull ? 'var(--red-500)' : 'var(--green-700)', fontWeight: 600 }}>
                        {t('slot.availN', { n: available })}
                      </span>
                    </div>

                    {/* ML Congestion Prediction */}
                    {!isFull && (
                      <div style={{
                        marginTop: 12,
                        padding: '10px 12px',
                        borderRadius: 8,
                        backgroundColor: congestionColor.bg,
                        border: `1px solid ${congestionColor.border}`,
                        fontSize: '.85rem',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                          <span style={{ fontWeight: 600, color: congestionColor.text }}>
                            {congestionEmoji} {t('slot.aiPrediction')}: {congestionLevel === 'UNKNOWN' ? t('slot.calculating') : t('slot.congestion', { level: congestionLevel })}
                          </span>
                        </div>
                        {congestionLevel !== 'UNKNOWN' && waitMinutes > 0 && (
                          <div style={{ color: congestionColor.text, fontSize: '.82rem' }}>
                            ⏱️ {t('dash.estWait')}: ~{waitMinutes} {t('unit.min')}
                          </div>
                        )}
                        {pred?.message && (
                          <div style={{ color: 'var(--gray-500)', fontSize: '.78rem', marginTop: 4 }}>
                            {pred.message}
                          </div>
                        )}
                      </div>
                    )}

                    {!isFull && (
                      <button
                        className="btn btn-primary btn-block"
                        style={{ marginTop: 12 }}
                        onClick={(e) => { e.stopPropagation(); handleSelectSlot(s); }}
                      >
                        {t('slot.select')}
                      </button>
                    )}
                    {isFull && (
                      <div style={{ marginTop: 10, fontSize: '.82rem', color: 'var(--red-500)', textAlign: 'center', fontWeight: 500 }}>
                        {t('slot.unavailable')}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}

      {predictionsLoading && (
        <div style={{ textAlign: 'center', padding: '12px 0', color: 'var(--gray-500)', fontSize: '.85rem' }}>
          🤖 {t('slot.loadingAi')}
        </div>
      )}

      <div style={{ marginTop: 8 }}>
        <button className="btn btn-secondary" onClick={() => navigate('/centres')}>
          {t('slot.back')}
        </button>
      </div>
    </div>
  );
}
