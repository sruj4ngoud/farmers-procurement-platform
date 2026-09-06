import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { centreApi } from '../../services/centreApi.js';
import { localizeCentre } from '../../utils/locale.js';
import BookingProgress from '../../components/farmer/BookingProgress.jsx';
import MicButton from '../../components/common/MicButton.jsx';
import SpeakButton from '../../components/common/SpeakButton.jsx';

const STEP_KEYS = ['sell.stepCrop', 'sell.stepQuantity', 'sell.stepCentre', 'sell.stepSlot', 'sell.stepConfirm', 'sell.stepQueue'];

export default function CentreListPage() {
  const { farmer } = useAuth();
  const { t, lang } = useLanguage();
  const navigate = useNavigate();
  const [centres, setCentres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const SELL_STEPS = STEP_KEYS.map((k) => ({ label: t(k) }));

  useEffect(() => {
    if (!farmer?.passbook_number) return;
    centreApi.nearby(farmer.passbook_number)
      .then(setCentres)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [farmer]);

  const visibleCentres = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    const filtered = centres.filter((c) => {
      if (!q) return true;
      const hay = [c.centre_name, localizeCentre(c.centre_name, lang), c.village, c.mandal, c.district].join(' ').toLowerCase();
      return hay.includes(q);
    });
    // Active/limited first, then nearest.
    return [...filtered].sort((a, b) => {
      const rank = (x) => (x.current_status === 'FULL' ? 2 : 0);
      if (rank(a) !== rank(b)) return rank(a) - rank(b);
      return (Number(a.distance_km) || 999) - (Number(b.distance_km) || 999);
    });
  }, [centres, searchQuery]);

  const applySpokenCentre = (transcript) => {
    const q = transcript.toLowerCase().trim();
    const matches = centres.filter((c) =>
      [c.centre_name, localizeCentre(c.centre_name, lang), c.village, c.mandal, c.district].join(' ').toLowerCase().includes(q)
    );
    if (matches.length === 1 && matches[0].current_status !== 'FULL') {
      handleSelectCentre(matches[0]);
    } else if (matches.length >= 1) {
      setSearchQuery(transcript);
    }
  };

  const handleSelectCentre = (centre) => {
    setSelectedId(centre.centre_id);
    localStorage.setItem('fp_selected_centre', JSON.stringify(centre));
    navigate(`/centres/${centre.centre_id}/slots`);
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>{t('cl.loading')}</p></div>;

  return (
    <div className="animate-fadeIn">
      <BookingProgress steps={SELL_STEPS} current={2} />

      <div className="page-header">
        <h1>📍 {t('cl.title')}</h1>
        <p>{t('cl.sub')}</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="form-group" style={{ marginBottom: 16 }}>
        <div className="search-with-mic">
          <input
            className="form-input"
            type="text"
            placeholder={t('cl.searchPh')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <MicButton onResult={applySpokenCentre} onError={setError} />
        </div>
      </div>

      {visibleCentres.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon">📍</div>
          <h3>{t('cl.empty')}</h3>
          <p>{t('cl.emptyDesc')}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {visibleCentres.map((c) => {
            const dist = c.distance_km != null ? Number(c.distance_km).toFixed(1) : null;
            const isFull = c.current_status === 'FULL';
            const isLimited = c.current_status === 'LIMITED';
            const isSelected = selectedId === c.centre_id;
            const statusKey = isFull ? 'cl.full' : isLimited ? 'cl.limited' : 'cl.active';
            return (
              <div
                className={`centre-card ${isSelected ? 'selected' : ''}`}
                key={c.centre_id}
                style={{ opacity: isFull ? 0.55 : 1, cursor: isFull ? 'not-allowed' : 'pointer' }}
                onClick={() => !isFull && handleSelectCentre(c)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div className="centre-name">{localizeCentre(c.centre_name, lang)}</div>
                      <SpeakButton
                        text={`${localizeCentre(c.centre_name, lang)}. ${c.village}, ${c.mandal}, ${c.district}. ${t(statusKey)}. ${dist ? `${dist} ${t('unit.km')}` : ''}`}
                        className="inline"
                      />
                    </div>
                    <div className="centre-location">{c.village}, {c.mandal}, {c.district}</div>
                    <div style={{ fontSize: '.8rem', color: 'var(--gray-500)', marginTop: 4 }}>
                      {t('cl.agency')}: {c.agency}
                    </div>
                    {dist != null && (
                      <div className="centre-distance">{t('cl.distance', { km: dist })}</div>
                    )}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                    <span className={`badge ${isFull ? 'badge-full' : isLimited ? 'badge-limited' : 'badge-active'}`}>
                      {t(statusKey)}
                    </span>
                    {!isFull && (
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={(e) => { e.stopPropagation(); handleSelectCentre(c); }}
                      >
                        {t('cl.select')} →
                      </button>
                    )}
                    {isFull && (
                      <span style={{ fontSize: '.8rem', color: 'var(--red-500)', fontWeight: 500 }}>
                        {t('cl.fullNote')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div style={{ marginTop: 20 }}>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          {t('cl.backDash')}
        </button>
      </div>
    </div>
  );
}
