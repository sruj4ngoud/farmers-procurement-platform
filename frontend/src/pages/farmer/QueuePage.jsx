import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { queueApi } from '../../services/queueApi.js';
import LiveQueueCard from '../../components/farmer/LiveQueueCard.jsx';

const QUEUE_STEPS = ['WAITING', 'CALLED', 'PROCESSING', 'COMPLETED'];

export default function QueuePage() {
  const { bookingId } = useParams();
  const { t } = useLanguage();
  const [queue, setQueue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchQueue = useCallback(async (silent = false) => {
    try {
      const data = await queueApi.getStatus(bookingId);
      setQueue(data);
      setError(null);
    } catch (e) { if (!silent) setError(e.message); }
    finally { setLoading(false); }
  }, [bookingId]);

  useEffect(() => {
    fetchQueue();
    const id = setInterval(() => {
      // Only keep polling quietly while the farmer is still waiting.
      fetchQueue(true);
    }, 15000);
    return () => clearInterval(id);
  }, [fetchQueue]);

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>{t('q.loading')}</p></div>;
  if (error) return (
    <div>
      <div className="error-banner">{error}</div>
      <Link to="/dashboard" className="btn btn-secondary">{t('q.error.back')}</Link>
    </div>
  );
  if (!queue) return null;

  const currentIdx = QUEUE_STEPS.indexOf(queue.queue_status);

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>🎫 {t('q.header')}</h1>
        <p>{t('q.sub')}</p>
      </div>

      {/* Big live queue card */}
      <div style={{ marginBottom: 20 }}>
        <LiveQueueCard queue={queue} onRefresh={() => fetchQueue(true)} showLink={false} />
      </div>

      {/* Queue progress */}
      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginBottom: 16, fontSize: '1rem', fontWeight: 700 }}>📋 {t('q.phase')}</h3>
        <div className="timeline">
          {QUEUE_STEPS.map((step, i) => {
            const isDone = i < currentIdx || queue.queue_status === 'COMPLETED';
            const isActiveStep = step === queue.queue_status && queue.queue_status !== 'COMPLETED';
            return (
              <div className="timeline-item" key={step}>
                <div className={`timeline-dot ${isDone ? 'done' : isActiveStep ? 'active' : ''}`} />
                <h4>{t(`q.step.${step}`)}</h4>
                {isDone && <p>{t('q.stepDone')}</p>}
                {isActiveStep && <p>{t('q.stepHere')}</p>}
                {!isDone && !isActiveStep && <p>{t('q.stepPending')}</p>}
              </div>
            );
          })}
        </div>
      </div>

      {/* Waiting / completion notice */}
      {['WAITING', 'CALLED', 'PROCESSING'].includes(queue.queue_status) && (
        <div className="info-banner" style={{ marginBottom: 20 }}>
          {t('q.waitNotice')}
        </div>
      )}
      {queue.queue_status === 'COMPLETED' && (
        <div className="success-banner" style={{ marginBottom: 20 }}>
          {t('q.doneBanner')}
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <Link to={`/booking-detail/${bookingId}`} className="btn btn-outline">
          📋 {t('q.viewDetails')}
        </Link>
        <Link to="/dashboard" className="btn btn-secondary">
          🏠 {t('q.dashboard')}
        </Link>
      </div>
    </div>
  );
}
