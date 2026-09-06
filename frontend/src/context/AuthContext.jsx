import { createContext, useContext, useState, useCallback } from 'react';
import { authApi } from '../services/authApi.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('fp_token'));
  const [farmer, setFarmer] = useState(() => {
    try { const d = localStorage.getItem('fp_farmer'); return d ? JSON.parse(d) : null; } catch { return null; }
  });
  const [otpState, setOtpState] = useState(null); // { passbookNumber, mobileNumber, demoOtp }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isAuthenticated = !!token;

  const requestOtp = useCallback(async (passbookNumber, mobileNumber) => {
    setLoading(true); setError(null);
    try {
      const res = await authApi.requestOtp(passbookNumber, mobileNumber);
      setOtpState({ passbookNumber, mobileNumber, demoOtp: res.demo_otp, expiresIn: res.expires_in_seconds });
      return res;
    } catch (e) { setError(e.message); throw e; }
    finally { setLoading(false); }
  }, []);

  const verifyOtp = useCallback(async (otp) => {
    if (!otpState) throw new Error('No pending OTP request');
    setLoading(true); setError(null);
    try {
      const res = await authApi.verifyOtp(otpState.passbookNumber, otpState.mobileNumber, otp);
      const newToken = res.access_token;
      const farmerData = { farmer_id: res.farmer_id, passbook_number: res.passbook_number, farmer_name: res.farmer_name };
      localStorage.setItem('fp_token', newToken);
      localStorage.setItem('fp_farmer', JSON.stringify(farmerData));
      setToken(newToken);
      setFarmer(farmerData);
      setOtpState(null);
      return res;
    } catch (e) { setError(e.message); throw e; }
    finally { setLoading(false); }
  }, [otpState]);

  const logout = useCallback(async () => {
    try { await authApi.logout(); } catch {}
    localStorage.removeItem('fp_token');
    localStorage.removeItem('fp_farmer');
    setToken(null);
    setFarmer(null);
    setOtpState(null);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return (
    <AuthContext.Provider value={{ token, farmer, isAuthenticated, otpState, loading, error, requestOtp, verifyOtp, logout, clearError, setError }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
