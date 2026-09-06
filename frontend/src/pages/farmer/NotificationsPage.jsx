import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext.jsx';
import { notificationApi } from '../../services/notificationApi.js';

export default function NotificationsPage() {
  const { farmer } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchNotifications = useCallback(async () => {
    if (!farmer?.passbook_number) return;
    try {
      const data = await notificationApi.list(farmer.passbook_number);
      setNotifications(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [farmer]);

  useEffect(() => { fetchNotifications(); }, [fetchNotifications]);

  const handleMarkRead = async (notif) => {
    try {
      await notificationApi.markRead(notif.notification_id);
      setNotifications((prev) => prev.map((n) =>
        n.notification_id === notif.notification_id ? { ...n, is_read: true } : n
      ));
    } catch {}
  };

  const unread = notifications.filter(n => !n.is_read);
  const read = notifications.filter(n => n.is_read);

  const iconFor = (type) => {
    const icons = {
      BOOKING_CONFIRMED: '✅',
      TOKEN_GENERATED: '🎫',
      QUEUE_UPDATE: '📋',
      PROCUREMENT_COMPLETED: '📦',
      PAYMENT_PROCESSED: '💰',
      SLOT_REMINDER: '⏰',
    };
    return icons[type] || '🔔';
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading notifications...</p></div>;

  return (
    <div>
      <div className="page-header">
        <h1>🔔 Notifications</h1>
        <p>
          {unread.length > 0
            ? `${unread.length} unread notification${unread.length !== 1 ? 's' : ''}`
            : 'You\'re all caught up!'
          }
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {notifications.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon">🔔</div>
          <h3>No notifications yet</h3>
          <p>You'll receive notifications when you create bookings, generate tokens, and more.</p>
        </div>
      ) : (
        <div className="card">
          {unread.length > 0 && (
            <div>
              <h3 style={{ fontSize: '.82rem', color: 'var(--gray-500)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.5px', fontWeight: 600 }}>New</h3>
              {unread.map((n) => (
                <div key={n.notification_id} className="notification-item unread">
                  <div className="notification-dot" />
                  <div style={{ fontSize: '1.3rem', flexShrink: 0 }}>{iconFor(n.notification_type)}</div>
                  <div className="notification-content">
                    <h4>{n.title}</h4>
                    <p>{n.message}</p>
                    <button
                      className="btn btn-sm btn-outline"
                      style={{ marginTop: 8 }}
                      onClick={() => handleMarkRead(n)}
                    >
                      Mark as read
                    </button>
                  </div>
                  <div className="notification-time">
                    {new Date(n.created_at).toLocaleDateString('en-IN')}
                  </div>
                </div>
              ))}
            </div>
          )}

          {read.length > 0 && (
            <div style={{ marginTop: unread.length > 0 ? 20 : 0 }}>
              <h3 style={{ fontSize: '.82rem', color: 'var(--gray-500)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.5px', fontWeight: 600 }}>Earlier</h3>
              {read.map((n) => (
                <div key={n.notification_id} className="notification-item">
                  <div style={{ fontSize: '1.3rem', opacity: .5, flexShrink: 0 }}>{iconFor(n.notification_type)}</div>
                  <div className="notification-content">
                    <h4 style={{ color: 'var(--gray-600)' }}>{n.title}</h4>
                    <p>{n.message}</p>
                  </div>
                  <div className="notification-time">
                    {new Date(n.created_at).toLocaleDateString('en-IN')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
