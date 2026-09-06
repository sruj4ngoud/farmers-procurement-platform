import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import { CreditCard, ArrowRight, AlertTriangle } from 'lucide-react';

export default function AdminPaymentsPage() {
  const [dashboard, setDashboard] = useState(null);
  const [payments, setPayments] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);

  const load = async () => {
    try {
      const [dash, pay] = await Promise.all([
        adminApi.getPaymentDashboard(),
        adminApi.getPayments(filter || undefined),
      ]);
      setDashboard(dash);
      setPayments(pay);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleAction = async (paymentId, action, ref) => {
    setProcessing(true); setError(null);
    try {
      if (action === 'process') await adminApi.processPayment(paymentId);
      else if (action === 'credit') await adminApi.creditPayment(paymentId, ref);
      else if (action === 'fail') await adminApi.failPayment(paymentId, 'Payment failed');
      load();
    } catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading...</p></div>;

  const fmt = (n) => `₹${Number(n).toLocaleString()}`;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>Payments</h1>
        <p>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            Government <ArrowRight size={14} /> Farmer
          </span>
        </p>
      </div>

      {error && <div className="error-banner"><AlertTriangle size={16} />{error}</div>}

      {/* Dashboard stats */}
      {dashboard && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 1, background: 'var(--gray-200)', borderRadius: 6, overflow: 'hidden', marginBottom: 24 }}>
          {[
            { label: 'Pending', value: dashboard.pending_payments, sub: fmt(dashboard.total_amount_pending) },
            { label: 'Ready', value: dashboard.ready_payments },
            { label: 'Processing', value: dashboard.processing_payments, sub: fmt(dashboard.total_amount_processing) },
            { label: 'Credited Today', value: dashboard.credited_today },
            { label: 'Failed', value: dashboard.failed_payments },
          ].map((item) => (
            <div key={item.label} style={{ background: 'var(--white)', padding: '14px 18px' }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{item.label}</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.03em' }}>{item.value}</div>
              {item.sub && <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)' }}>{item.sub}</div>}
            </div>
          ))}
        </div>
      )}

      {/* Filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {[{ label: 'All', value: '' }, { label: 'Pending', value: 'PENDING' }, { label: 'Ready', value: 'READY' }, { label: 'Processing', value: 'PROCESSING' }, { label: 'Completed', value: 'COMPLETED' }, { label: 'Failed', value: 'FAILED' }].map(f => (
          <button key={f.value} className={`btn btn-sm ${filter === f.value ? 'btn-primary' : 'btn-outline'}`} onClick={() => setFilter(f.value)}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Payments table */}
      {payments.length === 0 ? (
        <div className="card empty-state">
          <CreditCard size={32} style={{ opacity: 0.3 }} />
          <h3>No payments found</h3>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Booking</th>
                <th>Farmer</th>
                <th>Crop</th>
                <th>Qty x MSP</th>
                <th>Amount</th>
                <th>Bank</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {payments.map((p) => (
                <tr key={p.payment_id}>
                  <td className="font-mono" style={{ fontSize: '0.8rem' }}>{p.booking_number}</td>
                  <td style={{ fontWeight: 600 }}>{p.farmer_name}</td>
                  <td>{p.crop}</td>
                  <td>{p.accepted_quantity}Q x {fmt(p.msp_per_quintal)}</td>
                  <td style={{ fontWeight: 700 }}>{fmt(p.amount_payable)}</td>
                  <td>
                    <span className={`badge ${p.bank_verified ? 'badge-completed' : 'badge-rejected'}`}>
                      {p.bank_verified ? 'Verified' : 'Unverified'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${
                      p.payment_status === 'COMPLETED' ? 'badge-completed' :
                      p.payment_status === 'FAILED' ? 'badge-rejected' :
                      p.payment_status === 'PROCESSING' ? 'badge-processing' :
                      p.payment_status === 'READY' ? 'badge-confirmed' :
                      'badge-pending'
                    }`}>
                      {p.payment_status}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {p.payment_status === 'PENDING' && p.bank_verified && (
                        <button className="btn btn-primary btn-xs" onClick={() => handleAction(p.payment_id, 'process')} disabled={processing}>Ready</button>
                      )}
                      {p.payment_status === 'READY' && (
                        <button className="btn btn-primary btn-xs" onClick={() => handleAction(p.payment_id, 'process')} disabled={processing}>Process</button>
                      )}
                      {p.payment_status === 'PROCESSING' && (
                        <button className="btn btn-success btn-xs" onClick={() => handleAction(p.payment_id, 'credit')} disabled={processing}>Credit</button>
                      )}
                      {!['COMPLETED', 'FAILED'].includes(p.payment_status) && (
                        <button className="btn btn-outline btn-xs" onClick={() => handleAction(p.payment_id, 'fail')} disabled={processing}>Fail</button>
                      )}
                    </div>
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
