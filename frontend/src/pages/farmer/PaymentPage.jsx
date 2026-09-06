import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { paymentApi } from '../../services/paymentApi.js';

export default function PaymentPage() {
  const { bookingId } = useParams();
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    paymentApi.getByBooking(bookingId)
      .then(setPayment)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [bookingId]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading payment details...</p></div>;
  if (error) return (
    <div>
      <div className="error-banner">{error}</div>
      <Link to={`/booking-detail/${bookingId}`} className="btn btn-secondary">← Back</Link>
    </div>
  );
  if (!payment) return (
    <div className="card empty-state">
      <div className="empty-icon">💰</div>
      <h3>No payment record found</h3>
      <p>Government payment will be processed after procurement is completed.</p>
      <Link to={`/booking-detail/${bookingId}`} className="btn btn-secondary" style={{ marginTop: 16 }}>← Back</Link>
    </div>
  );

  const statusBadge = (s) => {
    const cls = { COMPLETED: 'badge-completed', PENDING: 'badge-pending', PROCESSING: 'badge-processing', FAILED: 'badge-cancelled' };
    return <span className={`badge ${cls[s] || 'badge-pending'}`}>{s}</span>;
  };

  // Build payment status timeline
  const paymentSteps = [
    { label: 'Procurement Completed', done: true },
    { label: 'Quantity Accepted', done: true },
    { label: 'Payment Processing', done: payment.payment_status === 'COMPLETED' },
    { label: 'Payment Credited to Your Account', done: payment.payment_status === 'COMPLETED' },
  ];

  return (
    <div>
      <div className="page-header">
        <h1>💰 Government Payment Status</h1>
        <p>Payment from government to farmer</p>
      </div>

      {/* Amount card */}
      <div className="payment-card">
        <div className="payment-label">Amount Payable to You</div>
        <div className="payment-amount">₹{Number(payment.amount_payable).toLocaleString()}</div>
        <div>{statusBadge(payment.payment_status)}</div>
        <div className="payment-direction">Government → Farmer</div>
      </div>

      {/* Payment timeline */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 16, fontSize: '1rem', fontWeight: 700 }}>📋 Payment Timeline</h3>
        <div className="timeline">
          {paymentSteps.map((step, i) => (
            <div className="timeline-item" key={i}>
              <div className={`timeline-dot ${step.done ? 'done' : ''}`} />
              <h4>{step.label}</h4>
              {step.done && <p>✓ Completed</p>}
              {!step.done && <p>Pending</p>}
            </div>
          ))}
        </div>
      </div>

      {/* Payment details */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 14, fontSize: '.95rem', fontWeight: 700 }}>📋 Payment Details</h3>
        <div className="summary-row-detail">
          <span className="label">Payment ID</span>
          <span className="value" style={{ fontFamily: 'monospace', fontSize: '.82rem' }}>{payment.payment_id.slice(0, 8)}...</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">Amount Payable</span>
          <span className="value highlight">₹{Number(payment.amount_payable).toLocaleString()}</span>
        </div>
        <div className="summary-row-detail">
          <span className="label">Status</span>
          <span className="value">{statusBadge(payment.payment_status)}</span>
        </div>
        {payment.transaction_reference && (
          <div className="summary-row-detail">
            <span className="label">Transaction Reference</span>
            <span className="value" style={{ fontFamily: 'monospace', fontSize: '.85rem' }}>{payment.transaction_reference}</span>
          </div>
        )}
        {payment.payment_date && (
          <div className="summary-row-detail">
            <span className="label">Payment Date</span>
            <span className="value">{new Date(payment.payment_date).toLocaleDateString('en-IN')}</span>
          </div>
        )}
        <div className="summary-row-detail">
          <span className="label">Payment Direction</span>
          <span className="value" style={{ color: 'var(--green-700)' }}>Government → Farmer</span>
        </div>
        {payment.failure_reason && (
          <div className="summary-row-detail">
            <span className="label">Failure Reason</span>
            <span className="value" style={{ color: 'var(--red-500)' }}>{payment.failure_reason}</span>
          </div>
        )}
        <div className="summary-row-detail">
          <span className="label">Created</span>
          <span className="value">{new Date(payment.created_at).toLocaleString()}</span>
        </div>
      </div>

      <Link to={`/booking-detail/${bookingId}`} className="btn btn-secondary">← Back to Booking</Link>
    </div>
  );
}
