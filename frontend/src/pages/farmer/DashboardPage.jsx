import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext.jsx';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { farmerApi } from '../../services/farmerApi.js';
import { queueApi } from '../../services/queueApi.js';
import {
  Sprout, ArrowRight, ClipboardCheck, Clock, MapPin,
  Users, Bell, ChevronRight, CheckCircle2, Circle, Loader2, Hourglass
} from 'lucide-react';
import SpeakButton from '../../components/common/SpeakButton.jsx';
import LiveQueueCard from '../../components/farmer/LiveQueueCard.jsx';
import { localizeCrop, cropEmoji } from '../../data/crops.js';
import { localizeCentre, localizeNotification } from '../../utils/locale.js';

const ACTIVE_STATUSES = ['PENDING_ADMIN_REVIEW', 'ACCEPTED', 'AUTO_ACCEPTED', 'CONFIRMED'];
const QUEUE_READY_STATUSES = ['ACCEPTED', 'AUTO_ACCEPTED', 'CONFIRMED'];

function getJourneyIndex(status) {
  switch (status) {
    case 'PENDING_ADMIN_REVIEW': return 1;
    case 'REJECTED': return 1;
    case 'ACCEPTED':
    case 'AUTO_ACCEPTED':
    case 'CONFIRMED': return 2;
    default: return 0;
  }
}

function getGreetingKey() {
  const h = new Date().getHours();
  if (h < 12) return 'dash.greeting.morning';
  if (h < 17) return 'dash.greeting.afternoon';
  return 'dash.greeting.evening';
}

const STATUS_KEY = {
  PENDING_ADMIN_REVIEW: 'status.pendingReview',
  REJECTED: 'status.rejected',
  ACCEPTED: 'status.accepted',
  AUTO_ACCEPTED: 'status.autoAccepted',
  CONFIRMED: 'status.confirmed',
  CANCELLED: 'status.cancelled',
  COMPLETED: 'status.completed',
};

function statusClass(status) {
  if (status === 'PENDING_ADMIN_REVIEW') return 'badge-pending';
  if (status === 'REJECTED') return 'badge-rejected';
  if (status === 'ACCEPTED') return 'badge-accepted';
  if (status === 'CONFIRMED') return 'badge-confirmed';
  return 'badge-processing';
}

export default function DashboardPage() {
  const { farmer } = useAuth();
  const { t, lang } = useLanguage();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [liveQueue, setLiveQueue] = useState(null);
  const pollRef = useRef(null);

  const fetchQueue = (booking) => {
    if (!booking?.token || !booking.booking_id) return;
    queueApi.getStatus(booking.booking_id)
      .then(setLiveQueue)
      .catch(() => { /* queue may not be created yet — keep last known */ });
  };

  useEffect(() => {
    let cancelled = false;
    const load = (silent) => {
      if (!silent) setLoading(true);
      farmerApi.getDashboard()
        .then((d) => {
          if (cancelled) return;
          setData(d);
          setError(null);
          const active = (d.bookings || []).find(
            (b) => QUEUE_READY_STATUSES.includes(b.booking_status) && b.token
          );
          if (active) fetchQueue(active);
          else setLiveQueue(null);
        })
        .catch((e) => { if (!cancelled) setError(e.message); })
        .finally(() => { if (!cancelled) setLoading(false); });
    };

    load(false);
    pollRef.current = setInterval(() => load(true), 20000);
    return () => { cancelled = true; if (pollRef.current) clearInterval(pollRef.current); };
  }, [lang]);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner" />
        <p>{t('q.loading')}</p>
      </div>
    );
  }

  if (error) return <div className="error-banner">{error}</div>;
  if (!data) return null;

  const bookings = data.bookings || [];
  const notifications = data.notifications || [];
  const activeBooking = bookings.find((b) => ACTIVE_STATUSES.includes(b.booking_status));
  const journeyIdx = activeBooking ? getJourneyIndex(activeBooking.booking_status) : -1;
  const completedSteps = activeBooking ? journeyIdx : 0;
  const journeyProgress = activeBooking
    ? Math.round((completedSteps / 7) * 100)
    : 0;
  const ahead = activeBooking?.token ? Math.max(0, (activeBooking.token.position || 1) - 1) : null;
  const hasLiveQueue = !!activeBooking && !!liveQueue;
  const underReview = activeBooking && ['PENDING_ADMIN_REVIEW', 'REJECTED'].includes(activeBooking.booking_status);

  const heroSpeakText = hasLiveQueue
    ? `${t('dash.queue.live')}. ${t(`q.state.${liveQueue.queue_status === 'COMPLETED' ? 'COMPLETED' : liveQueue.queue_status === 'CALLED' || liveQueue.queue_status === 'PROCESSING' ? 'CALLED' : 'WAITING'}.title`)}`
    : underReview
      ? `${t('dash.queue.next')}: ${t(STATUS_KEY[activeBooking.booking_status] || 'dash.noActiveBooking')}. ${activeBooking.booking_number || ''}`
      : `${t('dash.nextAction')}: ${t('dash.sell.title')}. ${t('dash.sell.desc')}`;

  return (
    <div className="dashboard-page animate-fadeIn">
      <motion.header
        className="dashboard-hero"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
      >
        <div>
          <span className="dashboard-eyebrow">{t(getGreetingKey())}</span>
          <h1>{data.farmer?.farmer_name || farmer?.farmer_name || 'Farmer'}</h1>
          <p className="dashboard-id">{t('dash.passbook')} · {data.farmer?.passbook_number || '—'}</p>
        </div>
        <div className="dashboard-date">
          <span>{t('dash.today')}</span>
          <strong>{new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}</strong>
        </div>
      </motion.header>

      <section className="dashboard-grid">
        <motion.div
          className="dashboard-main-column"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.08 }}
        >
          {/* ── Your next step ── */}
          {hasLiveQueue ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <LiveQueueCard queue={liveQueue} showLink />
            </motion.div>
          ) : (
            <Link to={underReview && activeBooking ? `/booking-detail/${activeBooking.booking_id}` : '/sell'} className="sell-hero">
              <div className="sell-hero-copy">
                <div className="sell-icon">
                  {underReview ? <Hourglass size={22} /> : <Sprout size={22} />}
                </div>
                <div>
                  <span className="sell-kicker">{t('dash.nextAction')}</span>
                  {underReview && activeBooking ? (
                    <>
                      <h2>{t(STATUS_KEY[activeBooking.booking_status])}</h2>
                      <p>{activeBooking.booking_number} · {activeBooking.centre?.centre_name ? localizeCentre(activeBooking.centre.centre_name, lang) : ''}</p>
                    </>
                  ) : (
                    <>
                      <h2>{t('dash.sell.title')}</h2>
                      <p>{t('dash.sell.desc')}</p>
                    </>
                  )}
                </div>
              </div>
              <span className="sell-arrow"><ArrowRight size={20} /></span>
            </Link>
          )}

          <div className="dashboard-stat-row">
            <div className="dashboard-stat-card">
              <ClipboardCheck size={18} />
              <span>{t('dash.stat.bookings')}</span>
              <strong>{bookings.length}</strong>
            </div>
            <div className="dashboard-stat-card">
              <Bell size={18} />
              <span>{t('dash.stat.updates')}</span>
              <strong>{notifications.length}</strong>
            </div>
            <div className="dashboard-stat-card dashboard-stat-card-accent">
              <Clock size={18} />
              <span>{ahead !== null ? t('dash.stat.ahead') : t('dash.stat.status')}</span>
              <strong>{ahead !== null ? ahead : activeBooking ? t('dash.stat.active') : t('dash.stat.ready')}</strong>
            </div>
          </div>

          {activeBooking ? (
            <motion.section
              className="modern-card booking-card"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.16 }}
            >
              <div className="section-heading">
                <div>
                  <span className="section-kicker">{t('dash.section.live')}</span>
                  <h3>{t('dash.currentBooking')}</h3>
                </div>
                <Link to={activeBooking.token ? `/queue/${activeBooking.booking_id}` : `/booking-detail/${activeBooking.booking_id}`} className="text-action">
                  {t('dash.viewDetails')} <ChevronRight size={15} />
                </Link>
              </div>

              <div className="booking-topline">
                <div>
                  <span className="data-label">{t('dash.bookingId')}</span>
                  <strong className="mono">{activeBooking.booking_number}</strong>
                </div>
                <div className="booking-topline-right">
                  <span className={`badge ${statusClass(activeBooking.booking_status)}`}>
                    {t(STATUS_KEY[activeBooking.booking_status] || 'dash.noActiveBooking')}
                  </span>
                  <SpeakButton text={`${t('dash.currentBooking')}. ${t('dash.bookingId')} ${activeBooking.booking_number}. ${activeBooking.cultivation ? `${t('dash.crop')} ${localizeCrop(activeBooking.cultivation.crop, lang)}.` : ''}`} />
                </div>
              </div>

              <div className="booking-details-grid">
                {activeBooking.cultivation && (
                  <div className="booking-detail">
                    <Sprout size={16} />
                    <div><span className="data-label">{t('dash.crop')}</span><strong>{cropEmoji(activeBooking.cultivation.crop)} {localizeCrop(activeBooking.cultivation.crop, lang)}</strong></div>
                  </div>
                )}
                <div className="booking-detail">
                  <ClipboardCheck size={16} />
                  <div><span className="data-label">{t('dash.quantity')}</span><strong>{Number(activeBooking.quantity_to_sell_quintals)} {t('unit.quintals')}</strong></div>
                </div>
                {activeBooking.centre && (
                  <div className="booking-detail">
                    <MapPin size={16} />
                    <div><span className="data-label">{t('dash.centre')}</span><strong>{localizeCentre(activeBooking.centre.centre_name, lang)}</strong></div>
                  </div>
                )}
                {activeBooking.slot && (
                  <div className="booking-detail">
                    <Clock size={16} />
                    <div><span className="data-label">{t('dash.slot')}</span><strong>{activeBooking.slot.slot_date} · {activeBooking.slot.start_time}</strong></div>
                  </div>
                )}
              </div>

              {activeBooking.token && (
                <div className="token-panel">
                  <div className="token-number">
                    <span>{t('dash.yourToken')}</span>
                    <strong>#{activeBooking.token.token_number}</strong>
                  </div>
                  <div className="token-divider" />
                  <div className="token-wait">
                    <Users size={17} />
                    <div>
                      <strong>{ahead !== null ? t('dash.aheadCount', { n: ahead }) : t('dash.aheadShort')}</strong>
                      <span>{t('dash.waitCalc', { min: (ahead || 0) * 15 })}</span>
                    </div>
                  </div>
                </div>
              )}
            </motion.section>
          ) : (
            <section className="modern-card empty-booking">
              <div className="empty-icon"><ClipboardCheck size={24} /></div>
              <div>
                <span className="section-kicker">{t('dash.nothingScheduled')}</span>
                <h3>{t('dash.noActiveBooking')}</h3>
                <p>{t('dash.noActiveDesc')}</p>
              </div>
              <Link to="/sell" className="outline-action">{t('dash.startBooking')} <ArrowRight size={16} /></Link>
            </section>
          )}
        </motion.div>

        <motion.aside
          className="dashboard-side-column"
          initial={{ opacity: 0, x: 14 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.45, delay: 0.12 }}
        >
          {activeBooking && (
            <section className="modern-card journey-card">
              <div className="section-heading">
                <div><span className="section-kicker">{t('dash.progress')}</span><h3>{t('dash.journey')}</h3></div>
                <strong className="progress-percent">{journeyProgress}%</strong>
              </div>
              <div className="progress-track"><motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${Math.max(8, journeyProgress)}%` }} transition={{ duration: 0.8, delay: 0.25 }} /></div>
              <div className="journey-list">
                {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => {
                  const isDone = i < journeyIdx;
                  const isCurrent = i === journeyIdx;
                  return (
                    <div key={i} className={`journey-item ${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}`}>
                      <div className="journey-icon">
                        {isDone ? <CheckCircle2 size={15} /> : isCurrent ? <Loader2 size={15} className="spin" /> : <Circle size={15} />}
                      </div>
                      <span>{t(`dash.journey.${i}`)}</span>
                      {isCurrent && <small>{t('dash.journeyNow')}</small>}
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {notifications.length > 0 && (
            <section className="modern-card updates-card">
              <div className="section-heading">
                <div><span className="section-kicker">{t('dash.latest')}</span><h3>{t('dash.recentUpdates')}</h3></div>
                <Bell size={17} />
              </div>
              <div className="updates-list">
                {notifications.slice(0, 3).map((n, index) => {
                  const loc = localizeNotification(n.title, n.message, lang);
                  return (
                    <div key={n.notification_id || index} className="update-item">
                      <span className="update-dot" />
                      <div>
                        <div className="update-item-head">
                          <strong>{loc.title}</strong>
                          <SpeakButton text={`${loc.title}. ${loc.message}`} className="tiny" />
                        </div>
                        <p>{loc.message}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )}
        </motion.aside>
      </section>
    </div>
  );
}
