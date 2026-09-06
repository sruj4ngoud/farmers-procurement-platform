import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import { BarChart3, Users, Wheat, Building2, ClipboardCheck, CreditCard } from 'lucide-react';

const TAB_ICONS = {
  farmers: Users,
  crops: Wheat,
  centres: Building2,
  bookings: ClipboardCheck,
  payments: CreditCard,
};

export default function AdminReportsPage() {
  const [activeTab, setActiveTab] = useState('farmers');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const tabs = [
    { key: 'farmers', label: 'Farmers', api: () => adminApi.reportFarmers() },
    { key: 'crops', label: 'Crops', api: () => adminApi.reportCrops() },
    { key: 'centres', label: 'Centres', api: () => adminApi.reportCentres() },
    { key: 'bookings', label: 'Bookings', api: () => adminApi.reportBookings() },
    { key: 'payments', label: 'Payments', api: () => adminApi.reportPayments() },
  ];

  useEffect(() => {
    setLoading(true);
    setError(null);
    const tab = tabs.find(t => t.key === activeTab);
    if (tab) {
      tab.api().then(d => { setData(d); setLoading(false); }).catch(e => { setError(e.message); setLoading(false); });
    }
  }, [activeTab]);

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>Reports</h1>
        <p>District analytics and summaries</p>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {tabs.map(t => {
          const Icon = TAB_ICONS[t.key];
          return (
            <button
              key={t.key}
              className={`btn btn-sm ${activeTab === t.key ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setActiveTab(t.key)}
            >
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="loading-spinner"><div className="spinner" /><p>Loading...</p></div>
      ) : data && <ReportView data={data} type={activeTab} />}
    </div>
  );
}

function ReportView({ data, type }) {
  if (type === 'farmers') return (
    <div>
      <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Total Farmers: {data.total}</div>
      {data.by_mandal?.map(m => (
        <div key={m.mandal} style={{
          padding: '10px 16px', background: 'var(--white)', border: '1px solid var(--gray-200)',
          borderRadius: 4, marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{m.mandal}</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>{m.count} farmers · {m.total_land_acres} acres</span>
        </div>
      ))}
    </div>
  );

  if (type === 'crops') return (
    <div>
      <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Total Cultivations: {data.total_cultivations}</div>
      {data.by_crop?.map(c => (
        <div key={c.crop} style={{
          padding: '10px 16px', background: 'var(--white)', border: '1px solid var(--gray-200)',
          borderRadius: 4, marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{c.crop}</span>
          <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>{c.count}</span>
        </div>
      ))}
    </div>
  );

  if (type === 'centres') return (
    <div className="table-container">
      <table>
        <thead>
          <tr><th>Centre</th><th>Status</th><th>Capacity</th><th>Total Bookings</th><th>Active</th></tr>
        </thead>
        <tbody>
          {data.centres?.map(c => (
            <tr key={c.centre_name}>
              <td style={{ fontWeight: 600 }}>{c.centre_name}</td>
              <td><span className={`badge ${c.status === 'ACTIVE' ? 'badge-completed' : 'badge-pending'}`}>{c.status}</span></td>
              <td>{c.capacity}</td>
              <td>{c.total_bookings}</td>
              <td>{c.active_bookings}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  if (type === 'bookings') return (
    <div>
      <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Total Bookings: {data.total}</div>
      {data.by_status?.map(s => (
        <div key={s.status} style={{
          padding: '10px 16px', background: 'var(--white)', border: '1px solid var(--gray-200)',
          borderRadius: 4, marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{s.status.replace(/_/g, ' ')}</span>
          <span style={{ fontSize: '0.875rem', fontWeight: 700 }}>{s.count}</span>
        </div>
      ))}
    </div>
  );

  if (type === 'payments') return (
    <div className="table-container">
      <table>
        <thead>
          <tr><th>Status</th><th>Count</th><th>Total Amount</th></tr>
        </thead>
        <tbody>
          {data.by_status?.map(s => (
            <tr key={s.status}>
              <td><span className="badge badge-pending">{s.status}</span></td>
              <td>{s.count}</td>
              <td style={{ fontWeight: 700 }}>₹{s.total_amount.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return <p style={{ color: 'var(--gray-400)' }}>No data</p>;
}
