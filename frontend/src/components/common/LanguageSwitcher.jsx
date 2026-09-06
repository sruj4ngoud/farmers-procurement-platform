import { LANGS } from '../../data/i18n.js';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { Languages } from 'lucide-react';

export default function LanguageSwitcher({ className = '' }) {
  const { lang, setLang } = useLanguage();
  return (
    <div className={`fp-langsw ${className}`} role="group" aria-label="Language / భాష / भाषा">
      <Languages size={14} className="fp-langsw-icon" aria-hidden="true" />
      {LANGS.map((l) => (
        <button
          key={l.code}
          type="button"
          className={lang === l.code ? 'active' : ''}
          onClick={() => setLang(l.code)}
          aria-pressed={lang === l.code}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
