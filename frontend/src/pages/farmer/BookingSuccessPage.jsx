import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { bookingApi } from '../../services/bookingApi.js';
import { useLanguage } from '../../context/LanguageContext.jsx';
import BookingProgress from '../../components/farmer/BookingProgress.jsx';

const STEP_KEYS = ['sell.stepCrop', 'sell.stepQuantity', 'sell.stepCentre', 'sell.stepSlot', 'sell.stepConfirm', 'sell.stepQueue'];

const STATUS_KEY = {
  PENDING_ADMIN_REVIEW: 'status.pendingReview', ACCEPTED: 'status.accepted',
  AUTO_ACCEPTED: 'status.autoAccepted', REJECTED: 'status.rejected',
  CONFIRMED: 'status.confirmed', CANCELLED: 'status.cancelled', COMPLETED: 'status.completed',
};

export default function BookingSuccessPage() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const booking = JSON.parse(localStorage.getItem('fp_last_booking') || 'null');
  const [generating, setGenerating] = useState(false);
  const [tokenGenerated, setTokenGenerated] = useState(false);
  const [tokenError, setTokenError] = useState(null);

  const SELL_STEPS = STEP_KEYS.map((k) => ({ label: t(k) }));

  useEffect(() => {
    if (!booking) navigate('/dashboard', { replace: true });
  }, [booking, navigate]);

  if (!booking) return null;

  const handleGenerateToken = async () => {
    setGenerating(true); setTokenError(null);
    try {
      await bookingApi.generateToken(booking.booking_id);
      setTokenGenerated(true);
    } catch (e) {
      if (e.status === 409) setTokenGenerated(true);
      else setTokenError(e.message || t('bs.err.token'));
    }
    finally { setGenerating(false); }
  };

  return (
    <div className="animate-fadeIn">
      <BookingProgress steps={SELL_STEPS} current={5} />

      {/* Success card */}
      <div className="card" style={{ textAlign: 'center', padding: '40px 24px', marginBottom: 24 }}>
        <div style={{ fontSize: '3.5rem', marginBottom: 12 }}>✅</div>
        <h1 style={{ color: 'var(--green-700)', marginBottom: 8, fontSize: '1.4rem' }}>{t('bs.success')}</h1>
        <p style={{ color: 'var(--gray-600)', marginBottom: 28, fontSize: '.92rem' }}>
          {t('bs.sub')}
        </p>

        <div className="summary-card" style={{ textAlign: 'left', maxWidth: 480, margin: '0 auto', border: 'none', padding: 0, background: 'transparent' }}>
          <div className="summary-row-detail">
            <span className="label">{t('bs.bookingNumber')}</span>
            <span className="value" style={{ fontFamily: 'monospace' }}>{booking.booking_number}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('dash.quantity')}</span>
            <span className="value">{Number(booking.quantity_to_sell_quintals)} {t('unit.quintals')}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bs.status')}</span>
            <span className="value"><span className="badge badge-confirmed">{t(STATUS_KEY[booking.booking_status] || 'status.pendingReview')}</span></span>
          </div>
        </div>
      </div>

      {/* Queue Token */}
      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginBottom: 14, fontSize: '1rem', fontWeight: 700 }}>{t('bs.tokenTitle')}</h3>
        {tokenGenerated ? (
          <div className="success-banner">
            {t('bs.tokenDone')}
          </div>
        ) : (
          <>
            <p style={{ fontSize: '.88rem', color: 'var(--gray-600)', marginBottom: 14 }}>
              {t('bs.tokenDesc')}
            </p>
            {tokenError && <div className="error-banner">{tokenError}</div>}
            <button className="btn btn-primary btn-lg btn-block" onClick={handleGenerateToken} disabled={generating}>
              {generating ? t('bs.generating') : t('bs.generate')}
            </button>
          </>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {tokenGenerated && (
          <Link to={`/queue/${booking.booking_id}`} className="btn btn-primary" style={{ flex: 1 }}>
            {t('bs.viewQueue')}
          </Link>
        )}
        <Link to={`/booking-detail/${booking.booking_id}`} className="btn btn-outline" style={{ flex: 1 }}>
          {t('bs.details')}
        </Link>
        <Link to="/dashboard" className="btn btn-secondary" style={{ flex: 1 }}>
          {t('bs.dashboard')}
        </Link>
      </div>
    </div>
  );
}
