import { Outlet, Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext.jsx';
import LanguageSwitcher from '../components/common/LanguageSwitcher.jsx';

export default function AuthLayout() {
  const { t } = useLanguage();

  return (
    <div className="auth-container">
      <div className="auth-left">
        <div className="auth-left-content">
          <div style={{ marginBottom: 24 }}>
            <div style={{
              width: 48, height: 48, background: 'rgba(255,255,255,0.1)',
              borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 20px'
            }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M7 20h10" /><path d="M10 20c5.5-2.5.8-6.4 3-10" />
                <path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z" />
                <path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z" />
              </svg>
            </div>
          </div>
          <h2>Smart Farmer<br />Procurement</h2>
          <p>
            {t('auth.brandSub')}
          </p>
        </div>
      </div>
      <div className="auth-right">
        <div className="auth-right-top">
          <Link
            to="/admin/login"
            style={{
              fontSize: '0.8rem',
              fontWeight: 500,
              color: 'var(--gray-500)',
              textDecoration: 'none'
            }}
          >
            {t('auth.districtAdmin')}
          </Link>
          <LanguageSwitcher />
        </div>
        <Outlet />
      </div>
    </div>
  );
}