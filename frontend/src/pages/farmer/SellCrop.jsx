import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { farmerApi } from '../../services/farmerApi.js';
import { cultivationApi } from '../../services/cultivationApi.js';
import { mspApi } from '../../services/mspApi.js';
import { cropApi } from '../../services/cropApi.js';
import { parseSpokenNumber } from '../../utils/speech.js';
import { localizeCrop, cropMatchesQuery, localizeCategory, categoryMatchesQuery, cropEmoji } from '../../data/crops.js';

import BookingProgress from '../../components/farmer/BookingProgress.jsx';
import MicButton from '../../components/common/MicButton.jsx';

const STEP_KEYS = ['sell.stepLand', 'sell.stepCrop', 'sell.stepQuantity', 'sell.stepCentre', 'sell.stepSlot', 'sell.stepConfirm'];

export default function SellCrop() {
  const { farmer } = useAuth();
  const { t, lang } = useLanguage();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Farmer data
  const [totalLand, setTotalLand] = useState(0);
  const [farmerData, setFarmerData] = useState(null);

  // Crops from API
  const [allCrops, setAllCrops] = useState([]);
  const [cropCategories, setCropCategories] = useState([]);

  // Step 1: Land
  const [cultivatedArea, setCultivatedArea] = useState('');

  // Step 2: Crop
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCrop, setSelectedCrop] = useState(null);

  // Step 3: Quantity + MSP
  const [quantityToSell, setQuantityToSell] = useState('');
  const [msp, setMsp] = useState(null);
  const [saving, setSaving] = useState(false);

  const SELL_STEPS = STEP_KEYS.map((k) => ({ label: t(k) }));

  // Load farmer data + crops from API
  useEffect(() => {
    Promise.all([
      farmerApi.getDashboard(),
      cropApi.getActiveCrops(),
      cropApi.getCategories(),
    ])
      .then(([dashData, cropsData, catsData]) => {
        setFarmerData(dashData);
        setTotalLand(Number(dashData.farmer?.total_land_acres || 0));
        setAllCrops(cropsData);
        setCropCategories(catsData);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Load MSP from crop data when selected
  useEffect(() => {
    if (selectedCrop) {
      setMsp(selectedCrop.msp_per_quintal || null);
    }
  }, [selectedCrop]);

  const filteredCrops = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return allCrops.filter((c) => {
      if (selectedCategory && c.category !== selectedCategory) return false;
      return cropMatchesQuery(c.name, q, lang) || categoryMatchesQuery(c.category, q, lang);
    });
  }, [searchQuery, selectedCategory, allCrops, lang]);

  const estimatedPayment = msp && quantityToSell ? (parseFloat(quantityToSell) * msp) : 0;

  /* ── Voice handlers ── */

  const applySpokenArea = (transcript) => {
    const num = parseSpokenNumber(transcript);
    if (num != null && num > 0) setCultivatedArea(String(num));
    else setError(t('voice.numberAgain'));
  };

  const applySpokenCrop = (transcript) => {
    const q = transcript.toLowerCase().trim();
    const inCategory = allCrops.filter((c) => !selectedCategory || c.category === selectedCategory);
    const matches = inCategory.filter((c) => cropMatchesQuery(c.name, q, lang) || categoryMatchesQuery(c.category, q, lang));
    if (matches.length === 1) {
      setSelectedCrop(matches[0]);
      setSearchQuery('');
      setError(null);
    } else if (matches.length > 1) {
      setSearchQuery(transcript);
      setError(null);
    } else {
      setError(t('voice.cropAgain'));
    }
  };

  const applySpokenQuantity = (transcript) => {
    const num = parseSpokenNumber(transcript);
    if (num != null && num > 0) setQuantityToSell(String(num));
    else setError(t('voice.numberAgain'));
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>{t('q.loading')}</p></div>;

  // Step 1: Land
  if (step === 1) {
    return (
      <div>
        <BookingProgress steps={SELL_STEPS} current={0} />
        <div className="page-header">
          <h1>{t('sell.s1.title')}</h1>
          <p>{t('sell.s1.desc')}</p>
        </div>
        {error && <div className="error-banner">{error}</div>}

        <div className="card" style={{ marginBottom: 20 }}>
          <div className="summary-row-detail">
            <span className="label">{t('sell.s1.total')}</span>
            <span className="value highlight">{totalLand} {t('unit.acres')}</span>
          </div>
        </div>

        <div className="form-group">
          <label>{t('sell.s1.ask')}</label>
          <div className="quantity-input-group">
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="0.01"
              max={totalLand}
              placeholder="0"
              value={cultivatedArea}
              onChange={(e) => setCultivatedArea(e.target.value)}
            />
            <span className="unit">{t('unit.acres')}</span>
            <MicButton onResult={applySpokenArea} onError={setError} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>{t('sell.cancel')}</button>
          <button
            className="btn btn-primary btn-lg"
            style={{ flex: 1 }}
            onClick={() => {
              const area = parseFloat(cultivatedArea);
              if (isNaN(area) || area <= 0) { setError(t('sell.err.area')); return; }
              if (area > totalLand) { setError(t('sell.err.maxLand', { area: totalLand })); return; }
              setError(null);
              setStep(2);
            }}
            disabled={!cultivatedArea}
          >
            {t('sell.s1.next')}
          </button>
        </div>
      </div>
    );
  }

  // Step 2: Crop Selection
  if (step === 2) {
    return (
      <div>
        <BookingProgress steps={SELL_STEPS} current={1} />
        <div className="page-header">
          <h1>{t('sell.s2.title')}</h1>
          <p>{t('sell.s2.desc', { area: cultivatedArea })}</p>
        </div>
        {error && <div className="error-banner">{error}</div>}

        {!selectedCrop ? (
          <>
            <div className="form-group">
              <label>{t('sell.s2.search')}</label>
              <div className="search-with-mic">
                <input
                  className="form-input"
                  type="text"
                  placeholder={t('sell.s2.ph')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  autoFocus
                />
                <MicButton onResult={applySpokenCrop} onError={setError} />
              </div>
              <p className="field-caption">{t('sell.s2.voiceHint')}</p>
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
              <button
                className={`btn btn-sm ${!selectedCategory ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setSelectedCategory('')}
              >
                {t('sell.s2.all')} ({allCrops.length})
              </button>
              {cropCategories.map((cat) => (
                <button
                  key={cat}
                  className={`btn btn-sm ${selectedCategory === cat ? 'btn-primary' : 'btn-outline'}`}
                  onClick={() => setSelectedCategory(selectedCategory === cat ? '' : cat)}
                >
                  {localizeCategory(cat, lang)}
                </button>
              ))}
            </div>

            <div className="card-grid card-grid-3">
              {filteredCrops.map((crop) => (
                <div className="crop-card" key={crop.name} onClick={() => setSelectedCrop(crop)}>
                  <div className="crop-name">{cropEmoji(crop.name)} {localizeCrop(crop.name, lang)}</div>
                  <div className="crop-area">{localizeCategory(crop.category, lang)}</div>
                </div>
              ))}
            </div>

            {filteredCrops.length === 0 && (
              <div className="card empty-state">
                <div className="empty-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></div>
                <h3>{t('sell.s2.none')}</h3>
                <p>{t('sell.s2.try')}</p>
              </div>
            )}
          </>
        ) : (
          <div className="card" style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>{cropEmoji(selectedCrop.name)} {localizeCrop(selectedCrop.name, lang)}</div>
                <div style={{ fontSize: '.85rem', color: 'var(--gray-500)' }}>{localizeCategory(selectedCrop.category, lang)}</div>
              </div>
              <button className="btn btn-sm btn-secondary" style={{ marginLeft: 'auto' }} onClick={() => setSelectedCrop(null)}>{t('sell.s2.change')}</button>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-secondary" onClick={() => setStep(1)}>{t('sell.back')}</button>
          <button
            className="btn btn-primary btn-lg"
            style={{ flex: 1 }}
            onClick={() => {
              if (!selectedCrop) { setError(t('sell.err.crop')); return; }
              setError(null);
              setStep(3);
            }}
            disabled={!selectedCrop}
          >
            {t('sell.s2.next')}
          </button>
        </div>
      </div>
    );
  }

  // Step 3: Quantity + MSP
  if (step === 3) {
    return (
      <div>
        <BookingProgress steps={SELL_STEPS} current={2} />
        <div className="page-header">
          <h1>{t('sell.s3.title')}</h1>
          <p>{t('sell.s3.desc', { crop: localizeCrop(selectedCrop.name, lang) })}</p>
        </div>
        {error && <div className="error-banner">{error}</div>}

        <div className="card" style={{ marginBottom: 20 }}>
          <div className="summary-row-detail">
            <span className="label">{t('dash.crop')}</span>
            <span className="value">{localizeCrop(selectedCrop.name, lang)}</span>
          </div>
        </div>

        <div className="form-group">
          <label>{t('sell.s3.ask')}</label>
          <div className="quantity-input-group">
            <input
              className="form-input"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0"
              value={quantityToSell}
              onChange={(e) => setQuantityToSell(e.target.value)}
            />
            <span className="unit">{t('unit.quintals')}</span>
            <MicButton onResult={applySpokenQuantity} onError={setError} />
          </div>
          <p className="field-caption">{t('sell.s3.voiceHint')}</p>
        </div>

        {msp && quantityToSell && parseFloat(quantityToSell) > 0 && (
          <div className="card" style={{ marginBottom: 20, background: 'var(--green-50)', border: '1px solid var(--green-200)' }}>
            <div className="summary-row-detail">
              <span className="label">{t('sell.msp')}</span>
              <span className="value">₹{msp.toLocaleString()} / {t('unit.quintal')}</span>
            </div>
            <div className="summary-row-detail">
              <span className="label">{t('sell.estPay')}</span>
              <span className="value highlight" style={{ fontSize: '1.15rem' }}>
                {t('sell.calc', {
                  qty: parseFloat(quantityToSell),
                  msp: msp.toLocaleString(),
                  total: estimatedPayment.toLocaleString(),
                })}
              </span>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-secondary" onClick={() => setStep(2)}>{t('sell.back')}</button>
          <button
            className="btn btn-primary btn-lg"
            style={{ flex: 1 }}
            onClick={() => {
              const qty = parseFloat(quantityToSell);
              if (isNaN(qty) || qty <= 0) { setError(t('sell.err.qty')); return; }
              setError(null);
              // Save cultivation and proceed
              handleSaveAndProceed(qty);
            }}
            disabled={!quantityToSell || saving}
          >
            {saving ? t('sell.saving') : t('sell.s3.next')}
          </button>
        </div>
      </div>
    );
  }

  async function handleSaveAndProceed(qty) {
    setSaving(true); setError(null);
    try {
      // Create cultivation record
      const cult = await cultivationApi.create({
        crop: selectedCrop.name,
        season: 'Kharif-2025',
        cultivated_area_acres: parseFloat(cultivatedArea),
        quantity_produced_quintals: qty,
      });
      // Update quantity to sell
      await cultivationApi.updateQuantityToSell(cult.cultivation_id, qty);
      // Store for booking flow
      localStorage.setItem('fp_selected_cultivation', JSON.stringify({
        ...cult,
        quantity_to_sell_quintals: qty,
        quantity_produced_quintals: qty,
      }));
      localStorage.setItem('fp_sell_msp', String(msp || ''));
      navigate('/centres');
    } catch (e) {
      setError(e.message || t('sell.err.save'));
    }
    finally { setSaving(false); }
  }

  return null;
}
