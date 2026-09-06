import { useRef, useState, useCallback } from 'react';
import { Volume2, Square } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { speak, stopSpeaking } from '../../utils/speech.js';

/**
 * Read-aloud button. Speaks `text` in the active UI language.
 * Pass langOverride to force a different BCP-47 code if needed.
 */
export default function SpeakButton({ text, langOverride, className = '', title }) {
  const { t, speechLang } = useLanguage();
  const [active, setActive] = useState(false);
  const timerRef = useRef(null);

  const toggle = useCallback((event) => {
    event?.stopPropagation?.();
    event?.preventDefault?.();
    if (active) {
      stopSpeaking();
      setActive(false);
      if (timerRef.current) clearTimeout(timerRef.current);
      return;
    }
    stopSpeaking();
    const langCode = langOverride || speechLang;
    speak(text, langCode);
    setActive(true);
    // Auto-clear the "stop" state after the estimated speech duration.
    const ms = Math.min(20000, Math.max(2000, (text || '').length * 95));
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setActive(false), ms);
  }, [active, text, langOverride, speechLang]);

  return (
    <button
      type="button"
      className={`fp-speak ${active ? 'active' : ''} ${className}`}
      onClick={toggle}
      aria-label={title || t('chrome.listen')}
      title={title || t('chrome.listen')}
    >
      {active ? <Square size={15} fill="currentColor" /> : <Volume2 size={15} />}
    </button>
  );
}
