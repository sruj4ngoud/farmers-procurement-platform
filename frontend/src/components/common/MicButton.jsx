import { useRef, useState, useEffect, useCallback } from 'react';
import { Mic, Square } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { createRecognizer, isRecognitionSupported } from '../../utils/speech.js';

/**
 * Voice-input button. Speaks in the active UI language (en-IN / te-IN / hi-IN).
 * - onResult(transcript)  — fired with the final transcript
 * - onError(message)      — fired when voice input is unavailable/fails
 * - hint                  — optional short text shown next to the button
 */
export default function MicButton({ onResult, onError, hint, className = '', disabled }) {
  const { t, speechLang } = useLanguage();
  const [listening, setListening] = useState(false);
  const [supported] = useState(isRecognitionSupported);
  const recRef = useRef(null);

  const stop = useCallback(() => {
    try { recRef.current?.stop(); } catch { /* ignore */ }
    recRef.current = null;
  }, []);

  useEffect(() => () => stop(), [stop]);

  const toggle = useCallback(() => {
    if (listening) { stop(); setListening(false); return; }
    if (!supported) {
      onError?.(t('voice.unsupported'));
      return;
    }
    const rec = createRecognizer(speechLang);
    if (!rec) {
      onError?.(t('voice.unsupported'));
      return;
    }
    recRef.current = rec;
    setListening(true);

    rec.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0]?.transcript || '')
        .join(' ')
        .trim();
      if (transcript) onResult?.(transcript);
    };
    rec.onend = () => setListening(false);
    rec.onerror = (event) => {
      setListening(false);
      recRef.current = null;
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        onError?.(t('voice.unsupported'));
      }
    };
    try { rec.start(); } catch { setListening(false); onError?.(t('voice.unsupported')); }
  }, [listening, supported, speechLang, stop, onResult, onError, t]);

  return (
    <span className={`fp-mic-wrap ${className}`}>
      <button
        type="button"
        className={`fp-mic ${listening ? 'listening' : ''}`}
        onClick={toggle}
        disabled={disabled || !supported}
        aria-label={listening ? t('voice.listening') : t('voice.tapToSpeak')}
        title={listening ? t('voice.listening') : t('voice.tapToSpeak')}
      >
        {listening ? <Square size={16} fill="currentColor" /> : <Mic size={16} />}
      </button>
      {listening && <span className="fp-mic-hint">{t('voice.listening')}</span>}
      {!listening && hint && <span className="fp-mic-hint">{hint}</span>}
    </span>
  );
}
