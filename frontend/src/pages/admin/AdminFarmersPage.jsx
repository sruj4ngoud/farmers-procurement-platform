import { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi.js';
import { useAdmin } from '../../context/AdminContext.jsx';
import { Users } from 'lucide-react';

export default function AdminFarmersPage() {
  const { admin } = useAdmin();
  const [farmers, setFarmers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await adminApi.getFarmers();
        if (!cancelled) setFarmers(data);
      } catch (e) {
        if (!cancelled) setError(e.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const filtered = farmers.filter(f =>
    !search || f.farmer_name.toLowerCase().includes(search.toLowerCase()) ||
    f.passbook_number.toLowerCase().includes(search.toLowerCase()) ||
    f.mandal.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>Loading farmers...</p></div>;
  if (error) return <div className="error-banner">{error}</div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>Farmers</h1>
        <p>{farmers.length} registered farmer(s) in {admin?.district}</p>
      </div>

      <div className="form-group" style={{ maxWidth: 360, marginBottom: 16 }}>
        <input
          className="form-input"
          type="text"
          placeholder="Search by name, passbook, or mandal..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Passbook</th>
              <th>Mobile</th>
              <th>Village</th>
              <th>Mandal</th>
              <th>Land (acres)</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((f) => (
              <tr key={f.farmer_id}>
                <td style={{ fontWeight: 600 }}>{f.farmer_name}</td>
                <td className="font-mono" style={{ fontSize: '0.8rem' }}>{f.passbook_number}</td>
                <td>{f.mobile_number}</td>
                <td>{f.village}</td>
                <td>{f.mandal}</td>
                <td>{f.total_land_acres}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan="6" style={{ textAlign: 'center', color: 'var(--gray-400)', padding: 24 }}>
                No farmers found
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
