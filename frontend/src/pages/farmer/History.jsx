import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { farmerApi } from '../../services/farmerApi.js';
import { localizeCrop, cropEmoji } from '../../data/crops.js';
import { localizeCentre } from '../../utils/locale.js';
import { History as HistoryIcon, ChevronRight, ClipboardCheck } from 'lucide-react';

const STATUS_KEY = {
  PENDING_ADMIN_REVIEW: 'status.pendingReview',
  ACCEPTED: 'status.accepted',
  AUTO_ACCEPTED: 'status.autoAccepted',
  REJECTED: 'status.rejected',
  CONFIRMED: 'status.confirmed',
  CANCELLED: 'status.cancelled',
  COMPLETED: 'status.completed',
  WAITING: 'status.waiting',
  PROCESSING: 'status.processing',
};

export default function History() {
  const { farmer } = useAuth();
  const { t, lang } = useLanguage();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    farmerApi.getDashboard()
      .then((d) => setBookings(d.bookings || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>{t('hist.loading')}</p></div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>{t('hist.title')}</h1>
        <p>{t('hist.sub')}</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {bookings.length === 0 ? (
        <div className="card empty-state" style={{ padding: '48px 24px' }}>
          <ClipboardCheck size={32} style={{ opacity: 0.3 }} />
          <h3>{t('hist.emptyTitle')}</h3>
          <p>{t('hist.emptyDesc')}</p>
          <Link to="/sell" className="btn btn-primary" style={{ marginTop: 16 }}>{t('nav.sell')}</Link>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>{t('hist.colDate')}</th>
                <th>{t('hist.colCrop')}</th>
                <th>{t('hist.colQty')}</th>
                <th>{t('hist.colCentre')}</th>
                <th>{t('hist.colStatus')}</th>
                <th>{t('hist.colPayment')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.booking_id}>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {new Date(b.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {b.cultivation?.crop ? `${cropEmoji(b.cultivation.crop)} ${localizeCrop(b.cultivation.crop, lang)}` : '—'}
                  </td>
                  <td>{Number(b.quantity_to_sell_quintals)} {t('unit.quintals')}</td>
                  <td>{b.centre?.centre_name ? localizeCentre(b.centre.centre_name, lang) : '—'}</td>
                  <td>
                    <span className={`badge ${
                      b.booking_status === 'COMPLETED' ? 'badge-completed' :
                      b.booking_status === 'ACCEPTED' || b.booking_status === 'CONFIRMED' || b.booking_status === 'AUTO_ACCEPTED' ? 'badge-confirmed' :
                      b.booking_status === 'REJECTED' ? 'badge-rejected' :
                      'badge-pending'
                    }`}>
                      {t(STATUS_KEY[b.booking_status] || 'status.pendingReview')}
                    </span>
                  </td>
                  <td>
                    {b.payment ? (
                      <span className={`badge ${b.payment.payment_status === 'COMPLETED' ? 'badge-completed' : 'badge-pending'}`}>
                        ₹{Number(b.payment.amount_payable).toLocaleString()}
                      </span>
                    ) : '—'}
                  </td>
                  <td>
                    <Link to={`/booking-detail/${b.booking_id}`} style={{
                      color: 'var(--gray-500)', display: 'flex', alignItems: 'center', gap: 2,
                    }}>
                      <ChevronRight size={16} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}