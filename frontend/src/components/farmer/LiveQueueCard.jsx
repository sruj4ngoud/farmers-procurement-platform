import { Link } from 'react-router-dom';
import { Users, Clock, RefreshCw, ChevronRight } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext.jsx';
import SpeakButton from '../common/SpeakButton.jsx';

function stateKey(status) {
  if (status === 'CALLED') return 'CALLED';
  if (status === 'PROCESSING') return 'PROCESSING';
  if (status === 'COMPLETED') return 'COMPLETED';
  return 'WAITING';
}

/**
 * Big “live queue” waiting card.
 * queue: { token_number, position, queue_status, booking_id? }
 */
export default function LiveQueueCard({ queue, onRefresh, compact = false, showLink = true }) {
  const { t } = useLanguage();
  if (!queue) return null;

  const status = queue.queue_status || 'WAITING';
  const state = stateKey(status);
  const position = queue.position != null ? Number(queue.position) : null;
  const farmersAhead = position != null ? Math.max(0, position - 1) : null;
  const estMin = farmersAhead != null ? farmersAhead * 10 : null;
  const isDone = state === 'COMPLETED';
  const isCalled = state === 'CALLED' || state === 'PROCESSING';
  const tokenNo = queue.token_number != null ? `#${queue.token_number}` : '—';
  const bookingId = queue.booking_id;

  const speakText = [
    t(`q.state.${state}.title`),
    `${t('q.token')} ${tokenNo}.`,
    position != null ? `${t('q.position')} ${position}.` : '',
    farmersAhead != null ? `${t('q.ahead')} ${farmersAhead}.` : '',
    estMin != null ? `${t('q.wait')} ${estMin} ${t('unit.min')}.` : '',
    isDone ? t('q.state.COMPLETED.desc') : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={`fp-queue-card ${isDone ? 'done' : ''} ${compact ? 'compact' : ''}`}>
      <div className="fp-queue-top">
        <span className="fp-queue-kicker">
          <span className={`fp-queue-dot ${isCalled ? 'called' : ''}`} />
          {t('q.title')}
        </span>
        <SpeakButton text={speakText} title={t('chrome.listen')} className="on-dark" />
      </div>

      <div className={`fp-queue-main ${isDone ? 'centered' : ''}`}>
        <div className="fp-queue-token-col">
          <span className="fp-queue-label">{t('q.token')}</span>
          <strong className="fp-queue-token">{tokenNo}</strong>
          <span className={`fp-queue-state ${isCalled ? 'urgent' : ''}`}>{t(`q.state.${state}.title`)}</span>
        </div>

        {!compact && !isDone && (
          <div className="fp-queue-metrics">
            <div className="fp-queue-metric">
              <strong>{position != null ? position : '—'}</strong>
              <span>{t('q.position')}</span>
            </div>
            <div className="fp-queue-metric">
              <strong><Users size={14} />{farmersAhead != null ? farmersAhead : '—'}</strong>
              <span>{t('q.ahead')}</span>
            </div>
            <div className="fp-queue-metric">
              <strong><Clock size={14} />{estMin != null ? `~${estMin}` : '—'}</strong>
              <span>{t('q.wait')}</span>
            </div>
          </div>
        )}
        {compact && !isDone && (
          <div className="fp-queue-metrics inline">
            <span>{t('q.ahead')}: <strong>{farmersAhead != null ? farmersAhead : '—'}</strong></span>
            <span>{t('q.wait')}: <strong>{estMin != null ? `~${estMin} ${t('unit.min')}` : '—'}</strong></span>
          </div>
        )}
      </div>

      <div className="fp-queue-foot">
        <span className={`fp-queue-status-note ${isDone ? 'ok' : ''}`}>
          {isDone ? t('q.state.COMPLETED.desc') : isCalled ? t(`q.state.${state}.desc`) : farmersAhead != null && farmersAhead >= 8 ? t('q.movingSlow') : t('q.movingNormal')}
        </span>
        <div className="fp-queue-actions">
          {onRefresh && (
            <button type="button" className="fp-queue-action" onClick={onRefresh}>
              <RefreshCw size={13} /> {t('q.refresh')}
            </button>
          )}
          {showLink && bookingId && (
            <Link className="fp-queue-action primary" to={`/queue/${bookingId}`}>
              {t('dash.queue.view')} <ChevronRight size={14} />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
