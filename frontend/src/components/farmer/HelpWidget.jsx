import { useState, useCallback, useEffect, useRef } from 'react';
import { HelpCircle, X, Mic, ChevronLeft, ArrowUpRight } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { useAuth } from '../../context/AuthContext.jsx';
import { isRecognitionSupported, createRecognizer } from '../../utils/speech.js';
import SpeakButton from '../common/SpeakButton.jsx';

const HELP_SECTIONS = [
  { key: 'booking', titleKey: 'help.booking', bodyKey: 'help.booking.body' },
  { key: 'queue', titleKey: 'help.queue', bodyKey: 'help.queue.body' },
  { key: 'payment', titleKey: 'help.payment', bodyKey: 'help.payment.body' },
  { key: 'contact', titleKey: 'help.contact', bodyKey: 'help.contact.body' },
];

/** Keywords (across languages) that map a spoken question to a help section. */
const KEYWORDS = {
  booking: ['booking', 'book', 'sell', 'अम्म', 'అమ్మ', 'बेच', 'बुक', 'బుక్', 'crop', 'పంట', 'फसल', 'slot', 'స్లాట్', 'स्लॉट'],
  queue: ['queue', 'क्यू', 'క్యూ', 'token', 'టోకెన్', 'टोकन', 'turn', 'వంతు', 'बारी', 'wait', 'నిరీక్షణ', 'इंतज़ार', 'position', 'స్థానం'],
  payment: ['payment', 'pay', 'చెల్లింపు', 'भुगतान', 'money', 'డబ్బు', 'पैसा', 'bank', 'బ్యాంక్', 'बैंक'],
  contact: ['help', 'contact', 'call', 'phone', 'సహాయం', 'मदद', 'కాల్', 'ఫోన్', 'फोन'],
};

function classify(transcript) {
  const q = transcript.toLowerCase();
  for (const [section, words] of Object.entries(KEYWORDS)) {
    if (words.some((w) => q.includes(w.toLowerCase()))) return section;
  }
  return null;
}

export default function HelpWidget() {
  const { t, speechLang } = useLanguage();
  const { farmer } = useAuth();
  const [open, setOpen] = useState(false);
  const [section, setSection] = useState(null); // null = menu
  const [listening, setListening] = useState(false);
  const [voiceNote, setVoiceNote] = useState(null); // 'thinking' | 'sorry' | null
  const recRef = useRef(null);

  const close = useCallback(() => {
    setOpen(false);
    setSection(null);
    setVoiceNote(null);
    try { recRef.current?.stop(); } catch { /* ignore */ }
    recRef.current = null;
    setListening(false);
  }, []);

  const openSection = useCallback((key) => {
    setVoiceNote(null);
    setSection(key);
  }, []);

  const startVoice = useCallback(() => {
    setVoiceNote(null);
    if (!isRecognitionSupported()) { setVoiceNote('sorry'); return; }
    const rec = createRecognizer(speechLang);
    if (!rec) { setVoiceNote('sorry'); return; }
    recRef.current = rec;
    setListening(true);
    rec.onresult = (event) => {
      const text = Array.from(event.results).map((r) => r[0]?.transcript || '').join(' ').trim();
      const hit = text ? classify(text) : null;
      setListening(false);
      recRef.current = null;
      if (hit) openSection(hit);
      else setVoiceNote('sorry');
    };
    rec.onend = () => { setListening(false); recRef.current = null; };
    rec.onerror = () => { setListening(false); recRef.current = null; setVoiceNote('sorry'); };
    try { rec.start(); } catch { setListening(false); setVoiceNote('sorry'); }
  }, [speechLang, openSection]);

  const activeSection = section ? HELP_SECTIONS.find((s) => s.key === section) : null;
  const firstName = (farmer?.farmer_name || '').split(' ')[0];

  return (
    <>
      <button
        type="button"
        className="fp-help-fab"
        onClick={() => (open ? close() : setOpen(true))}
        aria-label={t('chrome.help')}
        title={t('chrome.help')}
      >
        {open ? <X size={19} /> : <HelpCircle size={19} />}
        <span className="fp-help-fab-label">{t('chrome.help')}</span>
      </button>

      {open && (
        <div className="fp-help-modal">
          <div className="fp-help-head">
            <div>
              <strong>{t('help.title')}</strong>
              <p>{firstName ? `${firstName}, ${t('help.sub')}` : t('help.sub')}</p>
            </div>
            <button className="fp-help-close" onClick={close} aria-label={t('help.close')}>
              <X size={17} />
            </button>
          </div>

          {activeSection ? (
            <div className="fp-help-body">
              <button className="fp-help-back" onClick={() => setSection(null)}>
                <ChevronLeft size={15} /> {t('help.title')}
              </button>
              <div className="fp-help-card">
                <div className="fp-help-card-title">
                  <h4>{t(activeSection.titleKey)}</h4>
                  <SpeakButton text={`${t(activeSection.titleKey)}. ${t(activeSection.bodyKey)}`} />
                </div>
                <p className="fp-help-card-body">{t(activeSection.bodyKey)}</p>
              </div>
              {section === 'contact' && (
                <a className="fp-help-call" href="tel:18001801551">
                  <ArrowUpRight size={15} /> 1800-180-1551
                </a>
              )}
            </div>
          ) : (
            <div className="fp-help-body">
              <button type="button" className={`fp-help-voice ${listening ? 'listening' : ''}`} onClick={startVoice}>
                <span className="fp-help-voice-icon">{listening ? <Mic size={18} /> : <Mic size={18} />}</span>
                <span>
                  <strong>{t('help.voice')}</strong>
                  <small>{t('help.voice.desc')}</small>
                </span>
              </button>
              {listening && <p className="fp-help-note">{t('help.voice.thinking')}</p>}
              {!listening && voiceNote === 'sorry' && (
                <p className="fp-help-note error">{t('help.voice.sorry')}</p>
              )}

              <div className="fp-help-list">
                {HELP_SECTIONS.map((s) => (
                  <button key={s.key} className="fp-help-option" onClick={() => openSection(s.key)}>
                    <span>{t(s.titleKey)}</span>
                    <ChevronLeft size={15} className="fp-chev" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
