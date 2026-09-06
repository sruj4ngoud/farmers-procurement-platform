import { createContext, useContext, useEffect, useMemo, useState, useCallback } from 'react';
import { LANGS, SPEECH_LANGS, lookup } from '../data/i18n.js';

const LanguageContext = createContext(null);

const STORAGE_KEY = 'fp_lang';

function initialLang() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && LANGS.some((l) => l.code === saved)) return saved;
  } catch { /* ignore */ }
  return 'en';
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(initialLang);

  const setLang = useCallback((code) => {
    if (!LANGS.some((l) => l.code === code)) return;
    setLangState(code);
    try { localStorage.setItem(STORAGE_KEY, code); } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    try { document.documentElement.lang = lang; } catch { /* ignore */ }
  }, [lang]);

  const value = useMemo(() => {
    /** Translate key with optional {placeholder} interpolation. */
    const t = (key, vars) => {
      let str = lookup(lang, key);
      if (vars) {
        Object.entries(vars).forEach(([k, v]) => {
          str = str.split(`{${k}}`).join(v != null ? String(v) : '');
        });
      }
      return str;
    };
    return {
      lang,
      setLang,
      t,
      speechLang: SPEECH_LANGS[lang] || 'en-IN',
    };
  }, [lang, setLang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
}
