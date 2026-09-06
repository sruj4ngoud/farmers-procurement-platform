import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import {
  Eye, Check, X, Clock, ChevronDown, ChevronUp,
  AlertTriangle, ShieldCheck, Users, MapPin, Wheat
} from 'lucide-react';

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState([]);
  const [filter, setFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [rejectComment, setRejectComment] = useState('');
  const [processing, setProcessing] = useState(false);
  const [autoAcceptResult, setAutoAcceptResult] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = filter === 'pending'
        ? await adminApi.getPendingReviews()
        : await adminApi.getAllReviews();
      setReviews(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleAccept = async (booking) => {
    setProcessing(true); setError(null);
    try {
      await adminApi.reviewBooking(booking.booking_id, 'ACCEPT');
      setSelectedBooking(null);
      load();
    } catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  const handleReject = async (booking) => {
    if (!rejectComment.trim()) {
      setError('Rejection requires a comment explaining the reason');
      return;
    }
    setProcessing(true); setError(null);
    try {
      await adminApi.reviewBooking(booking.booking_id, 'REJECT', rejectComment.trim());
      setSelectedBooking(null);
      setRejectComment('');
      load();
    } catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  const handleAutoAccept = async () => {
    setProcessing(true); setError(null);
    try {
      const result = await adminApi.processAutoAccept();
      setAutoAcceptResult(result);
      load();
    } catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading reviews...</p></div>;

  return (
    <div className="animate-fadeIn">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div className="page-header" style={{ marginBottom: 0 }}>
          <h1>Booking Reviews</h1>
          <p>Review and approve farmer procurement bookings</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={handleAutoAccept} disabled={processing}>
          <Clock size={14} />
          Auto-Accept Overdue
        </button>
      </div>

      {error && <div className="error-banner"><AlertTriangle size={16} />{error}</div>}
      {autoAcceptResult && (
        <div className="success-banner">
          <ShieldCheck size={16} />
          Auto-accepted {autoAcceptResult.auto_accepted} overdue booking(s)
        </div>
      )}

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <button
          className={`btn btn-sm ${filter === 'pending' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('pending')}
        >
          Pending ({filter === 'pending' ? reviews.length : '...'})
        </button>
        <button
          className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setFilter('all')}
        >
          All
        </button>
      </div>

      {reviews.length === 0 ? (
        <div className="card empty-state" style={{ padding: '48px 24px' }}>
          <ShieldCheck size={32} style={{ opacity: 0.3 }} />
          <h3>No {filter === 'pending' ? 'pending' : ''} bookings to review</h3>
          <p>All bookings have been reviewed.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 8 }}>
          {reviews.map((r) => (
            <ReviewCard
              key={r.booking_id}
              review={r}
              isExpanded={selectedBooking?.booking_id === r.booking_id}
              onExpand={() => setSelectedBooking(selectedBooking?.booking_id === r.booking_id ? null : r)}
              onAccept={() => handleAccept(r)}
              onReject={() => handleReject(r)}
              rejectComment={rejectComment}
              setRejectComment={setRejectComment}
              processing={processing}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ReviewCard({ review: r, isExpanded, onExpand, onAccept, onReject, rejectComment, setRejectComment, processing }) {
  const isPending = r.booking_status === 'PENDING_ADMIN_REVIEW';

  return (
    <div className="card" style={{
      padding: 0,
      borderColor: isPending ? 'var(--warning)' : 'var(--gray-200)',
    }}>
      {/* Header row */}
      <div
        onClick={onExpand}
        style={{
          padding: '14px 20px',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: isExpanded ? '1px solid var(--gray-200)' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', fontFamily: 'var(--font-mono)' }}>
              {r.booking_number}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)', marginTop: 2 }}>
              {r.farmer_name} · {r.passbook_number} · {r.crop} · {r.quantity_to_sell_quintals}Q
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className={`badge ${
            r.booking_status === 'PENDING_ADMIN_REVIEW' ? 'badge-pending' :
            r.booking_status === 'ACCEPTED' ? 'badge-accepted' :
            r.booking_status === 'REJECTED' ? 'badge-rejected' :
            'badge-processing'
          }`}>
            {r.booking_status.replace(/_/g, ' ')}
          </span>
          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>

      {/* Expanded detail */}
      {isExpanded && (
        <div style={{ padding: '16px 20px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 16,
            marginBottom: 16,
          }}>
            {[
              { label: 'Farmer', value: r.farmer_name },
              { label: 'Passbook', value: r.passbook_number },
              { label: 'Mobile', value: r.mobile_number },
              { label: 'Village', value: r.village },
              { label: 'Mandal', value: r.mandal },
              { label: 'Crop', value: r.crop },
              { label: 'Quantity', value: `${r.quantity_to_sell_quintals} Quintals` },
              { label: 'Centre', value: r.centre_name },
              { label: 'Slot Date', value: r.slot_date },
              { label: 'Slot Time', value: `${r.slot_start_time} – ${r.slot_end_time}` },
              { label: 'Submitted', value: new Date(r.created_at).toLocaleString() },
              { label: 'Review Deadline', value: r.remaining_hours > 0 ? `${Math.floor(r.remaining_hours)}h remaining` : 'Overdue' },
            ].map((item) => (
              <div key={item.label}>
                <div style={{
                  fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase',
                  letterSpacing: '0.06em', marginBottom: 2, fontWeight: 500,
                }}>
                  {item.label}
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--gray-800)' }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>

          {/* Admin review info */}
          {r.reviewed_at && (
            <div style={{
              padding: 10, background: 'var(--gray-100)', borderRadius: 4,
              marginBottom: 12, fontSize: '0.8rem', color: 'var(--gray-600)',
            }}>
              Reviewed by {r.reviewed_by_username} on {new Date(r.reviewed_at).toLocaleString()}
              {r.admin_comment && <span> — "{r.admin_comment}"</span>}
            </div>
          )}

          {/* Action buttons */}
          {isPending && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <button
                className="btn btn-success"
                onClick={onAccept}
                disabled={processing}
              >
                <Check size={16} />
                Accept
              </button>
              <div style={{ flex: 1 }}>
                <textarea
                  className="form-input"
                  placeholder="Rejection reason (required)..."
                  value={rejectComment}
                  onChange={(e) => setRejectComment(e.target.value)}
                  rows={2}
                  style={{ marginBottom: 8, fontSize: '0.85rem' }}
                />
                <button
                  className="btn btn-danger btn-sm"
                  onClick={onReject}
                  disabled={processing || !rejectComment.trim()}
                >
                  <X size={14} />
                  Reject
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
