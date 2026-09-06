import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { bookingApi } from '../../services/bookingApi.js';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { localizeCrop, cropEmoji } from '../../data/crops.js';
import { localizeCentre } from '../../utils/locale.js';

export default function BookingDetailPage() {
  const { bookingId } = useParams();
  const { t, lang } = useLanguage();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    bookingApi.getById(bookingId)
      .then(setBooking)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [bookingId]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>{t('q.loading')}</p></div>;
  if (error) return (
    <div>
      <div className="error-banner">{error}</div>
      <Link to="/dashboard" className="btn btn-secondary">{t('q.error.back')}</Link>
    </div>
  );
  if (!booking) return null;

  const STATUS_KEYS = {
    CONFIRMED: 'status.confirmed', WAITING: 'status.waiting', PROCESSING: 'status.processing',
    COMPLETED: 'status.completed', PENDING: 'status.pendingReview', CANCELLED: 'status.cancelled',
    ACCEPTED: 'status.accepted', REJECTED: 'status.rejected', READY: 'status.ready',
    QUALITY_CHECK: 'status.qualityCheck', AUTO_ACCEPTED: 'status.autoAccepted',
    PENDING_ADMIN_REVIEW: 'status.pendingReview',
  };
  const statusBadge = (s) => {
    const cls = { CONFIRMED: 'badge-confirmed', WAITING: 'badge-waiting', PROCESSING: 'badge-processing', COMPLETED: 'badge-completed', PENDING: 'badge-pending', CANCELLED: 'badge-cancelled', READY: 'badge-active', QUALITY_CHECK: 'badge-processing', ACCEPTED: 'badge-confirmed', AUTO_ACCEPTED: 'badge-confirmed', PENDING_ADMIN_REVIEW: 'badge-pending' };
    const label = STATUS_KEYS[s] ? t(STATUS_KEYS[s]) : s;
    return <span className={`badge ${cls[s] || 'badge-pending'}`}>{label}</span>;
  };

  // Build procurement status steps
  const procurementSteps = [
    { labelKey: 'bd.step0', done: true },
    { labelKey: 'bd.step1', done: true },
    { labelKey: 'bd.step2', done: !!booking.token && ['CALLED', 'PROCESSING', 'COMPLETED'].includes(booking.token?.queue_status) },
    { labelKey: 'bd.step3', done: !!booking.token && ['PROCESSING', 'COMPLETED'].includes(booking.token?.queue_status) },
    { labelKey: 'bd.step4', done: !!booking.procurement && ['QUALITY_CHECK', 'ACCEPTED', 'COMPLETED'].includes(booking.procurement?.procurement_status) },
    { labelKey: 'bd.step5', done: !!booking.procurement && ['ACCEPTED', 'COMPLETED'].includes(booking.procurement?.procurement_status) },
    { labelKey: 'bd.step6', done: booking.procurement?.procurement_status === 'COMPLETED' },
  ];

  const currentStepIdx = procurementSteps.findIndex(s => !s.done);
  const activeStep = currentStepIdx === -1 ? procurementSteps.length - 1 : currentStepIdx;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>{t('bs.details')}</h1>
        <p>{booking.booking_number}</p>
      </div>

      {/* Status summary */}
      <div className="card" style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '.82rem', color: 'var(--gray-500)' }}>{t('bd.status')}</div>
          <div style={{ marginTop: 4 }}>{statusBadge(booking.booking_status)}</div>
        </div>
        <div>
          <div style={{ fontSize: '.82rem', color: 'var(--gray-500)' }}>{t('bd.created')}</div>
          <div style={{ fontWeight: 600, fontSize: '.9rem', marginTop: 4 }}>{new Date(booking.created_at).toLocaleString()}</div>
        </div>
      </div>

      {/* Procurement Status Timeline */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 16, fontSize: '1rem', fontWeight: 700 }}>📦 {t('bd.procurementStatus')}</h3>
        <div className="timeline">
          {procurementSteps.map((step, i) => (
            <div className="timeline-item" key={i}>
              <div className={`timeline-dot ${step.done ? 'done' : i === activeStep ? 'active' : ''}`} />
              <h4>{t(step.labelKey)}</h4>
              {step.done && <p>{t('q.stepDone')}</p>}
              {!step.done && i === activeStep && <p>{t('q.stepHere')}</p>}
              {!step.done && i !== activeStep && <p>{t('q.stepPending')}</p>}
            </div>
          ))}
        </div>
      </div>

      {/* Cultivation */}
      {booking.cultivation && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>🌾 {t('bd.cultivation')}</h3>
          <div className="summary-row-detail">
            <span className="label">{t('dash.crop')}</span>
            <span className="value">{cropEmoji(booking.cultivation.crop)} {localizeCrop(booking.cultivation.crop, lang)}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.season')}</span>
            <span className="value">{booking.cultivation.season}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.totalProduced')}</span>
            <span className="value">{Number(booking.cultivation.quantity_produced_quintals)} {t('unit.quintals')}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.qtyToSell')}</span>
            <span className="value highlight">{Number(booking.cultivation.quantity_to_sell_quintals)} {t('unit.quintals')}</span>
          </div>
        </div>
      )}

      {/* Centre & Slot */}
      {booking.centre && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>📍 {t('bk.centreTitle')}</h3>
          <div className="summary-row-detail">
            <span className="label">{t('bd.centre')}</span>
            <span className="value">{localizeCentre(booking.centre.centre_name, lang)}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.location')}</span>
            <span className="value">{booking.centre.village}, {booking.centre.mandal}, {booking.centre.district}</span>
          </div>
        </div>
      )}

      {booking.slot && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>🕐 {t('bd.slot')}</h3>
          <div className="summary-row-detail">
            <span className="label">{t('bd.date')}</span>
            <span className="value">{booking.slot.slot_date}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.time')}</span>
            <span className="value">{booking.slot.start_time} — {booking.slot.end_time}</span>
          </div>
        </div>
      )}

      {/* Queue Token */}
      {booking.token && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>🎫 {t('bs.tokenTitle')}</h3>
          <div className="summary-row-detail">
            <span className="label">{t('bd.tokenNumber')}</span>
            <span className="value" style={{ fontSize: '1.2rem' }}>#{booking.token.token_number}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.position')}</span>
            <span className="value">{booking.token.position != null ? booking.token.position : '—'}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.status')}</span>
            <span className="value">{statusBadge(booking.token.queue_status)}</span>
          </div>
        </div>
      )}

      {/* Procurement */}
      {booking.procurement && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>📦 {t('bd.procurement')}</h3>
          <div className="summary-row-detail">
            <span className="label">{t('bd.quantitySubmitted')}</span>
            <span className="value">{Number(booking.procurement.quantity_submitted_quintals)} {t('unit.quintals')}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.quantityAccepted')}</span>
            <span className="value">{Number(booking.procurement.quantity_accepted_quintals)} {t('unit.quintals')}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.ratePerQuintal')}</span>
            <span className="value">₹{Number(booking.procurement.price_per_quintal).toLocaleString()}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.status')}</span>
            <span className="value">{statusBadge(booking.procurement.procurement_status)}</span>
          </div>
        </div>
      )}

      {/* Government Payment */}
      {booking.payment && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>💰 {t('bd.govPayment')}</h3>
          <div className="summary-row-detail">
            <span className="label">{t('bd.amountPayable')}</span>
            <span className="value highlight" style={{ fontSize: '1.15rem' }}>₹{Number(booking.payment.amount_payable).toLocaleString()}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bd.status')}</span>
            <span className="value">{statusBadge(booking.payment.payment_status)}</span>
          </div>
          {booking.payment.transaction_reference && (
            <div className="summary-row-detail">
              <span className="label">{t('bd.transactionRef')}</span>
              <span className="value" style={{ fontFamily: 'monospace', fontSize: '.82rem' }}>{booking.payment.transaction_reference}</span>
            </div>
          )}
          <div className="summary-row-detail">
            <span className="label">{t('bd.paymentDirection')}</span>
            <span className="value" style={{ color: 'var(--green-700)' }}>{t('bd.govToFarmer')}</span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {booking.token && (
          <Link to={`/queue/${bookingId}`} className="btn btn-primary">{t('bs.viewQueue')}</Link>
        )}
        <Link to="/dashboard" className="btn btn-secondary">{t('q.error.back')}</Link>
      </div>
    </div>
  );
}