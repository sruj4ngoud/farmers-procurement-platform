import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import {
  ListOrdered, Play, CheckCircle2, SkipForward, AlertTriangle, Clock
} from 'lucide-react';

export default function AdminQueuePage() {
  const [overview, setOverview] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);

  const load = async () => {
    try { setOverview(await adminApi.getQueueOverview()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const loadTokens = async (slotId) => {
    try {
      setTokens(await adminApi.getSlotTokens(slotId));
      setSelectedSlot(slotId);
    } catch (e) { setError(e.message); }
  };

  const handleTransition = async (tokenId, newStatus) => {
    setProcessing(true); setError(null);
    try {
      await adminApi.transitionToken(tokenId, newStatus);
      if (selectedSlot) await loadTokens(selectedSlot);
    } catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  const handleCallNext = async (slotId) => {
    setProcessing(true); setError(null);
    try {
      await adminApi.callNextToken(slotId);
      await loadTokens(slotId);
      await load();
    } catch (e) { setError(e.message); }
    finally { setProcessing(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading queue...</p></div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>Queue Dashboard</h1>
        <p>Manage live farmer queues at procurement centres</p>
      </div>

      {error && <div className="error-banner"><AlertTriangle size={16} />{error}</div>}

      {/* Slot overview */}
      {overview.length === 0 ? (
        <div className="card empty-state">
          <ListOrdered size={32} style={{ opacity: 0.3 }} />
          <h3>No active queues</h3>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
          {overview.map((s) => (
            <div
              key={s.slot_id}
              onClick={() => loadTokens(s.slot_id)}
              className="card"
              style={{
                cursor: 'pointer',
                borderColor: selectedSlot === s.slot_id ? 'var(--black)' : 'var(--gray-200)',
                padding: 0,
              }}
            >
              <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--gray-100)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{s.centre_name}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--gray-500)', marginTop: 2 }}>
                  {s.slot_date} · {s.start_time}–{s.end_time}
                </div>
              </div>
              <div style={{ padding: '12px 18px', display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                {[
                  { label: 'Current', value: s.current_token || '—' },
                  { label: 'Waiting', value: s.waiting },
                  { label: 'Called', value: s.called },
                  { label: 'Completed', value: s.completed },
                ].map((item) => (
                  <div key={item.label}>
                    <div style={{ fontSize: '0.68rem', color: 'var(--gray-400)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                      {item.label}
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{item.value}</div>
                  </div>
                ))}
              </div>
              <div style={{ padding: '0 18px 14px' }}>
                <button
                  className="btn btn-primary btn-block btn-sm"
                  onClick={(e) => { e.stopPropagation(); handleCallNext(s.slot_id); }}
                  disabled={processing || s.waiting === 0}
                >
                  <Play size={14} /> Call Next
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Token list */}
      {selectedSlot && tokens.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{ marginBottom: 12 }}>Token List</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Token</th>
                  <th>Farmer</th>
                  <th>Crop</th>
                  <th>Qty</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tokens.map((t) => (
                  <tr key={t.queue_id}>
                    <td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>#{t.token_number}</td>
                    <td>{t.farmer_name}</td>
                    <td>{t.crop}</td>
                    <td>{t.quantity}Q</td>
                    <td>
                      <span className={`badge ${
                        t.queue_status === 'WAITING' ? 'badge-waiting' :
                        t.queue_status === 'CALLED' ? 'badge-processing' :
                        t.queue_status === 'PROCESSING' ? 'badge-processing' :
                        t.queue_status === 'COMPLETED' ? 'badge-completed' :
                        'badge-cancelled'
                      }`}>
                        {t.queue_status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {t.queue_status === 'WAITING' && (
                          <button className="btn btn-primary btn-xs" onClick={() => handleTransition(t.queue_id, 'CALLED')} disabled={processing}>
                            Call
                          </button>
                        )}
                        {t.queue_status === 'CALLED' && (
                          <button className="btn btn-primary btn-xs" onClick={() => handleTransition(t.queue_id, 'PROCESSING')} disabled={processing}>
                            Process
                          </button>
                        )}
                        {t.queue_status === 'PROCESSING' && (
                          <button className="btn btn-success btn-xs" onClick={() => handleTransition(t.queue_id, 'COMPLETED')} disabled={processing}>
                            Complete
                          </button>
                        )}
                        {['WAITING', 'CALLED'].includes(t.queue_status) && (
                          <button className="btn btn-outline btn-xs" onClick={() => handleTransition(t.queue_id, 'SKIPPED')} disabled={processing}>
                            Skip
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
