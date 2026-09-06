import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext.jsx';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { ShieldCheck, ArrowRight, ArrowLeft } from 'lucide-react';

export default function OtpVerifyPage() {
  const { verifyOtp, otpState, loading, error, clearError, requestOtp } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef([]);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!otpState) navigate('/login', { replace: true });
  }, [otpState, navigate]);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    if (value && index < 5) inputRefs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = pasted.split('').concat(Array(6).fill('')).slice(0, 6);
    setOtp(newOtp);
    inputRefs.current[Math.min(pasted.length, 5)]?.focus();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    const code = otp.join('');
    if (code.length !== 6) return;
    try {
      await verifyOtp(code);
      navigate('/dashboard');
    } catch {
      // error is set in AuthContext
    }
  };

  const handleResend = async () => {
    if (!otpState) return;
    setResending(true);
    try {
      await requestOtp(otpState.passbookNumber, otpState.mobileNumber);
    } catch {}
    setResending(false);
  };

  const otpString = otp.join('');
  const demoOtp = otpState?.demoOtp;
  const maskedMobile = otpState?.mobileNumber
    ? otpState.mobileNumber.replace(/(\d{2})(\d{3})(\d{3})(\d{2})/, '+91 $1 XXX $2XX $3')
    : '';

  return (
    <div className="auth-card">
      <div className="auth-header">
        <div className="auth-icon">
          <ShieldCheck size={20} />
        </div>
        <h1>{t('auth.verifyOtp')}</h1>
        <p>
          {t('auth.otpSub')}<br />
          <strong style={{ color: 'var(--gray-800)' }}>{maskedMobile || otpState?.mobileNumber}</strong>
        </p>
      </div>

      {demoOtp && (
        <div className="success-banner" style={{ justifyContent: 'center', textAlign: 'center' }}>
          <div>
            <strong style={{ fontSize: '1rem', letterSpacing: '0.1em', fontFamily: 'var(--font-mono)' }}>
              {demoOtp}
            </strong>
            <br />
            <small style={{ opacity: 0.8 }}>{t('auth.demoMode')}</small>
          </div>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label style={{ textAlign: 'center' }}>{t('auth.enterOtp')}</label>
          <div
            style={{ display: 'flex', gap: 8, justifyContent: 'center' }}
            onPaste={handlePaste}
          >
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={(el) => (inputRefs.current[i] = el)}
                type="tel"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                className="form-input"
                style={{
                  width: 48,
                  height: 56,
                  textAlign: 'center',
                  fontSize: '1.25rem',
                  fontWeight: 700,
                  fontFamily: 'var(--font-mono)',
                  padding: 0,
                }}
                autoFocus={i === 0}
              />
            ))}
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-block btn-lg"
          disabled={loading || otpString.length !== 6}
        >
          {loading ? (
            t('auth.verifying')
          ) : (
            <>
              {t('auth.verify')}
              <ArrowRight size={18} />
            </>
          )}
        </button>
      </form>

      <div style={{
        display: 'flex',
        gap: 10,
        justifyContent: 'center',
        marginTop: 16
      }}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => navigate('/login')}
        >
          <ArrowLeft size={14} />
          {t('auth.changeNumber')}
        </button>
        <button
          className="btn btn-outline btn-sm"
          onClick={handleResend}
          disabled={resending}
        >
          {resending ? t('auth.sending') : t('auth.resendOtp')}
        </button>
      </div>
    </div>
  );
}