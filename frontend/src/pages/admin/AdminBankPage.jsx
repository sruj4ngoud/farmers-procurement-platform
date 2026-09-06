import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import { Landmark, ShieldCheck, X, AlertTriangle } from 'lucide-react';

export default function AdminBankPage() {
  const [banks, setBanks] = useState([]);
  const [filter, setFilter] = useState('PENDING_VERIFICATION');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [processing, setProcessing] = useState(false);

  const load = async () => {
    try { setBanks(await adminApi.getBankVerifications(filter)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [filter]);

  const handleVerify = async (bd) => {
    setProcessing(true); setError(null);
    try { await adminApi.verifyBank(bd.bank_detail_id, 'VERIFIED'); load(); }
    catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  const handleReject = async (bd) => {
    if (!rejectReason.trim()) { setError('Rejection requires a reason'); return; }
    setProcessing(true); setError(null);
    try { await adminApi.verifyBank(bd.bank_detail_id, 'REJECTED', rejectReason.trim()); setRejectReason(''); load(); }
    catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading...</p></div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>Bank Verification</h1>
        <p>Verify farmer bank accounts for payment processing</p>
      </div>

      {error && <div className="error-banner"><AlertTriangle size={16} />{error}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {['PENDING_VERIFICATION', 'VERIFIED', 'REJECTED', 'ALL'].map(s => (
          <button key={s} className={`btn btn-sm ${filter === s ? 'btn-primary' : 'btn-outline'}`} onClick={() => setFilter(s)}>
            {s === 'ALL' ? 'All' : s.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {banks.length === 0 ? (
        <div className="card empty-state">
          <Landmark size={32} style={{ opacity: 0.3 }} />
          <h3>No bank records found</h3>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 8 }}>
          {banks.map((bd) => (
            <div key={bd.bank_detail_id} className="card" style={{ borderColor: bd.verification_status === 'VERIFIED' ? 'var(--success)' : bd.verification_status === 'REJECTED' ? 'var(--error)' : 'var(--gray-200)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{bd.farmer_name}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>{bd.passbook_number} · {bd.mandal}</div>
                </div>
                <span className={`badge ${bd.verification_status === 'VERIFIED' ? 'badge-completed' : bd.verification_status === 'REJECTED' ? 'badge-rejected' : 'badge-pending'}`}>
                  {bd.verification_status.replace(/_/g, ' ')}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, padding: 12, background: 'var(--gray-100)', borderRadius: 4, marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Account Holder</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{bd.account_holder_name}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Account</div>
                  <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>{bd.account_number_masked}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>IFSC</div>
                  <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>{bd.ifsc_code}</div>
                </div>
              </div>

              {bd.verification_status === 'PENDING_VERIFICATION' && (
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <button className="btn btn-success btn-sm" onClick={() => handleVerify(bd)} disabled={processing}>
                    <ShieldCheck size={14} /> Verify
                  </button>
                  <div style={{ flex: 1 }}>
                    <input className="form-input" placeholder="Rejection reason..." value={rejectReason} onChange={e => setRejectReason(e.target.value)} style={{ marginBottom: 8, fontSize: '0.85rem' }} />
                    <button className="btn btn-danger btn-xs" onClick={() => handleReject(bd)} disabled={processing || !rejectReason.trim()}>
                      <X size={12} /> Reject
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
