import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';

export default function AdminMLPage() {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    adminApi.getMLInsights().then(d => { setInsights(d); setLoading(false); }).catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <div className="page-container"><p>Loading AI insights...</p></div>;

  const congColor = { LOW: '#22c55e', MODERATE: '#f59e0b', HIGH: '#ef4444' };

  return (
    <div className="page-container">
      <h1>AI Insights</h1>
      <p style={{ color: '#64748b', marginBottom: '1rem' }}>ML-based congestion and waiting time predictions for your district's centres. Advisory only — does not override any business rules.</p>
      {error && <div className="error-banner">{error}</div>}

      {insights.length === 0 ? <p style={{ color: '#94a3b8' }}>No centres found for prediction.</p> : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          {insights.map((ins, idx) => (
            <div key={idx} style={{ background: 'white', borderRadius: '12px', padding: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', borderTop: `4px solid ${congColor[ins.predicted_congestion] || '#94a3b8'}` }}>
              <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#1e293b', marginBottom: '1rem' }}>{ins.centre_name}</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div style={{ textAlign: 'center', padding: '0.75rem', background: '#f8fafc', borderRadius: '8px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#3b82f6' }}>{ins.current_queue}</div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Current Queue</div>
                </div>
                <div style={{ textAlign: 'center', padding: '0.75rem', background: `${congColor[ins.predicted_congestion]}15`, borderRadius: '8px' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: congColor[ins.predicted_congestion] }}>{ins.predicted_congestion}</div>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Congestion</div>
                </div>
              </div>
              <div style={{ textAlign: 'center', marginTop: '1rem', padding: '0.75rem', background: '#f0f9ff', borderRadius: '8px' }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e293b' }}>~{ins.predicted_wait_minutes} min</div>
                <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Estimated Wait Time</div>
              </div>
              {ins.confidence && (
                <div style={{ textAlign: 'center', marginTop: '0.5rem', fontSize: '0.8rem', color: '#94a3b8' }}>
                  Confidence: {(ins.confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '2rem', padding: '1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
        <h3 style={{ margin: '0 0 0.5rem', color: '#334155' }}>About AI Predictions</h3>
        <p style={{ margin: 0, color: '#64748b', fontSize: '0.9rem' }}>
          These predictions are advisory only. They help admins understand expected congestion patterns.
          The ML model does not override capacity limits, booking rules, or authorization checks.
          Prediction accuracy improves with more real procurement and queue data.
        </p>
      </div>
    </div>
  );
}
