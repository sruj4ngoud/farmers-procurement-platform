import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext.jsx';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { bankDetailsApi } from '../../services/bankDetailsApi.js';
import { Landmark, ShieldCheck, Lock } from 'lucide-react';

export default function BankDetails() {
  const { farmer } = useAuth();
  const { t } = useLanguage();
  const [bankData, setBankData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState('');

  const [accountHolder, setAccountHolder] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [confirmAccount, setConfirmAccount] = useState('');
  const [ifscCode, setIfscCode] = useState('');
  const [saving, setSaving] = useState(false);

  const [showOtp, setShowOtp] = useState(false);
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [otpLoading, setOtpLoading] = useState(false);
  const [demoOtp, setDemoOtp] = useState(null);

  useEffect(() => {
    bankDetailsApi.get()
      .then((d) => {
        setBankData(d);
        if (d) {
          setAccountHolder(d.account_holder_name || '');
          setAccountNumber('');
          setIfscCode('');
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setError(null); setSuccess('');
    if (!accountHolder.trim()) { setError(t('bank.err.holder')); return; }
    if (!accountNumber.trim()) { setError(t('bank.err.account')); return; }
    if (accountNumber !== confirmAccount) { setError(t('bank.err.mismatch')); return; }
    if (!ifscCode.trim()) { setError(t('bank.err.ifsc')); return; }

    setSaving(true);
    try {
      await bankDetailsApi.save({
        account_holder_name: accountHolder.trim(),
        account_number: accountNumber.trim(),
        ifsc_code: ifscCode.trim(),
      });
      const otpRes = await bankDetailsApi.requestOtp();
      setDemoOtp(otpRes.demo_otp);
      setShowOtp(true);
    } catch (e) {
      setError(e.message || t('bank.err.save'));
    }
    finally { setSaving(false); }
  };

  const handleVerifyOtp = async () => {
    const code = otp.join('');
    if (code.length !== 6) { setError(t('bank.err.otpIncomplete')); return; }
    setError(null);
    setOtpLoading(true);
    try {
      const verified = await bankDetailsApi.verifyOtp(code);
      setBankData(verified);
      setShowOtp(false);
      setSuccess(t('bank.success'));
      setAccountNumber('');
      setConfirmAccount('');
      setIfscCode('');
    } catch (e) {
      setError(e.message || t('bank.err.otp'));
    }
    finally { setOtpLoading(false); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /><p>{t('bank.loading')}</p></div>;

  return (
    <div className="animate-fadeIn">
      <div className="page-header">
        <h1>{t('bank.title')}</h1>
        <p>{t('bank.sub')}</p>
      </div>

      {error && <div className="error-banner"><Lock size={16} />{error}</div>}
      {success && <div className="success-banner"><ShieldCheck size={16} />{success}</div>}

      {/* Verified state */}
      {bankData && bankData.is_verified && (
        <div className="card" style={{ marginBottom: 20, borderLeft: '3px solid var(--black)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <ShieldCheck size={18} style={{ color: 'var(--success)' }} />
            <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--gray-800)' }}>
              {t('bank.verified')}
            </span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bank.holder')}</span>
            <span className="value">{bankData.account_holder_name}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bank.accountNo')}</span>
            <span className="value font-mono">{bankData.account_number_masked}</span>
          </div>
          <div className="summary-row-detail">
            <span className="label">{t('bank.ifsc')}</span>
            <span className="value font-mono">{bankData.ifsc_code_masked}</span>
          </div>
        </div>
      )}

      {/* OTP Verification */}
      {showOtp && (
        <div className="card" style={{ marginBottom: 20, borderLeft: '3px solid var(--black)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Lock size={18} />
            <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{t('bank.verifyTitle')}</span>
          </div>
          {demoOtp && (
            <div className="success-banner" style={{ marginBottom: 12 }}>
              <strong style={{ fontFamily: 'var(--font-mono)', letterSpacing: '0.1em' }}>
                {demoOtp}
              </strong>
              <small style={{ opacity: 0.8 }}> — {t('bank.demoMode')}</small>
            </div>
          )}
          <p style={{ fontSize: '0.85rem', color: 'var(--gray-500)', marginBottom: 12 }}>
            {t('bank.otpSentTo', { mobile: farmer?.mobile_number })}
          </p>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 16 }}>
            {otp.map((digit, i) => (
              <input
                key={i}
                type="tel"
                maxLength={1}
                value={digit}
                onChange={(e) => {
                  if (!/^\d*$/.test(e.target.value)) return;
                  const newOtp = [...otp];
                  newOtp[i] = e.target.value.slice(-1);
                  setOtp(newOtp);
                  if (e.target.value && i < 5) {
                    document.getElementById(`otp-${i+1}`)?.focus();
                  }
                }}
                id={`otp-${i}`}
                className="form-input"
                style={{
                  width: 48, height: 56, textAlign: 'center',
                  fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', padding: 0,
                }}
                autoFocus={i === 0}
              />
            ))}
          </div>
          <button
            className="btn btn-primary btn-block btn-lg"
            onClick={handleVerifyOtp}
            disabled={otpLoading || otp.join('').length !== 6}
          >
            {otpLoading ? t('bank.verifying') : t('bank.verifySave')}
          </button>
        </div>
      )}

      {/* Bank Form */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <Landmark size={18} />
          <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>
            {bankData?.is_verified ? t('bank.updateTitle') : t('bank.submitTitle')}
          </span>
        </div>

        <div className="form-group">
          <label>{t('bank.holderName')}</label>
          <input
            className="form-input"
            type="text"
            placeholder={t('bank.ph.holder')}
            value={accountHolder}
            onChange={(e) => setAccountHolder(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>{t('bank.accountNo')}</label>
          <input
            className="form-input"
            type="text"
            placeholder={t('bank.ph.account')}
            value={accountNumber}
            onChange={(e) => setAccountNumber(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>{t('bank.confirmAccount')}</label>
          <input
            className="form-input"
            type="text"
            placeholder={t('bank.ph.confirm')}
            value={confirmAccount}
            onChange={(e) => setConfirmAccount(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>{t('bank.ifsc')}</label>
          <input
            className="form-input"
            type="text"
            placeholder={t('bank.ph.ifsc')}
            value={ifscCode}
            onChange={(e) => setIfscCode(e.target.value.toUpperCase())}
          />
        </div>

        <button
          className="btn btn-primary btn-block btn-lg"
          onClick={handleSave}
          disabled={saving || showOtp}
        >
          {saving ? t('bank.saving') : t('bank.continue')}
        </button>
      </div>
    </div>
  );
}