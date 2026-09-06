import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { cultivationApi } from '../../services/cultivationApi.js';
import { cropApi } from '../../services/cropApi.js';
import { CATEGORY_EMOJI } from '../../data/crops.js';

export default function AddCultivation() {
  const navigate = useNavigate();
  const [allCrops, setAllCrops] = useState([]);
  const [cropCategories, setCropCategories] = useState([]);
  const [loadingCrops, setLoadingCrops] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCrop, setSelectedCrop] = useState(null);
  const [area, setArea] = useState('');
  const [quantityProduced, setQuantityProduced] = useState('');
  const [season, setSeason] = useState('Kharif-2025');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([cropApi.getActiveCrops(), cropApi.getCategories()])
      .then(([crops, cats]) => { setAllCrops(crops); setCropCategories(cats); })
      .catch(() => setError('Failed to load crop data'))
      .finally(() => setLoadingCrops(false));
  }, []);

  const filteredCrops = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return allCrops.filter((c) => {
      if (selectedCategory && c.category !== selectedCategory) return false;
      if (!q) return true;
      return c.name.toLowerCase().includes(q) || c.category.toLowerCase().includes(q);
    });
  }, [searchQuery, selectedCategory, allCrops]);

  const handleSelectCrop = (crop) => {
    setSelectedCrop(crop);
    setError(null);
  };

  const handleSave = async () => {
    if (!selectedCrop) { setError('Please select a crop'); return; }
    const areaNum = parseFloat(area);
    if (isNaN(areaNum) || areaNum <= 0) { setError('Please enter a valid cultivated area'); return; }
    const qtyNum = parseFloat(quantityProduced);
    if (isNaN(qtyNum) || qtyNum <= 0) { setError('Please enter a valid quantity produced'); return; }

    setSaving(true); setError(null);
    try {
      await cultivationApi.create({
        crop: selectedCrop.name,
        season: season,
        cultivated_area_acres: areaNum,
        quantity_produced_quintals: qtyNum,
      });
      navigate('/dashboard');
    } catch (e) {
      if (e.message.includes('land is available') || e.message.includes('acres of land')) {
        setError(e.message);
      } else {
        setError(e.message || 'Failed to add crop. Please try again.');
      }
    }
    finally { setSaving(false); }
  };

  return (
    <div>
      <div className="page-header">
        <h1>➕ Add Crop</h1>
        <p>Add a new cultivation record from the crop master list</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {!selectedCrop ? (
        <>
          {/* Search */}
          <div className="form-group">
            <label>Search Crop</label>
            <input
              className="form-input"
              type="text"
              placeholder="Search by crop name (e.g. Paddy, Tomato, Cotton...)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
          </div>

          {/* Category filter */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
            <button
              className={`btn btn-sm ${!selectedCategory ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setSelectedCategory('')}
            >
              All ({allCrops.length})
            </button>
            {cropCategories.map((cat) => (
              <button
                key={cat}
                className={`btn btn-sm ${selectedCategory === cat ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setSelectedCategory(selectedCategory === cat ? '' : cat)}
              >
                {CATEGORY_EMOJI[cat] || '🌱'} {cat}
              </button>
            ))}
          </div>

          {/* Crop list */}
          <div className="card-grid card-grid-3">
            {filteredCrops.map((crop) => {
              const cat = crop.category;
              const emoji = CATEGORY_EMOJI[cat] || '🌱';
              return (
                <div
                  className="crop-card"
                  key={crop.name}
                  onClick={() => handleSelectCrop(crop)}
                >
                  <div className="crop-emoji">{emoji}</div>
                  <div className="crop-name">{crop.name}</div>
                  <div className="crop-area">{crop.category}</div>
                </div>
              );
            })}
          </div>

          {filteredCrops.length === 0 && (
            <div className="card empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No crops found</h3>
              <p>Try a different search term or category.</p>
            </div>
          )}
        </>
      ) : (
        <>
          {/* Selected crop */}
          <div className="card" style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: '2rem' }}>{CATEGORY_EMOJI[selectedCrop.category] || '🌱'}</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>{selectedCrop.name}</div>
                <div style={{ fontSize: '.85rem', color: 'var(--gray-500)' }}>{selectedCrop.category}</div>
              </div>
              <button className="btn btn-sm btn-secondary" style={{ marginLeft: 'auto' }} onClick={() => setSelectedCrop(null)}>
                Change
              </button>
            </div>
          </div>

          {/* Season */}
          <div className="form-group">
            <label>Season</label>
            <select
              className="form-input"
              value={season}
              onChange={(e) => setSeason(e.target.value)}
            >
              <option value="Kharif-2025">Kharif 2025</option>
              <option value="Rabi-2025">Rabi 2025</option>
              <option value="Zaid-2025">Zaid 2025</option>
              <option value="Kharif-2024">Kharif 2024</option>
              <option value="Rabi-2024">Rabi 2024</option>
            </select>
          </div>

          {/* Cultivated area */}
          <div className="form-group">
            <label>Cultivated Area (Acres)</label>
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="e.g. 2.00"
              value={area}
              onChange={(e) => setArea(e.target.value)}
            />
            <div className="form-hint">Enter the area of land you cultivated for this crop.</div>
          </div>

          {/* Quantity produced */}
          <div className="form-group">
            <label>Total Quantity Produced (Quintals)</label>
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="e.g. 40"
              value={quantityProduced}
              onChange={(e) => setQuantityProduced(e.target.value)}
            />
            <div className="form-hint">Enter the total quantity that has already been harvested/produced.</div>
          </div>

          {/* Summary preview */}
          {area && quantityProduced && parseFloat(area) > 0 && parseFloat(quantityProduced) > 0 && (
            <div className="card" style={{ marginBottom: 20, background: 'var(--green-50)', border: '1px solid var(--green-200)' }}>
              <div className="summary-row-detail">
                <span className="label">Crop</span>
                <span className="value">{selectedCrop.name}</span>
              </div>
              <div className="summary-row-detail">
                <span className="label">Season</span>
                <span className="value">{season}</span>
              </div>
              <div className="summary-row-detail">
                <span className="label">Cultivated Area</span>
                <span className="value">{parseFloat(area)} Acres</span>
              </div>
              <div className="summary-row-detail">
                <span className="label">Quantity Produced</span>
                <span className="value">{parseFloat(quantityProduced)} Quintals</span>
              </div>
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12 }}>
            <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
              ← Cancel
            </button>
            <button
              className="btn btn-primary btn-lg"
              style={{ flex: 1 }}
              onClick={handleSave}
              disabled={saving || !selectedCrop || !area || !quantityProduced}
            >
              {saving ? 'Saving...' : '➕ Add Crop'}
            </button>
          </div>
        </>
      )}

      <div style={{ marginTop: 20 }}>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          ← Back to Dashboard
        </button>
      </div>
    </div>
  );
}
